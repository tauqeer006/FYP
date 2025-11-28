"""
External API service module.
Handles communication with Flask ML APIs and external services.
"""

import logging
import requests
from django.conf import settings
from requests.exceptions import Timeout, ConnectionError, RequestException

logger = logging.getLogger(__name__)


class MLAPIService:
    """Service for communicating with ML APIs"""
    
    def __init__(self):
        """Initialize API service with configuration"""
        self.cnn_api_url = getattr(settings, 'FLASK_CNN_API_URL', 'http://localhost:5001')
        self.xray_api_url = getattr(settings, 'FLASK_XRAY_API_URL', 'http://localhost:5002')
        self.pose_api_url = getattr(settings, 'FLASK_POSE_API_URL', 'http://localhost:5003')
        self.timeout = getattr(settings, 'API_REQUEST_TIMEOUT', 30)
        self.headers = {'Content-Type': 'application/json'}
    
    def _make_request(self, url, method='GET', data=None, files=None, timeout=None):
        """
        Make HTTP request to API
        
        Args:
            url (str): API endpoint URL
            method (str): HTTP method (GET, POST, etc)
            data (dict): JSON data to send
            files (dict): Files to upload
            timeout (int): Request timeout in seconds
            
        Returns:
            dict: API response or error dict
        """
        timeout = timeout or self.timeout
        
        try:
            if method == 'POST':
                if files:
                    # For file uploads, don't set Content-Type header
                    headers = {}
                    response = requests.post(url, files=files, data=data, headers=headers, timeout=timeout)
                else:
                    response = requests.post(url, json=data, headers=self.headers, timeout=timeout)
            elif method == 'GET':
                response = requests.get(url, params=data, headers=self.headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except Timeout:
            logger.error(f"Request to {url} timed out after {timeout}s")
            return {'error': 'API request timed out', 'status': 'error'}
        except ConnectionError:
            logger.error(f"Connection error to {url}")
            return {'error': 'API service unavailable', 'status': 'error'}
        except RequestException as e:
            logger.error(f"Request error to {url}: {e}")
            return {'error': f'API request failed: {str(e)}', 'status': 'error'}
        except Exception as e:
            logger.error(f"Unexpected error calling {url}: {e}")
            return {'error': 'Unexpected API error', 'status': 'error'}
    
    def detect_fracture(self, image_path=None, image_data=None):
        """
        Detect fracture using CNN API
        
        Args:
            image_path (str): Path to image file
            image_data (bytes): Image data as bytes
            
        Returns:
            dict: Detection results
        """
        try:
            url = f"{self.cnn_api_url}/detect"
            
            if image_data:
                files = {'image': ('image.jpg', image_data)}
                result = self._make_request(url, method='POST', files=files)
            elif image_path:
                with open(image_path, 'rb') as f:
                    files = {'image': f}
                    result = self._make_request(url, method='POST', files=files)
            else:
                return {'error': 'No image provided', 'status': 'error'}
            
            logger.info(f"Fracture detection completed: {result.get('status')}")
            return result
            
        except Exception as e:
            logger.error(f"Error in fracture detection: {e}")
            return {'error': str(e), 'status': 'error'}
    
    def classify_xray(self, image_path=None, image_data=None):
        """
        Classify X-ray using X-ray API
        
        Args:
            image_path (str): Path to image file
            image_data (bytes): Image data as bytes
            
        Returns:
            dict: Classification results
        """
        try:
            url = f"{self.xray_api_url}/classify"
            
            if image_data:
                files = {'image': ('image.jpg', image_data)}
                result = self._make_request(url, method='POST', files=files)
            elif image_path:
                with open(image_path, 'rb') as f:
                    files = {'image': f}
                    result = self._make_request(url, method='POST', files=files)
            else:
                return {'error': 'No image provided', 'status': 'error'}
            
            logger.info(f"X-ray classification completed: {result.get('status')}")
            return result
            
        except Exception as e:
            logger.error(f"Error in X-ray classification: {e}")
            return {'error': str(e), 'status': 'error'}
    
    def analyze_pose(self, image_path=None, image_data=None):
        """
        Analyze pose using Pose API
        
        Args:
            image_path (str): Path to image file
            image_data (bytes): Image data as bytes
            
        Returns:
            dict: Pose analysis results
        """
        try:
            url = f"{self.pose_api_url}/analyze"
            
            if image_data:
                files = {'image': ('image.jpg', image_data)}
                result = self._make_request(url, method='POST', files=files)
            elif image_path:
                with open(image_path, 'rb') as f:
                    files = {'image': f}
                    result = self._make_request(url, method='POST', files=files)
            else:
                return {'error': 'No image provided', 'status': 'error'}
            
            logger.info(f"Pose analysis completed: {result.get('status')}")
            return result
            
        except Exception as e:
            logger.error(f"Error in pose analysis: {e}")
            return {'error': str(e), 'status': 'error'}
    
    def get_api_status(self, api_type='cnn'):
        """
        Check if API service is available
        
        Args:
            api_type (str): API type ('cnn', 'xray', 'pose')
            
        Returns:
            dict: Status information
        """
        try:
            if api_type == 'cnn':
                url = f"{self.cnn_api_url}/status"
            elif api_type == 'xray':
                url = f"{self.xray_api_url}/status"
            elif api_type == 'pose':
                url = f"{self.pose_api_url}/status"
            else:
                return {'status': 'error', 'message': 'Invalid API type'}
            
            result = self._make_request(url, method='GET', timeout=5)
            return result
            
        except Exception as e:
            logger.error(f"Error checking {api_type} API status: {e}")
            return {'status': 'error', 'available': False}


class GeminiAPIService:
    """Service for communicating with Google Gemini API"""
    
    def __init__(self):
        """Initialize Gemini API service"""
        self.api_key = getattr(settings, 'GEMINI_API_KEY', None)
        self.timeout = getattr(settings, 'API_REQUEST_TIMEOUT', 30)
    
    def send_message(self, message, context=None):
        """
        Send message to Gemini API
        
        Args:
            message (str): User message
            context (str): Optional context for the conversation
            
        Returns:
            dict: API response
        """
        # This is a placeholder - actual implementation depends on Gemini SDK
        logger.info(f"Sending message to Gemini: {message[:50]}...")
        return {'status': 'success', 'message': 'Response from Gemini'}
    
    def generate_report(self, findings, patient_data):
        """
        Generate a medical report using Gemini API
        
        Args:
            findings (dict): Medical findings
            patient_data (dict): Patient information
            
        Returns:
            str: Generated report
        """
        try:
            # Construct prompt for Gemini
            prompt = f"""
Generate a medical report based on the following:

Patient Information:
- Name: {patient_data.get('name', 'N/A')}
- Age: {patient_data.get('age', 'N/A')}
- Gender: {patient_data.get('gender', 'N/A')}

Findings:
{findings}

Please generate a professional medical report.
            """
            
            result = self.send_message(prompt)
            logger.info("Medical report generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {'error': str(e)}
