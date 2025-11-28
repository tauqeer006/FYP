"""
Health check and monitoring service.
Provides endpoints for system status monitoring and alerting.
"""

import logging
import os
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import requests

logger = logging.getLogger(__name__)


class HealthCheckService:
    """Service for health checks and monitoring"""
    
    @staticmethod
    def check_database_connection():
        """
        Check if database connection is working
        
        Returns:
            dict: Status and details
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            logger.info("Database health check passed")
            return {
                'status': 'healthy',
                'service': 'database',
                'message': 'Database connection successful'
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'service': 'database',
                'message': f'Database connection failed: {str(e)}'
            }
    
    @staticmethod
    def check_cache_connection():
        """
        Check if cache (Redis) connection is working
        
        Returns:
            dict: Status and details
        """
        try:
            # Try to set and get a test value
            test_key = 'health_check_test'
            test_value = 'test'
            
            cache.set(test_key, test_value, 10)
            retrieved = cache.get(test_key)
            
            if retrieved == test_value:
                cache.delete(test_key)
                logger.info("Cache health check passed")
                return {
                    'status': 'healthy',
                    'service': 'cache',
                    'message': 'Cache connection successful'
                }
            else:
                raise Exception("Cache value mismatch")
        
        except Exception as e:
            logger.warning(f"Cache health check failed: {e}")
            return {
                'status': 'degraded',
                'service': 'cache',
                'message': f'Cache connection failed: {str(e)}'
            }
    
    @staticmethod
    def check_gemini_api():
        """
        Check if Gemini API is accessible
        
        Returns:
            dict: Status and details
        """
        try:
            api_key = os.getenv('GEMINI_API_KEY', '')
            
            if not api_key:
                logger.warning("Gemini API key not configured")
                return {
                    'status': 'warning',
                    'service': 'gemini_api',
                    'message': 'Gemini API key not configured'
                }
            
            # Try a simple API call
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            headers = {'Content-Type': 'application/json'}
            data = {
                "contents": [{"parts": [{"text": "Hello"}]}]
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("Gemini API health check passed")
                return {
                    'status': 'healthy',
                    'service': 'gemini_api',
                    'message': 'Gemini API accessible'
                }
            else:
                logger.warning(f"Gemini API returned status {response.status_code}")
                return {
                    'status': 'unhealthy',
                    'service': 'gemini_api',
                    'message': f'Gemini API returned status {response.status_code}'
                }
        
        except requests.Timeout:
            logger.warning("Gemini API timeout")
            return {
                'status': 'unhealthy',
                'service': 'gemini_api',
                'message': 'Gemini API timeout'
            }
        except Exception as e:
            logger.error(f"Gemini API health check failed: {e}")
            return {
                'status': 'unhealthy',
                'service': 'gemini_api',
                'message': f'Gemini API error: {str(e)}'
            }
    
    @staticmethod
    def check_external_apis():
        """
        Check if external ML APIs are accessible
        
        Returns:
            dict: Status and details for all APIs
        """
        results = {}
        
        # Check CNN API
        try:
            cnn_url = getattr(settings, 'FLASK_CNN_API_URL', 'http://cnn-api:5001')
            response = requests.get(f"{cnn_url}/status", timeout=5)
            results['cnn_api'] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'message': f'Status code: {response.status_code}'
            }
        except Exception as e:
            logger.warning(f"CNN API health check failed: {e}")
            results['cnn_api'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
        
        # Check X-ray API
        try:
            xray_url = getattr(settings, 'FLASK_XRAY_API_URL', 'http://xray-api:5002')
            response = requests.get(f"{xray_url}/status", timeout=5)
            results['xray_api'] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'message': f'Status code: {response.status_code}'
            }
        except Exception as e:
            logger.warning(f"X-ray API health check failed: {e}")
            results['xray_api'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
        
        # Check Pose API
        try:
            pose_url = getattr(settings, 'FLASK_POSE_API_URL', 'http://pose-api:5003')
            response = requests.get(f"{pose_url}/status", timeout=5)
            results['pose_api'] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'message': f'Status code: {response.status_code}'
            }
        except Exception as e:
            logger.warning(f"Pose API health check failed: {e}")
            results['pose_api'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
        
        return results
    
    @staticmethod
    def get_full_health_status():
        """
        Get complete system health status
        
        Returns:
            dict: Complete health status
        """
        return {
            'timestamp': str(__import__('datetime').datetime.now()),
            'database': HealthCheckService.check_database_connection(),
            'cache': HealthCheckService.check_cache_connection(),
            'gemini_api': HealthCheckService.check_gemini_api(),
            'external_apis': HealthCheckService.check_external_apis(),
            'overall_status': 'healthy'  # Will be updated based on checks
        }


class MonitoringService:
    """Service for application monitoring and metrics"""
    
    @staticmethod
    def log_request(request, response, duration):
        """
        Log request details for monitoring
        
        Args:
            request: Django request object
            response: Django response object
            duration (float): Request duration in seconds
        """
        logger.info(
            f"HTTP {response.status_code} {request.method} {request.path} "
            f"({duration:.2f}s) User: {request.user.username if request.user.is_authenticated else 'Anonymous'}"
        )
    
    @staticmethod
    def log_api_call(api_name, endpoint, status_code, duration):
        """
        Log external API call for monitoring
        
        Args:
            api_name (str): Name of API
            endpoint (str): API endpoint
            status_code (int): Response status code
            duration (float): Request duration in seconds
        """
        logger.info(
            f"API_CALL {api_name} {endpoint} {status_code} ({duration:.2f}s)"
        )
    
    @staticmethod
    def log_performance_metric(metric_name, value, unit='ms'):
        """
        Log performance metric
        
        Args:
            metric_name (str): Name of metric
            value (float): Metric value
            unit (str): Unit of measurement
        """
        logger.info(f"METRIC {metric_name}={value}{unit}")
    
    @staticmethod
    def log_error_event(error_type, error_message, context=None):
        """
        Log error event for monitoring
        
        Args:
            error_type (str): Type of error
            error_message (str): Error message
            context (dict): Additional context
        """
        context_str = f" Context: {context}" if context else ""
        logger.error(f"ERROR_EVENT {error_type}: {error_message}{context_str}")
