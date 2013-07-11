//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2008-2013, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////

#include <cassert>

#include "boost/format.hpp"

#include "IECore/MeshPrimitive.h"
#include "IECore/MessageHandler.h"

#include "IECoreGL/ToGLMeshConverter.h"
#include "IECoreGL/MeshPrimitive.h"
#include "IECoreGL/CachedConverter.h"

using namespace IECoreGL;


//////////////////////////////////////////////////////////////////////////
// CreateNormalsConverter
//////////////////////////////////////////////////////////////////////////

class ToGLMeshConverter::CalculateNormals
{
	public :

		CalculateNormals( const IECore::IntVectorData *vertexIds, const IECore::IntVectorData *verticesPerFace ) :
				m_vertexIds(vertexIds), m_verticesPerFace(verticesPerFace)
		{
		}

		/// hash function used by CachedConverter.
		IECore::MurmurHash hash( const IECore::Object *object ) const
		{
			IECore::MurmurHash h;
			h.append( "CalculateNormals");
			m_verticesPerFace->hash(h);
			m_vertexIds->hash(h);
			object->hash(h);
			return h;
		}

		/// call operator used by the CachedConverter.
		IECore::RunTimeTypedPtr operator()( const IECore::Object *object )
		{
			return compute( static_cast< const IECore::V3fVectorData * >(object) );
		}

		private :

		template<typename T>
		IECore::DataPtr compute( T *pointsData )
		{
			typedef typename T::ValueType VecContainer;
			typedef typename VecContainer::value_type Vec;

			const std::vector<int> &vertsPerFace = m_verticesPerFace->readable();
			const std::vector<int> &vertIds = m_vertexIds->readable();

			const typename T::ValueType &points = pointsData->readable();

			typename T::Ptr normalsData = new T;
			normalsData->setInterpretation( IECore::GeometricData::Normal );
			VecContainer &normals = normalsData->writable();
			normals.resize( points.size(), Vec( 0 ) );

			// for each face, calculate its normal, and accumulate that normal onto
			// the normal for each of its vertices.
			const int *vertId = &(vertIds[0]);
			for( std::vector<int>::const_iterator it = vertsPerFace.begin(); it!=vertsPerFace.end(); it++ )
			{
				const Vec &p0 = points[*vertId];
				const Vec &p1 = points[*(vertId+1)];
				const Vec &p2 = points[*(vertId+2)];

				Vec normal = (p2-p1).cross(p0-p1);
				normal.normalize();
				for( int i=0; i<*it; i++ )
				{
					normals[*vertId] += normal;
					vertId++;
				}
			}

			// normalize each of the vertex normals
			for( typename VecContainer::iterator it=normals.begin(); it!=normals.end(); it++ )
			{
				it->normalize();
			}

			return normalsData;
		}

		private :

		const IECore::IntVectorData *m_vertexIds;
		const IECore::IntVectorData *m_verticesPerFace;

};


//////////////////////////////////////////////////////////////////////////
// ToGLMeshConverter
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( ToGLMeshConverter );

ToGLConverter::ConverterDescription<ToGLMeshConverter> ToGLMeshConverter::g_description;

ToGLMeshConverter::ToGLMeshConverter( IECore::ConstMeshPrimitivePtr toConvert )
	:	ToGLConverter( "Converts IECore::MeshPrimitive objects to IECoreGL::MeshPrimitive objects.", IECore::MeshPrimitiveTypeId )
{
	srcParameter()->setValue( IECore::constPointerCast<IECore::MeshPrimitive>( toConvert ) );
}

ToGLMeshConverter::~ToGLMeshConverter()
{
}

