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

#ifndef IECORE_OBJECTCACHE_H
#define IECORE_OBJECTCACHE_H

#include "IECore/LRUCache.h"
#include "IECore/Object.h"
#include "IECore/MurmurHash.h"

namespace IECore
{

IE_CORE_FORWARDDECLARE( ObjectCache );

/// Cache that holds Object instances.
/// 
/// \ingroup utilityGroup
class ObjectCache : public RefCounted
{
	public:

		ObjectCache();
		virtual ~ObjectCache();

		void clear();

		// Erases the Object with the given hash if it is contained in the cache. Returns whether any item was removed.
		bool erase( const MurmurHash &hash );

		/// Set the maximum memory cost of the items held in the cache, discarding any items if necessary.
		void setMaxMemoryUsage( size_t maxMemory );

		/// Get the maximum possible memory cost of cacheable items
		size_t getMaxMemoryUsage() const;

		/// Returns the current memory cost of items held in the cache
		size_t currentMemoryUsage() const;

		/// Retrieves the Object with the given hash, or NULL if not contained in the cache.
		ConstObjectPtr get( const MurmurHash &hash );

		/// Registers an object in the cache directly. Returns the object stored in the cache.
		ConstObjectPtr set( ConstObjectPtr &obj );

		/// Register the object in the cache or a copy of it, in case you can't garantee that the given
		/// object will not be modified after this call.
		/// Returns the object stored in the cache.
		ConstObjectPtr set( ObjectPtr &obj, bool copy );

		/// Returns true if the object with the given hash is in the cache.
		bool cached( const MurmurHash &hash ) const;

		/// Returns the singleton ObjectCache. It's default maximum cost is defined by the environment
		/// variable $IECORE_OBJECTCACHE_MEMORY in mega bytes and it defaults to 500.
		static ObjectCachePtr defaultObjectCache();

	private:

		LRUCache< MurmurHash, ConstObjectPtr > m_cache;
};

} // namespace IECore

#endif // IECORE_OBJECTCACHE_H

