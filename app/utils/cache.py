"""Caching utilities using Python's built-in functools module."""
from functools import lru_cache, wraps
from typing import Any, Callable, TypeVar, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


def timed_cache(seconds: int = 300) -> Callable:
    """
    Decorator that caches function results with a time-to-live (TTL).
    
    Args:
        seconds: Cache duration in seconds (default: 5 minutes)
    
    Example:
        @timed_cache(seconds=600)
        def get_job_listings():
            # Expensive DB query
            return db.query(JobPosting).all()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache: dict[tuple, tuple[T, datetime]] = {}
        
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Create cache key from function arguments
            cache_key = (args, tuple(sorted(kwargs.items())))
            
            # Check if cached and not expired
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=seconds):
                    logger.debug(f"Cache hit for {func.__name__}")
                    return result
                else:
                    # Remove expired cache entry
                    del cache[cache_key]
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[cache_key] = (result, datetime.now())
            logger.debug(f"Cache miss for {func.__name__} - result cached for {seconds}s")
            return result
        
        # Add cache management methods
        def clear_cache():
            """Clear all cached results."""
            cache.clear()
            logger.info(f"Cache cleared for {func.__name__}")
        
        def cache_info():
            """Get cache statistics."""
            return {
                "function": func.__name__,
                "cached_entries": len(cache),
                "ttl_seconds": seconds
            }
        
        wrapper.clear_cache = clear_cache  # type: ignore
        wrapper.cache_info = cache_info  # type: ignore
        
        return wrapper
    
    return decorator


def simple_cache(func: Callable[..., T]) -> Callable[..., T]:
    """
    Simple in-memory cache decorator for pure functions (no TTL).
    Uses Python's built-in functools.lru_cache under the hood.
    
    Maintains cache until explicitly cleared or process restarts.
    
    Example:
        @simple_cache
        def calculate_officer_risk_level(badge_level: str) -> int:
            return badge_to_risk_mapping[badge_level]
    """
    @lru_cache(maxsize=256)
    def cached_func(*args: Any, **kwargs: Any) -> T:
        return func(*args, **kwargs)
    
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        return cached_func(*args, **kwargs)
    
    def clear_cache():
        """Clear all cached results."""
        cached_func.cache_clear()
        logger.info(f"Cache cleared for {func.__name__}")
    
    def cache_info():
        """Get cache statistics."""
        info = cached_func.cache_info()
        return {
            "function": func.__name__,
            "hits": info.hits,
            "misses": info.misses,
            "current_size": info.currsize,
            "max_size": info.maxsize
        }
    
    wrapper.clear_cache = clear_cache  # type: ignore
    wrapper.cache_info = cache_info  # type: ignore
    
    return wrapper


def cached_property_with_ttl(seconds: int = 300):
    """
    Decorator for caching property/method results with TTL on class instances.
    
    Example:
        class UserRepository:
            @cached_property_with_ttl(seconds=600)
            def get_all_officers(self):
                return db.query(Officer).all()
    """
    def decorator(func: Callable) -> property:
        cache_attr = f"_cache_{func.__name__}"
        timestamp_attr = f"_cache_timestamp_{func.__name__}"
        
        def fget(self: Any) -> Any:
            now = datetime.now()
            cached_value = getattr(self, cache_attr, None)
            cached_time = getattr(self, timestamp_attr, None)
            
            # Return cached value if not expired
            if cached_value is not None and cached_time is not None:
                if now - cached_time < timedelta(seconds=seconds):
                    return cached_value
            
            # Compute and cache new value
            value = func(self)
            setattr(self, cache_attr, value)
            setattr(self, timestamp_attr, now)
            return value
        
        return property(fget)
    
    return decorator


# Pre-configured caching decorators for common use cases
cache_5min = timed_cache(seconds=300)      # 5 minutes
cache_15min = timed_cache(seconds=900)     # 15 minutes
cache_60min = timed_cache(seconds=3600)    # 1 hour
cache_24hr = timed_cache(seconds=86400)    # 24 hours

