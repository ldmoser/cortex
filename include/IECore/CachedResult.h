//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#ifndef IECORE_CACHEDRESULT_H
#define IECORE_CACHEDRESULT_H

#include "boost/function.hpp"

#include "IECore/ObjectCache.h"

namespace IECore
{

IE_CORE_FORWARDDECLARE( CachedResult )

/// LRUCache for generic computation that results on Object derived classes. It uses the default ObjectCache for the storage and retrieval of 
/// the computation results, and internally it only holds a map of computationHash =>objectHash. The get functions will return the resulting 
/// Object, which should be copied prior to modification.
/// \todo Consider instead using a map computationHash => object weak pointer. That would require only one map query per get() if results are still cached.
/// \todo Stop using LRUCache for two reasons: we don't need to store the cost, we are hacking it by providing a getter function that tests if the compute is NULL. The most natural way would be to have a get in LRUCache that would not compute, just a query...
class CachedResult : public RefCounted
{
	public :

		typedef boost::function<IECore::ConstObjectPtr ()> ComputeFn;

		/// Constructs a cache that uses the default ObjectCache as the object storage.
		CachedResult( size_t maxResults, ObjectCachePtr objectCache = ObjectCache::defaultObjectCache() );

/*		/// key must be a hashable object (could be a MurmurHash object, or be a implicitly convertible to MurmurHash or define hash() method)
		/// compute is a callable object that should know how to return the Object.
		template< typename K, typename T >
		ConstObjectPtr get( K key, T compute );

		/// compute is a hashable object (defines the hash() method and also it is a callable object that 
		/// knows how to create the requested Object in case it's not available in the cache.
		template< typename T >
		ConstObjectPtr get( T compute );

		/// key must be a hashable object (could be a MurmurHash object, or be a implicitly convertible to MurmurHash or define hash() method)
		template< typename K >
		bool cached( K key );
*/
		void clear();

		size_t getMaxCachedResults() const;

		void setMaxCachedResults( size_t maxResults );

		size_t currentCachedResults() const;

		bool cached( const MurmurHash &key );

		/// If compute is NULL and is not cached, the get will cache the NULL object.
		ConstObjectPtr get( const MurmurHash &key, ComputeFn compute );

		/// Sets an object to the cache
		void set( const MurmurHash &key, ConstObjectPtr obj );

	private :

		struct MemberData;
		MemberData *m_data;
};


} // namespace IECore

//#include "IECore/CachedResult.inl"

#endif // IECORE_CACHEDRESULT_H

