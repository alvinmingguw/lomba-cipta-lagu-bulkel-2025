# -*- coding: utf-8 -*-
"""
Cache Service - Optimized caching layer for performance
Replaces inconsistent caching with unified strategy
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any, Callable
import hashlib
import json
import time
import logging
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheService:
    """Centralized cache service with intelligent invalidation"""
    
    def __init__(self):
        """Initialize cache service"""
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'invalidations': 0
        }
    
    # ==================== CACHE DECORATORS ====================
    
    @staticmethod
    def cache_data(ttl: int = 3600, key_prefix: str = None, show_spinner: bool = True):
        """
        Enhanced cache decorator with better key generation
        
        Args:
            ttl: Time to live in seconds
            key_prefix: Optional prefix for cache key
            show_spinner: Whether to show loading spinner
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = CacheService._generate_cache_key(func, args, kwargs, key_prefix)
                
                # Check if cached
                if cache_key in st.session_state:
                    cached_data = st.session_state[cache_key]
                    if time.time() - cached_data['timestamp'] < ttl:
                        return cached_data['data']
                
                # Execute function
                if show_spinner:
                    with st.spinner(f"Loading {func.__name__}..."):
                        result = func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Cache result
                st.session_state[cache_key] = {
                    'data': result,
                    'timestamp': time.time()
                }
                
                return result
            
            return wrapper
        return decorator
    
    @staticmethod
    def _generate_cache_key(func: Callable, args: tuple, kwargs: dict, prefix: str = None) -> str:
        """Generate unique cache key for function call"""
        # Convert numpy/pandas types to native Python types
        def convert_types(obj):
            if hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            elif hasattr(obj, 'tolist'):  # numpy array
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_types(item) for item in obj]
            else:
                return obj

        # Create key from function name, args, and kwargs
        key_data = {
            'func': func.__name__,
            'args': str(convert_types(args)),
            'kwargs': sorted(convert_types(kwargs).items())
        }

        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()

        if prefix:
            return f"{prefix}_{key_hash}"
        return f"cache_{key_hash}"
    
    # ==================== CACHE MANAGEMENT ====================
    
    @staticmethod
    def invalidate_cache(pattern: str = None):
        """Invalidate cache entries matching pattern"""
        if pattern is None:
            # Clear all cache
            keys_to_remove = [k for k in st.session_state.keys() if k.startswith('cache_')]
        else:
            # Clear specific pattern
            keys_to_remove = [k for k in st.session_state.keys() if pattern in k]
        
        for key in keys_to_remove:
            del st.session_state[key]
        
        logger.info(f"Invalidated {len(keys_to_remove)} cache entries")
    
    @staticmethod
    def invalidate_evaluation_cache():
        """Invalidate evaluation-related cache"""
        CacheService.invalidate_cache('evaluation')
        CacheService.invalidate_cache('leaderboard')
        CacheService.invalidate_cache('analytics')

    def clear_evaluations_cache(self):
        """Clear evaluations-related cache (alias for invalidate_evaluation_cache)"""
        self.invalidate_evaluation_cache()
    
    @staticmethod
    def invalidate_song_cache():
        """Invalidate song-related cache"""
        CacheService.invalidate_cache('song')
        CacheService.invalidate_cache('file')
    
    @staticmethod
    def get_cache_stats() -> Dict[str, int]:
        """Get cache statistics"""
        cache_keys = [k for k in st.session_state.keys() if k.startswith('cache_')]
        return {
            'total_entries': len(cache_keys),
            'memory_usage_mb': sum(len(str(st.session_state[k])) for k in cache_keys) / (1024 * 1024)
        }
    
    # ==================== SPECIALIZED CACHE FUNCTIONS ====================
    
    @staticmethod
    @cache_data(ttl=3600, key_prefix="config")
    def get_cached_config():
        """Get cached configuration"""
        from services.database_service import db_service
        return db_service.get_config()
    
    @staticmethod
    @cache_data(ttl=1800, key_prefix="songs")
    def get_cached_songs():
        """Get cached songs"""
        from services.database_service import db_service
        return db_service.get_songs()
    
    @staticmethod
    @cache_data(ttl=3600, key_prefix="judges")
    def get_cached_judges():
        """Get cached judges"""
        from services.database_service import db_service
        return db_service.get_judges()
    
    @staticmethod
    @cache_data(ttl=3600, key_prefix="rubrics")
    def get_cached_rubrics():
        """Get cached rubrics"""
        from services.database_service import db_service
        return db_service.get_rubrics()
    
    @staticmethod
    @cache_data(ttl=300, key_prefix="evaluations")
    def get_cached_evaluations(judge_id: int = None, song_id: int = None):
        """Get cached evaluations"""
        from services.database_service import db_service
        return db_service.get_evaluations(judge_id, song_id)
    
    @staticmethod
    @cache_data(ttl=600, key_prefix="leaderboard")
    def get_cached_leaderboard():
        """Get cached leaderboard"""
        from services.database_service import db_service
        return db_service.get_leaderboard()
    
    # ==================== FILE CACHE ====================
    
    @staticmethod
    @cache_data(ttl=3600, key_prefix="file_content", show_spinner=False)
    def get_cached_file_content(file_id: str):
        """Get cached file content"""
        from services.file_service import file_service
        return file_service.get_file_content(file_id)
    
    @staticmethod
    @cache_data(ttl=1800, key_prefix="file_url", show_spinner=False)
    def get_cached_file_url(file_id: str):
        """Get cached file URL"""
        from services.file_service import file_service
        return file_service.get_file_url(file_id)
    
    # ==================== PERFORMANCE MONITORING ====================
    
    @staticmethod
    def monitor_cache_performance():
        """Monitor and log cache performance"""
        stats = CacheService.get_cache_stats()
        
        if stats['total_entries'] > 100:
            logger.warning(f"High cache usage: {stats['total_entries']} entries")
        
        if stats['memory_usage_mb'] > 50:
            logger.warning(f"High memory usage: {stats['memory_usage_mb']:.2f} MB")
        
        return stats
    
    # ==================== CACHE WARMING ====================
    
    @staticmethod
    def warm_cache():
        """Pre-load frequently accessed data"""
        try:
            logger.info("Warming cache...")
            
            # Load core data
            CacheService.get_cached_config()
            CacheService.get_cached_judges()
            CacheService.get_cached_rubrics()
            CacheService.get_cached_songs()
            
            # Load recent evaluations
            CacheService.get_cached_evaluations()
            
            logger.info("Cache warming completed")
            
        except Exception as e:
            logger.error(f"Error warming cache: {e}")

# Global instance
cache_service = CacheService()
