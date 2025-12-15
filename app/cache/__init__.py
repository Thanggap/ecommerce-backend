import os
import json
import asyncio
from typing import Optional, Any, List
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Redis client singleton
redis: Optional[Any] = None
_redis_available: bool = True

# Default TTL: 300 seconds (5 minutes)
DEFAULT_TTL = 300


async def init_redis():
    """Initialize Redis connection - call this on app startup"""
    global redis, _redis_available
    try:
        import redis.asyncio as aioredis
        redis = await aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
        # Test connection
        await redis.ping()
        print(f"Redis connected successfully to {REDIS_URL[:30]}...")
        _redis_available = True
    except Exception as e:
        print(f"Redis unavailable, running without cache: {e}")
        _redis_available = False
        redis = None


async def close_redis():
    """Close Redis connection - call this on app shutdown"""
    global redis
    if redis:
        await redis.close()
        redis = None


async def cache_get(key: str) -> Optional[Any]:
    """Get value from cache - returns None if cache unavailable"""
    global redis, _redis_available
    if not _redis_available or not redis:
        return None
    try:
        data = await redis.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        print(f"Cache get error: {e}")
        return None


async def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> bool:
    """Set value in cache with expiration (TTL in seconds)"""
    global redis, _redis_available
    if not _redis_available or not redis:
        return False
    try:
        await redis.setex(key, ttl, json.dumps(value))
        return True
    except Exception as e:
        print(f"Cache set error: {e}")
        return False


async def cache_delete(key: str) -> bool:
    """Delete key from cache"""
    global redis, _redis_available
    if not _redis_available or not redis:
        return False
    try:
        await redis.delete(key)
        return True
    except Exception as e:
        print(f"Cache delete error: {e}")
        return False


async def cache_delete_pattern(pattern: str) -> bool:
    """Delete all keys matching pattern"""
    global redis, _redis_available
    if not _redis_available or not redis:
        return False
    try:
        keys = await redis.keys(pattern)
        if keys:
            await asyncio.gather(*[redis.delete(k) for k in keys])
        return True
    except Exception as e:
        print(f"Cache delete pattern error: {e}")
        return False


# =====================
# Cache Key Builders
# =====================

def products_cache_key(page: int = 1, size: int = 20, **filters) -> str:
    """Generate cache key for product list"""
    filter_str = ":".join(f"{k}={v}" for k, v in sorted(filters.items()) if v is not None)
    return f"products:page={page}:size={size}:{filter_str}" if filter_str else f"products:page={page}:size={size}"


def product_cache_key(product_id: int) -> str:
    """Generate cache key for single product"""
    return f"product:{product_id}"


def product_slug_cache_key(slug: str) -> str:
    """Generate cache key for product by slug"""
    return f"product:slug:{slug}"


def search_cache_key(query: str = "", **filters) -> str:
    """Generate cache key for search results"""
    filter_str = ":".join(f"{k}={v}" for k, v in sorted(filters.items()) if v is not None)
    query_part = f"q={query}" if query else "q=*"
    return f"search:{query_part}:{filter_str}" if filter_str else f"search:{query_part}"


def autocomplete_cache_key(query: str) -> str:
    """Generate cache key for autocomplete results"""
    return f"autocomplete:{query.lower()}"


# =====================
# Cache Invalidation
# =====================

async def invalidate_product_cache(product_id: int = None, slug: str = None):
    """Invalidate product cache when admin creates/updates/deletes product"""
    # Delete specific product cache
    if product_id:
        await cache_delete(product_cache_key(product_id))
    if slug:
        await cache_delete(product_slug_cache_key(slug))
    
    # Delete all product list caches
    await cache_delete_pattern("products:*")
    
    # Delete all search caches (search results depend on product data)
    await cache_delete_pattern("search:*")
    
    # Delete all autocomplete caches
    await cache_delete_pattern("autocomplete:*")
