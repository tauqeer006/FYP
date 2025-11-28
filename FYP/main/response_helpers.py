"""
Response helpers module for standardized API responses.
Provides consistent JSON response format across all API endpoints.
"""

from django.http import JsonResponse
from django.core.paginator import Paginator
import logging

logger = logging.getLogger(__name__)


# ==================== STANDARD RESPONSES ====================

def success_response(data=None, message="Success", status_code=200):
    """
    Return a standardized success response
    
    Args:
        data (dict/list): Response data (optional)
        message (str): Human-readable message
        status_code (int): HTTP status code
        
    Returns:
        JsonResponse: Standard JSON response
        
    Example:
        return success_response(
            data={'user_id': 123, 'name': 'John'},
            message="User created successfully",
            status_code=201
        )
    """
    response = {
        'success': True,
        'message': message,
    }
    
    if data is not None:
        response['data'] = data
    
    logger.info(f"Success response: {message}")
    return JsonResponse(response, status=status_code)


def error_response(message, status_code=400, error_code=None, details=None):
    """
    Return a standardized error response
    
    Args:
        message (str): Error message
        status_code (int): HTTP status code
        error_code (str): Machine-readable error code (optional)
        details (dict): Additional error details (optional)
        
    Returns:
        JsonResponse: Standard JSON error response
        
    Example:
        return error_response(
            message="Invalid credentials",
            status_code=401,
            error_code="INVALID_CREDENTIALS"
        )
    """
    response = {
        'success': False,
        'message': message,
    }
    
    if error_code:
        response['error_code'] = error_code
    
    if details:
        response['details'] = details
    
    logger.warning(f"Error response ({status_code}): {message}")
    return JsonResponse(response, status=status_code)


# ==================== SPECIFIC ERROR RESPONSES ====================

def bad_request(message, details=None):
    """Return 400 Bad Request response"""
    return error_response(message, status_code=400, error_code="BAD_REQUEST", details=details)


def unauthorized(message="Authentication required"):
    """Return 401 Unauthorized response"""
    return error_response(message, status_code=401, error_code="UNAUTHORIZED")


def forbidden(message="Access denied"):
    """Return 403 Forbidden response"""
    return error_response(message, status_code=403, error_code="FORBIDDEN")


def not_found(message="Resource not found"):
    """Return 404 Not Found response"""
    return error_response(message, status_code=404, error_code="NOT_FOUND")


def conflict(message, details=None):
    """Return 409 Conflict response (e.g., duplicate resource)"""
    return error_response(message, status_code=409, error_code="CONFLICT", details=details)


def validation_error(message, details=None):
    """Return 422 Unprocessable Entity response"""
    return error_response(message, status_code=422, error_code="VALIDATION_ERROR", details=details)


def rate_limit_exceeded(remaining_requests=0, reset_time=0):
    """Return 429 Too Many Requests response"""
    details = {
        'remaining_requests': remaining_requests,
        'reset_time_seconds': reset_time
    }
    return error_response(
        "Too many requests. Please try again later.",
        status_code=429,
        error_code="RATE_LIMIT_EXCEEDED",
        details=details
    )


def server_error(message="An internal server error occurred", error_id=None):
    """Return 500 Internal Server Error response"""
    details = {}
    if error_id:
        details['error_id'] = error_id
        logger.error(f"Server error (ID: {error_id}): {message}")
    else:
        logger.error(f"Server error: {message}")
    
    return error_response(
        message,
        status_code=500,
        error_code="INTERNAL_SERVER_ERROR",
        details=details if details else None
    )


def service_unavailable(message="Service temporarily unavailable"):
    """Return 503 Service Unavailable response"""
    return error_response(message, status_code=503, error_code="SERVICE_UNAVAILABLE")


# ==================== SPECIALIZED RESPONSES ====================

def paginated_response(queryset, serializer_func, page_number=1, page_size=20):
    """
    Return a paginated response
    
    Args:
        queryset: Django QuerySet
        serializer_func: Function to serialize each item
        page_number (int): Page number
        page_size (int): Items per page
        
    Returns:
        JsonResponse: Paginated data with metadata
        
    Example:
        def serialize_patient(patient):
            return {
                'id': patient.id,
                'name': f"{patient.fname} {patient.lname}",
                'age': patient.age
            }
        
        return paginated_response(
            Patient.objects.all(),
            serialize_patient,
            page_number=1,
            page_size=10
        )
    """
    paginator = Paginator(queryset, page_size)
    
    try:
        page = paginator.page(page_number)
    except Exception:
        return error_response("Invalid page number", 400)
    
    serialized_data = [serializer_func(item) for item in page.object_list]
    
    response = {
        'success': True,
        'data': serialized_data,
        'pagination': {
            'current_page': page_number,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'items_per_page': page_size,
            'has_next': page.has_next(),
            'has_previous': page.has_previous(),
        }
    }
    
    return JsonResponse(response)


def list_response(items, message="Retrieved successfully", serializer_func=None):
    """
    Return a list response
    
    Args:
        items (list): List of items to return
        message (str): Response message
        serializer_func: Optional function to serialize each item
        
    Returns:
        JsonResponse: List data with metadata
    """
    if serializer_func:
        data = [serializer_func(item) for item in items]
    else:
        data = items
    
    response = {
        'success': True,
        'message': message,
        'data': data,
        'count': len(data)
    }
    
    return JsonResponse(response)


def created_response(data, message="Resource created successfully"):
    """Return 201 Created response"""
    return success_response(data, message, status_code=201)


def no_content_response():
    """Return 204 No Content response"""
    return JsonResponse({'success': True}, status=204)


# ==================== RESPONSE DECORATORS ====================

def handle_validation_errors(func):
    """
    Decorator to handle validation errors in view functions
    
    Usage:
        @handle_validation_errors
        def my_view(request):
            from main.validators import validate_email
            email = validate_email(request.POST.get('email'))
            # ValidationError is automatically caught and returned as error_response
    """
    from functools import wraps
    from django.core.exceptions import ValidationError
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error: {e.message}")
            return validation_error(str(e.message))
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return server_error(str(e))
    
    return wrapper


# ==================== ERROR LOGGING ====================

def log_error(message, error=None, level='error', context=None):
    """
    Log an error with context information
    
    Args:
        message (str): Error message
        error (Exception): Exception object (optional)
        level (str): Log level ('debug', 'info', 'warning', 'error', 'critical')
        context (dict): Additional context information
    """
    log_message = message
    
    if error:
        log_message += f" - {type(error).__name__}: {str(error)}"
    
    if context:
        log_message += f" - Context: {context}"
    
    if level == 'debug':
        logger.debug(log_message)
    elif level == 'info':
        logger.info(log_message)
    elif level == 'warning':
        logger.warning(log_message)
    elif level == 'error':
        logger.error(log_message)
    elif level == 'critical':
        logger.critical(log_message)
