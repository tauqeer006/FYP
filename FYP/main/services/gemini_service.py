"""
Unified Gemini API Service using google.generativeai library
This service provides centralized access to Google Gemini API for all modules
"""

import google.generativeai as genai
import logging
import os
from typing import Optional
from django.conf import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiService:
    """
    Unified service for Google Gemini API using the official library.
    Handles model initialization, availability checking, and API calls.
    """
    
    def __init__(self):
        """Initialize Gemini service with API key and model"""
        self.api_key = os.getenv('GEMINI_API_KEY', '') or getattr(settings, 'GEMINI_API_KEY', '')
        
        if not self.api_key:
            logger.error("❌ GEMINI_API_KEY not found in environment variables or settings")
            raise ValueError("GEMINI_API_KEY is required but not configured")
        
        # Configure the API key
        genai.configure(api_key=self.api_key)
        logger.info("✓ Gemini API configured successfully")
        
        # Initialize the model
        self.model = self._initialize_model()
    
    def _initialize_model(self):
        """
        Get the first available generative model that supports generateContent.
        Falls back to a specific model if no available model is found.
        
        Returns:
            GenerativeModel: The initialized Gemini model
        
        Raises:
            Exception: If no available generative model found and fallback fails
        """
        try:
            # Try to list available models
            available_models = genai.list_models()
            model_name = None
            
            for m in available_models:
                if 'generateContent' in m.supported_generation_methods:
                    model_name = m.name
                    logger.info(f"✓ Found available model: {model_name}")
                    break
            
            if not model_name:
                # Fallback to a known working model
                logger.warning("⚠️ No available model found in list, using fallback: gemini-2.0-flash")
                model_name = 'gemini-2.0-flash'
            
            # Initialize and return the model
            model = genai.GenerativeModel(model_name)
            logger.info(f"✓ Gemini model initialized: {model_name}")
            return model
            
        except Exception as e:
            logger.error(f"❌ Error initializing Gemini model: {str(e)}")
            # Try fallback model
            try:
                logger.info("⚠️ Attempting fallback model initialization...")
                model = genai.GenerativeModel('gemini-2.0-flash')
                logger.info("✓ Fallback model (gemini-2.0-flash) initialized successfully")
                return model
            except Exception as fallback_error:
                logger.error(f"❌ Fallback model also failed: {str(fallback_error)}")
                raise Exception(f"Unable to initialize any Gemini model: {str(e)}")
    
    def get_response(self, user_input: str, max_retries: int = 3) -> Optional[str]:
        """
        Send user input to Gemini and get response with retry logic.
        
        Args:
            user_input (str): The input message to send to Gemini
            max_retries (int): Maximum number of retries on failure (default: 3)
        
        Returns:
            str: The response text from Gemini, or None if all retries fail
        """
        if not user_input or not isinstance(user_input, str):
            logger.warning("⚠️ Invalid user input provided to get_response")
            return None
        
        base_delay = 1  # Start with 1 second delay
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"📤 Sending request to Gemini (attempt {attempt + 1}/{max_retries + 1})")
                response = self.model.generate_content(user_input)
                
                if response and response.text:
                    logger.info(f"✓ Received response from Gemini (attempt {attempt + 1})")
                    return response.text
                else:
                    logger.warning(f"⚠️ Empty response from Gemini (attempt {attempt + 1})")
                    return None
                    
            except Exception as e:
                error_str = str(e)
                logger.error(f"❌ Gemini API error (attempt {attempt + 1}): {error_str}")
                
                # Check if it's a rate limit error (429)
                if "429" in error_str or "too many requests" in error_str.lower():
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"⚠️ Rate limited. Waiting {delay} seconds before retry...")
                        import time
                        time.sleep(delay)
                        continue
                    else:
                        logger.error("❌ Max retries exceeded. Rate limit still active.")
                        return None
                
                # For other errors, don't retry
                logger.error(f"❌ Non-recoverable error: {error_str}")
                return None
        
        return None
    
    def generate_report(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """
        Generate a medical report or other structured response using Gemini.
        
        Args:
            prompt (str): The prompt for report generation
            max_retries (int): Maximum number of retries (default: 3)
        
        Returns:
            str: Generated report text, or None if generation fails
        """
        return self.get_response(prompt, max_retries)


# Global instance (lazy initialization)
_gemini_service_instance = None


def get_gemini_service() -> GeminiService:
    """
    Get or create a global Gemini service instance.
    Uses lazy initialization to avoid errors if API key is not set early.
    
    Returns:
        GeminiService: The global Gemini service instance
    
    Raises:
        ValueError: If GEMINI_API_KEY is not configured
    """
    global _gemini_service_instance
    
    if _gemini_service_instance is None:
        try:
            _gemini_service_instance = GeminiService()
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini service: {str(e)}")
            raise
    
    return _gemini_service_instance
