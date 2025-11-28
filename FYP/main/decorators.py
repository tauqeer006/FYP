"""
Custom decorators for views.
Handles rate limiting, authentication checks, and request validation.
"""

import logging
import functools
from django.http import JsonResponse
from django.core.cache import cache
from django.contrib.auth.decorators import login_required, user_passes_test
from django_ratelimit.decorators import ratelimit
from main.response_helpers import (
    rate_limit_exceeded,
    unauthorized,
    error_response
)

logger = logging.getLogger(__name__)


def rate_limit_view(rate_str):
    """
    Decorator for rate limiting views
    
    Args:
        rate_str (str): Rate limit string (e.g., '10/m' for 10 per minute)
        
    Returns:
        Decorated function with rate limiting
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        @ratelimit(key='ip', rate=rate_str, method='POST', block=True)
        def wrapper(request, *args, **kwargs):
            try:
                return view_func(request, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in rate_limit_view: {e}")
                return error_response(f"An error occurred: {str(e)}", status_code=500)
        return wrapper
    return decorator


def require_ajax(view_func):
    """
    Decorator to ensure request is AJAX
    
    Args:
        view_func: View function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            logger.warning(f"Non-AJAX request to {request.path}")
            return JsonResponse({'error': 'Invalid request'}, status=400)
        return view_func(request, *args, **kwargs)
    return wrapper


def require_post(view_func):
    """
    Decorator to ensure request is POST
    
    Args:
        view_func: View function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method != 'POST':
            logger.warning(f"Non-POST request to {request.path}")
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        return view_func(request, *args, **kwargs)
    return wrapper


def require_get(view_func):
    """
    Decorator to ensure request is GET
    
    Args:
        view_func: View function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method != 'GET':
            logger.warning(f"Non-GET request to {request.path}")
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        return view_func(request, *args, **kwargs)
    return wrapper


def require_user_type(*user_types):
    """
    Decorator to check if user has specific user_type
    
    Args:
        *user_types (str): Allowed user types (e.g., 'admin', 'doctor', 'patient')
        
    Returns:
        Decorated function
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                logger.warning(f"Unauthenticated access to {request.path}")
                return unauthorized("User authentication required")
            
            if hasattr(request.user, 'user_type') and request.user.user_type in user_types:
                return view_func(request, *args, **kwargs)
            
            logger.warning(f"User {request.user.username} with type {getattr(request.user, 'user_type', 'unknown')} denied access to {request.path}")
            return JsonResponse(
                {'error': 'Access denied', 'message': 'You do not have permission to access this resource'},
                status=403
            )
        return wrapper
    return decorator


def check_ajax_and_post(view_func):
    """
    Decorator to ensure request is both AJAX and POST
    
    Args:
        view_func: View function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method != 'POST':
            logger.warning(f"Non-POST request to AJAX endpoint {request.path}")
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            logger.warning(f"Non-AJAX POST request to {request.path}")
            return JsonResponse({'error': 'Invalid request'}, status=400)
        
        return view_func(request, *args, **kwargs)
    return wrapper


def login_required_api(view_func):
    """
    Decorator for API endpoints requiring login
    
    Args:
        view_func: View function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            logger.warning(f"Unauthenticated API access attempt to {request.path}")
            return unauthorized("Authentication required")
        return view_func(request, *args, **kwargs)
    return wrapper


def log_view_access(view_func):
    """
    Decorator to log view access
    
    Args:
        view_func: View function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user.username if request.user.is_authenticated else 'Anonymous'
        logger.info(f"Access to {request.path} by {user} ({request.method})")
        return view_func(request, *args, **kwargs)
    return wrapper


def handle_api_errors(view_func):
    """
    Decorator to handle API errors consistently
    
    Args:
        view_func: View function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except ValueError as e:
            logger.warning(f"ValueError in {view_func.__name__}: {e}")
            return error_response(str(e), status_code=400)
        except KeyError as e:
            logger.warning(f"Missing required field in {view_func.__name__}: {e}")
            return error_response(f"Missing required field: {str(e)}", status_code=400)
        except Exception as e:
            logger.error(f"Unexpected error in {view_func.__name__}: {e}", exc_info=True)
            return error_response("An internal error occurred", status_code=500)
    return wrapper
