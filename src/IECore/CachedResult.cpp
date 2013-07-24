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

#include "IECore/CachedResult.h"

using namespace IECore;

////////////////////////////////////////////////////////////////////////
// MemberData
////////////////////////////////////////////////////////////////////////

struct CachedResult::MemberData
{
	MemberData( size_t maxMemory, ObjectCachePtr c )
		:	cache( getter, maxMemory ), objectCache(c)
	{
	}
	
	// The key for the cache is just the hash of
	// the object, but we also need the key to carry the ObjectCache and the converter,
	// so that the getter can use it for the source of the conversion.
	// So we derive from the Hash, adding these extra data and we use 
	// this object on the call to the get() function, that will 
	struct CacheKey : public MurmurHash
	{

		CacheKey( MurmurHash h, ComputeFn &c, ObjectCachePtr cache )
			: MurmurHash( h ), compute(c), objectCache(cache), object(0)
		{
		}

		ComputeFn compute;
		IECore::ObjectCachePtr objectCache;
		IECore::ConstObjectPtr object;
	};

	static MurmurHash getter( const MurmurHash &h, size_t &cost )
	{
		CacheKey &key = *(const_cast< CacheKey * >(static_cast< const CacheKey * >(&h)));
		cost = 1;
		if ( key.compute )
		{
			key.object = key.compute();
		}

		if ( !key.object )
		{
			return MurmurHash();
		}

		/// the object cache may return a different object if the object was already in the cache.
		key.object = key.objectCache->set(key.object);

		return key.object->hash();
	}

	typedef IECore::LRUCache<MurmurHash, MurmurHash> Cache;
	Cache cache;
	ObjectCachePtr objectCache;
	
};

//////////////////////////////////////////////////////////////////////////
// CachedResult
//////////////////////////////////////////////////////////////////////////

CachedResult::CachedResult( size_t maxResults, ObjectCachePtr objectCache ) : m_data( new MemberData(maxResults, objectCache) )
{
}

void CachedResult::clear()
{
	m_data->cache.clear();
}

size_t CachedResult::getMaxCachedResults() const
{
	return m_data->cache.getMaxCost();
}

void CachedResult::setMaxCachedResults( size_t maxResults )
{
	m_data->cache.setMaxCost(maxResults);
}

size_t CachedResult::currentCachedResults() const
{
	return m_data->cache.currentCost();
}

bool CachedResult::cached( const MurmurHash &key )
{
	return m_data->cache.cached(key);
}

ConstObjectPtr CachedResult::get( const MurmurHash &key )
{
	MemberData::CacheKey cacheKey(key, compute, m_data->objectCache);

	MurmurHash objectHash = m_data->cache.get( key );
	ConstObjectPtr obj = cacheKey.object;

	if ( !obj )
	{
		if ( objectHash == MurmurHash() )
		{
			return 0;
		}
		/// we retrieved the hash from the cache, now we have to retrieve the object itself...
		obj = m_data->objectCache->get(objectHash);
		if ( !obj && compute )
		{
			/// object is not in the cache anymore... recompute and register back in the ObjectCache
			obj = compute();
			obj = m_data->objectCache->set( obj );
		}
	}
	return obj;
}

ConstObjectPtr CachedResult::get( const MurmurHash &key, ComputeFn compute )
{
	MemberData::CacheKey cacheKey(key, compute, m_data->objectCache);

	MurmurHash objectHash = m_data->cache.get( cacheKey );
	ConstObjectPtr obj = cacheKey.object;

	if ( !obj )
	{
		if ( objectHash == MurmurHash() )
		{
			return 0;
		}
		/// we retrieved the hash from the cache, now we have to retrieve the object itself...
		obj = m_data->objectCache->get(objectHash);
		if ( !obj && compute )
		{
			/// object is not in the cache anymore... recompute and register back in the ObjectCache
			obj = compute();
			obj = m_data->objectCache->set( obj );
		}
	}
	return obj;
}

void CachedResult::set( const MurmurHash &key, ConstObjectPtr obj )
{
	m_data->objectCache->set(obj);
	m_data->cache.set( key, obj->hash(), 1 );
}


