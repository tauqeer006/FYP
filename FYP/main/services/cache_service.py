"""
Caching service module.
Handles caching of frequently accessed data and API responses.
"""

import logging
import hashlib
from django.core.cache import cache
from django.conf import settings
from functools import wraps

logger = logging.getLogger(__name__)


class CacheService:
    """Service for handling caching operations"""
    
    # Default cache timeouts (in seconds)
    DEFAULT_TIMEOUT = 300  # 5 minutes
    SHORT_TIMEOUT = 60  # 1 minute
    LONG_TIMEOUT = 3600  # 1 hour
    VERY_LONG_TIMEOUT = 86400  # 24 hours
    
    @staticmethod
    def get(key):
        """
        Retrieve value from cache
        
        Args:
            key (str): Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            value = cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit for key: {key}")
            return value
        except Exception as e:
            logger.warning(f"Error retrieving cache for {key}: {e}")
            return None
    
    @staticmethod
    def set(key, value, timeout=None):
        """
        Store value in cache
        
        Args:
            key (str): Cache key
            value: Value to cache
            timeout (int): Cache timeout in seconds (default: 300)
            
        Returns:
            bool: True if successful
        """
        timeout = timeout or CacheService.DEFAULT_TIMEOUT
        
        try:
            cache.set(key, value, timeout)
            logger.debug(f"Cache set for key: {key} with timeout {timeout}s")
            return True
        except Exception as e:
            logger.error(f"Error setting cache for {key}: {e}")
            return False
    
    @staticmethod
    def delete(key):
        """
        Delete value from cache
        
        Args:
            key (str): Cache key
            
        Returns:
            bool: True if successful
        """
        try:
            cache.delete(key)
            logger.debug(f"Cache deleted for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting cache for {key}: {e}")
            return False
    
    @staticmethod
    def clear_pattern(pattern):
        """
        Clear all cache keys matching a pattern
        
        Args:
            pattern (str): Pattern to match (e.g., 'patient_*')
            
        Returns:
            int: Number of keys cleared
        """
        try:
            if hasattr(cache, 'delete_pattern'):
                result = cache.delete_pattern(pattern)
                logger.info(f"Cache pattern cleared: {pattern}")
                return result
            else:
                logger.warning(f"Cache backend doesn't support pattern deletion: {pattern}")
                return 0
        except Exception as e:
            logger.error(f"Error clearing cache pattern {pattern}: {e}")
            return 0
    
    @staticmethod
    def generate_key(prefix, *args, **kwargs):
        """
        Generate a cache key from prefix and arguments
        
        Args:
            prefix (str): Key prefix
            *args: Arguments to include in key
            **kwargs: Keyword arguments to include in key
            
        Returns:
            str: Generated cache key
        """
        # Create a unique key from all arguments
        key_parts = [str(prefix)]
        
        for arg in args:
            key_parts.append(str(arg))
        
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        
        # Join and hash if too long
        key = ":".join(key_parts)
        
        if len(key) > 250:  # Redis key limit is 512MB, but keep it reasonable
            key = prefix + ":" + hashlib.md5(key.encode()).hexdigest()
        
        return key


def cache_response(timeout=None, key_prefix=None):
    """
    Decorator to cache view responses
    
    Args:
        timeout (int): Cache timeout in seconds
        key_prefix (str): Custom key prefix
        
    Returns:
        Decorated function
    """
    timeout = timeout or CacheService.DEFAULT_TIMEOUT
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key
            if key_prefix:
                cache_key = CacheService.generate_key(
                    key_prefix,
                    request.path,
                    request.user.id if request.user.is_authenticated else 'anonymous'
                )
            else:
                cache_key = CacheService.generate_key(
                    f"view_{view_func.__name__}",
                    request.path,
                    request.user.id if request.user.is_authenticated else 'anonymous'
                )
            
            # Try to get from cache
            cached_value = CacheService.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute view function
            response = view_func(request, *args, **kwargs)
            
            # Cache the response
            CacheService.set(cache_key, response, timeout)
            
            return response
        
        return wrapper
    
    return decorator


def cache_result(timeout=None, key_prefix=None):
    """
    Decorator to cache function results
    
    Args:
        timeout (int): Cache timeout in seconds
        key_prefix (str): Custom key prefix
        
    Returns:
        Decorated function
    """
    timeout = timeout or CacheService.DEFAULT_TIMEOUT
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_prefix:
                cache_key = CacheService.generate_key(key_prefix, *args, **kwargs)
            else:
                cache_key = CacheService.generate_key(f"func_{func.__name__}", *args, **kwargs)
            
            # Try to get from cache
            cached_value = CacheService.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache the result
            CacheService.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    
    return decorator


class GeminiResponseCache:
    """Specialized caching for Gemini API responses"""
    
    PREFIX = "gemini_response"
    TIMEOUT = CacheService.LONG_TIMEOUT  # 1 hour
    
    @staticmethod
    def get_or_generate(prompt, generator_func, timeout=None):
        """
        Get cached Gemini response or generate new one
        
        Args:
            prompt (str): Prompt text
            generator_func: Function to generate response if not cached
            timeout (int): Cache timeout
            
        Returns:
            str: Generated or cached response
        """
        timeout = timeout or GeminiResponseCache.TIMEOUT
        
        # Generate cache key from prompt
        cache_key = CacheService.generate_key(
            GeminiResponseCache.PREFIX,
            hashlib.md5(prompt.encode()).hexdigest()
        )
        
        # Try to get cached response
        cached_response = CacheService.get(cache_key)
        if cached_response is not None:
            logger.info(f"Using cached Gemini response for prompt hash")
            return cached_response
        
        # Generate new response
        logger.info("Generating new Gemini response")
        response = generator_func(prompt)
        
        # Cache the response
        CacheService.set(cache_key, response, timeout)
        
        return response
    
    @staticmethod
    def invalidate_prompt_cache(prompt):
        """
        Invalidate cache for a specific prompt
        
        Args:
            prompt (str): Prompt text
        """
        cache_key = CacheService.generate_key(
            GeminiResponseCache.PREFIX,
            hashlib.md5(prompt.encode()).hexdigest()
        )
        CacheService.delete(cache_key)
        logger.info(f"Invalidated Gemini cache for prompt")


class PatientDataCache:
    """Specialized caching for patient data"""
    
    PREFIX = "patient"
    TIMEOUT = CacheService.LONG_TIMEOUT  # 1 hour
    
    @staticmethod
    def get_patient(patient_id):
        """Get cached patient data"""
        cache_key = CacheService.generate_key(PatientDataCache.PREFIX, "patient", patient_id)
        return CacheService.get(cache_key)
    
    @staticmethod
    def set_patient(patient_id, patient_data, timeout=None):
        """Cache patient data"""
        timeout = timeout or PatientDataCache.TIMEOUT
        cache_key = CacheService.generate_key(PatientDataCache.PREFIX, "patient", patient_id)
        return CacheService.set(cache_key, patient_data, timeout)
    
    @staticmethod
    def get_patient_xrays(patient_id):
        """Get cached patient X-ray records"""
        cache_key = CacheService.generate_key(PatientDataCache.PREFIX, "xrays", patient_id)
        return CacheService.get(cache_key)
    
    @staticmethod
    def set_patient_xrays(patient_id, xray_data, timeout=None):
        """Cache patient X-ray records"""
        timeout = timeout or PatientDataCache.TIMEOUT
        cache_key = CacheService.generate_key(PatientDataCache.PREFIX, "xrays", patient_id)
        return CacheService.set(cache_key, xray_data, timeout)
    
    @staticmethod
    def invalidate_patient(patient_id):
        """Invalidate all caches for a patient"""
        CacheService.delete(CacheService.generate_key(PatientDataCache.PREFIX, "patient", patient_id))
        CacheService.delete(CacheService.generate_key(PatientDataCache.PREFIX, "xrays", patient_id))
        logger.info(f"Invalidated cache for patient {patient_id}")
    
    @staticmethod
    def invalidate_doctor_patients(doctor_id):
        """Invalidate patient list cache for a doctor"""
        cache_key = CacheService.generate_key(PatientDataCache.PREFIX, "doctor", doctor_id)
        CacheService.delete(cache_key)
        logger.info(f"Invalidated patient list cache for doctor {doctor_id}")
