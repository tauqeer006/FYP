"""
API Authentication and Authorization utilities
"""
from functools import wraps
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import logging

logger = logging.getLogger(__name__)


def api_login_required(view_func):
    """
    Decorator to require login for API endpoints
    Returns JSON response instead of redirect
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


def api_permission_required(permission_name):
    """
    Decorator to require specific permission for API endpoints
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'error': 'Authentication required'
                }, status=401)
            
            if not request.user.has_perm(permission_name):
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def doctor_only(view_func):
    """
    Decorator to require doctor user type
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)
        
        if getattr(request.user, 'user_type', None) != 'doctor':
            return JsonResponse({
                'success': False,
                'error': 'Doctor access required'
            }, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper


def patient_only(view_func):
    """
    Decorator to require patient user type
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)
        
        if getattr(request.user, 'user_type', None) != 'patient':
            return JsonResponse({
                'success': False,
                'error': 'Patient access required'
            }, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper


def handle_api_errors(view_func):
    """
    Decorator to handle common API errors
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Invalid input: {str(e)}'
            }, status=400)
        except PermissionError as e:
            logger.warning(f"Permission error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Permission denied'
            }, status=403)
        except Exception as e:
            logger.error(f"Unexpected error in {view_func.__name__}: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'An error occurred. Please try again later.'
            }, status=500)
    return wrapper
