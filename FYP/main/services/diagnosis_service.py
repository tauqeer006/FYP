"""
Diagnosis service module.
Handles medical diagnosis, analysis, and report generation.
"""

import logging
import os
import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from requests.exceptions import Timeout, RequestException

logger = logging.getLogger(__name__)


class DiagnosisService:
    """Service for handling diagnosis operations"""
    
    @staticmethod
    def detect_fracture_from_xray(image_file, timeout=None):
        """
        Detect fracture using X-ray API
        
        Args:
            image_file: Image file object or bytes
            timeout (int): Request timeout in seconds
            
        Returns:
            dict: Detection results with fracture types and confidence
            
        Raises:
            ValidationError: If API call fails
        """
        timeout = timeout or getattr(settings, 'API_REQUEST_TIMEOUT', 30)
        
        try:
            flask_url = getattr(settings, 'FLASK_XRAY_API_URL', 'http://xray-api:5002')
            url = f"{flask_url}/detect-fracture"
            
            response = requests.post(
                url,
                files={'image': image_file},
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Fracture detection successful: {result.get('status')}")
            return result
        
        except Timeout:
            logger.error("Fracture detection API timeout")
            raise ValidationError("Fracture detection API timeout. Please try again.")
        except RequestException as e:
            logger.error(f"Fracture detection API error: {e}")
            raise ValidationError(f"Fracture detection failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in fracture detection: {e}")
            raise ValidationError("An unexpected error occurred during fracture detection")
    
    @staticmethod
    def predict_fracture_side(image_file, timeout=None):
        """
        Predict left/right side of fracture using CNN
        
        Args:
            image_file: Image file object or bytes
            timeout (int): Request timeout in seconds
            
        Returns:
            dict: Prediction results with side and confidence
            
        Raises:
            ValidationError: If API call fails
        """
        timeout = timeout or getattr(settings, 'API_REQUEST_TIMEOUT', 30)
        
        try:
            flask_url = getattr(settings, 'FLASK_CNN_API_URL', 'http://cnn-api:5001')
            url = f"{flask_url}/predict-lr"
            
            response = requests.post(
                url,
                files={'image': image_file},
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Side prediction successful: {result.get('prediction')}")
            return result
        
        except Timeout:
            logger.error("Side prediction API timeout")
            raise ValidationError("Side prediction API timeout. Please try again.")
        except RequestException as e:
            logger.error(f"Side prediction API error: {e}")
            raise ValidationError(f"Side prediction failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in side prediction: {e}")
            raise ValidationError("An unexpected error occurred during side prediction")
    
    @staticmethod
    def generate_gemini_report(prompt, timeout=None):
        """
        Generate report using Gemini API
        
        Args:
            prompt (str): Prompt for Gemini
            timeout (int): Request timeout in seconds
            
        Returns:
            str: Generated report text
            
        Raises:
            ValidationError: If API call fails
        """
        timeout = timeout or getattr(settings, 'API_REQUEST_TIMEOUT', 30)
        api_key = os.getenv('GEMINI_API_KEY', '')
        
        if not api_key:
            logger.error("Gemini API key not configured")
            raise ValidationError("Gemini API key not configured. Please check .env file.")
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            
            headers = {'Content-Type': 'application/json'}
            data = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            generated_text = result['candidates'][0]['content']['parts'][0]['text']
            logger.info("Gemini report generated successfully")
            return generated_text
        
        except Timeout:
            logger.error("Gemini API timeout")
            raise ValidationError("Gemini API timeout. Please try again.")
        except RequestException as e:
            logger.error(f"Gemini API error: {e}")
            raise ValidationError(f"Gemini API error: {str(e)}")
        except (KeyError, IndexError) as e:
            logger.error(f"Invalid Gemini API response: {e}")
            raise ValidationError("Invalid response from Gemini API")
        except Exception as e:
            logger.error(f"Unexpected error in Gemini report generation: {e}")
            raise ValidationError("An unexpected error occurred during report generation")
    
    @staticmethod
    def generate_clinical_summary(patient_findings, timeout=None):
        """
        Generate clinical summary from findings
        
        Args:
            patient_findings (str): Clinical findings text
            timeout (int): Request timeout in seconds
            
        Returns:
            str: Generated summary
        """
        prompt = f"""
        Summarize the following clinical findings into a short medical summary suitable for a doctor's report:
        Write only 2 lines to generate a small summary
        
        Findings:
        {patient_findings}
        """
        
        try:
            return DiagnosisService.generate_gemini_report(prompt, timeout)
        except ValidationError:
            logger.warning("Failed to generate summary, returning default")
            return "Clinical summary could not be generated at this time."
    
    @staticmethod
    def generate_recommendations(affected_hand, fracture_type, timeout=None):
        """
        Generate treatment recommendations
        
        Args:
            affected_hand (str): Affected hand (left/right)
            fracture_type (str): Type of fracture
            timeout (int): Request timeout in seconds
            
        Returns:
            str: Generated recommendations
        """
        prompt = f"""
        Tell me 3 points of small recommendations in bullet points according to the type of fracture.
        Write only 3 bullet points for the following:
        
        Affected Hand: {affected_hand}
        Fracture Type: {fracture_type}
        """
        
        try:
            return DiagnosisService.generate_gemini_report(prompt, timeout)
        except ValidationError:
            logger.warning("Failed to generate recommendations, returning default")
            return "• Orthopedic consultation recommended\n• Follow-up imaging in 2 weeks\n• Physical therapy pending fracture healing"


class ReportGenerationService:
    """Service for generating medical reports"""
    
    @staticmethod
    def build_html_report(patient_name, patient_id, age, fracture_type, affected_hand, 
                         finding, clinical_report, summary, recommendations):
        """
        Build HTML report from components
        
        Args:
            patient_name (str): Patient name
            patient_id (str): Patient ID/code
            age (int): Patient age
            fracture_type (str): Type of fracture
            affected_hand (str): Affected hand
            finding (str): Imaging findings
            clinical_report (str): Clinical report text
            summary (str): Clinical summary
            recommendations (str): Treatment recommendations
            
        Returns:
            str: HTML report content
        """
        report_html = f"""
        <h2>Comprehensive Medical Diagnostic Report</h2>
        <p><b>Patient Name:</b> {patient_name}</p>
        <p><b>Patient ID:</b> {patient_id}</p>
        <p><b>Age:</b> {age}</p>
        <p><b>Finding:</b> {finding}</p>
        <p><b>Fracture type:</b> {fracture_type}</p>
        <p><b>Hand Affected:</b> {affected_hand}</p>

        <h3>Clinical History & Complaints</h3>
        {clinical_report}

        <h3>Summary</h3>
        {summary}

        <h3>Recommendations</h3>
        {recommendations}
        """
        
        logger.info(f"HTML report generated for patient {patient_id}")
        return report_html
    
    @staticmethod
    def generate_test_results(fracture_type, affected_hand):
        """
        Generate recommended test results based on fracture type
        
        Args:
            fracture_type (str): Type of fracture
            affected_hand (str): Affected hand
            
        Returns:
            list: List of test result dictionaries
        """
        hand_prefix = f"{affected_hand.capitalize()} hand -"
        fracture_lower = fracture_type.lower()
        
        # Default test results
        test_results = [
            {"test": f"X-ray {affected_hand.capitalize()} Wrist", 
             "result": f"{hand_prefix} Fracture confirmed", 
             "remarks": "High resolution imaging"},
        ]
        
        # Add specific tests based on fracture type
        if "boneanomaly" in fracture_lower:
            test_results.extend([
                {"test": "MRI", "result": "Localized bone density variations", 
                 "remarks": "Consider further metabolic evaluation"},
                {"test": "Blood Work", "result": "Elevated alkaline phosphatase", 
                 "remarks": "Check for bone growth disorders"}
            ])
        elif "fracture" in fracture_lower:
            test_results.extend([
                {"test": "CT Scan", "result": "Detailed fracture assessment", 
                 "remarks": "For complex fractures"},
                {"test": "Physical Exam", "result": "Range of motion assessment", 
                 "remarks": "Functional evaluation"}
            ])
        else:
            test_results.extend([
                {"test": "General X-ray", "result": "No clear diagnosis", 
                 "remarks": "Further evaluation recommended"},
                {"test": "Ultrasound", "result": "Soft tissue evaluation", 
                 "remarks": "If applicable"}
            ])
        
        logger.info(f"Test results generated for {fracture_type}")
        return test_results