IECore::RunTimeTypedPtr ToGLMeshConverter::doConversion( IECore::ConstObjectPtr src, IECore::ConstCompoundObjectPtr operands ) const
{
	IECore::ConstMeshPrimitivePtr mesh = IECore::staticPointerCast< const IECore::MeshPrimitive>( src ); // safe because the parameter validated it for us

	IECore::ConstV3fVectorDataPtr p = mesh->variableData<IECore::V3fVectorData >( "P", IECore::PrimitiveVariable::Vertex );
	if( !p )
	{
		throw IECore::Exception( "Could not find primitive variable \"P\", of type V3fVectorData and interpolation type Vertex." );
	}

	MeshPrimitivePtr glMesh;

	if ( mesh->maxVerticesPerFace() 	== 3 )
	{
		glMesh = new MeshPrimitive( mesh->vertexIds() );
	}
	else
	{
		glMesh = new MeshPrimitive( mesh->verticesPerFace(), mesh->vertexIds() );
	}

	/// add normals to the GL mesh if necessary...
	/// \todo consider generating Normals when 'P' is added as a primVar. So we can update only 'P' and have normals recomputed.
	if( mesh->interpolation() != "linear" )
	{
		// it's a subdivision mesh. in the absence of a nice subdivision algorithm to display things with,
		// we can at least make things look a bit nicer by calculating some smooth shading normals.
		// if interpolation is linear and no normals are provided then we assume the faceted look is intentional.
		if( mesh->variables.find( "N" )==mesh->variables.end() )
		{
			CachedConverterPtr cachedConverter = CachedConverter::defaultCachedConverter();
			CalculateNormals calculateNormals( mesh->vertexIds(), mesh->verticesPerFace() );
			IECore::ConstDataPtr normals = IECore::staticPointerCast< const IECore::Data >( cachedConverter->convert( p, calculateNormals ) );
			glMesh->addPrimitiveVariable( "N", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Vertex, normals->copy() ) );
		}
	}

	IECore::PrimitiveVariableMap::const_iterator sIt = mesh->variables.end();
	IECore::PrimitiveVariableMap::const_iterator tIt = mesh->variables.end();

	// add the primitive variables to the mesh (which know how to triangulate)
	for ( IECore::PrimitiveVariableMap::const_iterator pIt = mesh->variables.begin(); pIt != mesh->variables.end(); ++pIt )
	{
		/// only process valid prim vars
		if ( !mesh->isPrimitiveVariableValid( pIt->second ) )
		{
			continue;
		}

		if ( pIt->second.data )
		{
			if ( pIt->first == "s" )
			{
				sIt = pIt;
			}
			else if ( pIt->first == "t" )
			{
				tIt = pIt;
			}
			glMesh->addPrimitiveVariable( pIt->first, pIt->second );
		}
		else
		{
			IECore::msg( IECore::Msg::Warning, "MeshPrimitive", boost::format( "No data given for primvar \"%s\"" ) % pIt->first );
		}
	}

	/// \todo remove all this when we start supporting a V2f primVar for UVs.
	/// create variable 'st' from 's' and 't'
	if ( sIt != mesh->variables.end() && tIt != mesh->variables.end() )
	{
		if ( sIt->second.interpolation == tIt->second.interpolation && 
			 sIt->second.interpolation != IECore::PrimitiveVariable::Constant )
		{
			IECore::ConstFloatVectorDataPtr s = IECore::runTimeCast< const IECore::FloatVectorData >( sIt->second.data );
			IECore::ConstFloatVectorDataPtr t = IECore::runTimeCast< const IECore::FloatVectorData >( tIt->second.data );

			if ( s && t )
			{
				/// Should hold true if primvarsAreValid
				assert( s->readable().size() == t->readable().size() );

				IECore::V2fVectorDataPtr stData = new IECore::V2fVectorData();
				stData->writable().resize( s->readable().size() );

				for ( unsigned i = 0; i < s->readable().size(); i++ )
				{
					stData->writable()[i] = Imath::V2f( s->readable()[i], t->readable()[i] );
				}
				glMesh->addPrimitiveVariable( "st", IECore::PrimitiveVariable( sIt->second.interpolation, stData ) );
			}
			else
			{
				IECore::msg( IECore::Msg::Warning, "ToGLMeshConverter", "If specified, primitive variables \"s\" and \"t\" must be of type FloatVectorData and interpolation type FaceVarying." );
			}
		}
		else
		{
			IECore::msg( IECore::Msg::Warning, "ToGLMeshConverter", "If specified, primitive variables \"s\" and \"t\" must be of type FloatVectorData and non-Constant interpolation type." );
		}
	}
	else if ( sIt != mesh->variables.end() || tIt != mesh->variables.end() )
	{
		IECore::msg( IECore::Msg::Warning, "ToGLMeshConverter", "Primitive variable \"s\" or \"t\" found, but not both." );
	}

	return glMesh;
}
