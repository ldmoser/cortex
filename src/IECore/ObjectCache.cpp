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

#include "boost/lexical_cast.hpp"
#include "IECore/ObjectCache.h"

using namespace IECore;

////////////////////////////////////////////////////////////////////////
// LRUCache specialization
////////////////////////////////////////////////////////////////////////

namespace IECore
{

/// specialization for the get function for our ObjectCache which does not have a getter function. 
/// So we want to return NULL when the object is not available and never throw exceptions.
template<>
ConstObjectPtr LRUCache<MurmurHash,ConstObjectPtr>::get( const MurmurHash& key )
{
	Mutex::scoped_lock lock( m_mutex );

	Cache::iterator cIt = m_cache.find(key);
	if ( cIt == m_cache.end() )
	{
		return NULL;
	}

	CacheEntry &cacheEntry = cIt->second;

	if( cacheEntry.status!=Cached )
	{
		return NULL;
	}

	// move the entry to the front of the list
	m_list.erase( cacheEntry.listIterator );
	m_list.push_front( key );
	cacheEntry.listIterator = m_list.begin();
	assert( m_list.size() <= m_cache.size() );
	return cacheEntry.data;
}

}

//////////////////////////////////////////////////////////////////////////
// ObjectCache
//////////////////////////////////////////////////////////////////////////

ObjectCache::ObjectCache()
	:	m_cache( NULL )
{
}

ObjectCache::~ObjectCache()
{
}

ConstObjectPtr ObjectCache::get( const MurmurHash &hash )
{
	return m_cache.get(hash);
}

ConstObjectPtr ObjectCache::set( ConstObjectPtr &obj )
{
	MurmurHash h = obj->hash();

	// first tries to see if the object is already in the cache and return that one quickly.
	ConstObjectPtr cachedObj = m_cache.get(h);
	if ( cachedObj )
	{
		return cachedObj;
	}

	m_cache.set( h, obj, obj->memoryUsage() );
	return obj;
}

ConstObjectPtr ObjectCache::set( ObjectPtr &obj, bool copy )
{
	MurmurHash h = obj->hash();

	// first tries to see if the object is already in the cache and return that one quickly.
	ConstObjectPtr cachedObj = m_cache.get(h);
	if ( cachedObj )
	{
		return cachedObj;
	}

	if ( copy )
	{
		m_cache.set( h, obj->copy(), obj->memoryUsage() );
	}
	else
	{
		m_cache.set( h, obj, obj->memoryUsage() );
	}
	return obj;
}

bool ObjectCache::cached( const MurmurHash &hash ) const
{
	return m_cache.cached(hash);
}

void ObjectCache::clear()
{
	m_cache.clear();
}

bool ObjectCache::erase( const MurmurHash &hash )
{
	return m_cache.erase(hash);
}

void ObjectCache::setMaxMemoryUsage( size_t maxMemory )
{
	m_cache.setMaxCost(maxMemory);
}

size_t ObjectCache::getMaxMemoryUsage() const
{
	return m_cache.getMaxCost();
}

size_t ObjectCache::currentMemoryUsage() const
{
	return m_cache.currentCost();
}

ObjectCachePtr ObjectCache::defaultObjectCache()
{
	static ObjectCachePtr c = 0;
	if( !c )
	{
		const char *m = getenv( "IECORE_OBJECTCACHE_MEMORY" );
		int mi = m ? boost::lexical_cast<int>( m ) : 500;
		c = new ObjectCache();
		c->setMaxMemoryUsage( 1024 * 1024 * mi );
	}
	return c;
}

