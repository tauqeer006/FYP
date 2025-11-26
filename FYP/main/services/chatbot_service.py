"""
Chatbot Service - Route Matching using Google Gemini AI
This service handles user queries and matches them to the appropriate Django routes
using Google Gemini AI with RAG (Retrieval-Augmented Generation)
"""

import yaml
import requests
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatbotService:
    """Service to process user queries and match them to routes using Gemini AI"""
    
    def __init__(self):
        """Initialize the chatbot service with routes data"""
        self.routes_file = Path(__file__).parent.parent / "config" / "routes.yml"
        self.routes_data = None
        self.gemini_api_key = "AIzaSyAw0_LNo3c1dLn0CHh0C0tEbe2-DBmerv8"
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        self.load_routes()
    
    def load_routes(self) -> bool:
        """
        Load and parse routes from YAML file
        Returns: True if successful, False otherwise
        """
        try:
            if not self.routes_file.exists():
                logger.error(f"Routes file not found: {self.routes_file}")
                return False
            
            with open(self.routes_file, 'r') as f:
                self.routes_data = yaml.safe_load(f)
            
            logger.info(f"Successfully loaded routes from {self.routes_file}")
            return True
        except Exception as e:
            logger.error(f"Error loading routes: {str(e)}")
            return False
    
    def format_routes_for_context(self, user_roles: List[str] = None) -> str:
        """
        Format routes data into a readable context for Gemini
        Filters routes based on user roles if provided
        
        Args:
            user_roles: List of user roles to filter routes (e.g., ['admin', 'doctor'])
        
        Returns:
            Formatted string with all available routes
        """
        if not self.routes_data or 'routes' not in self.routes_data:
            return "No routes available"
        
        context = "AVAILABLE ROUTES IN THE APPLICATION:\n"
        context += "=" * 80 + "\n\n"
        
        routes = self.routes_data['routes']
        
        for route_id, route_info in routes.items():
            # Filter by user roles if provided
            if user_roles and 'user_roles' in route_info:
                # Check if any of user's roles can access this route
                if not any(role in route_info['user_roles'] for role in user_roles):
                    continue
            
            context += f"ROUTE ID: {route_id}\n"
            context += f"  Path: {route_info.get('path', 'N/A')}\n"
            context += f"  Description: {route_info.get('description', 'N/A')}\n"
            context += f"  Category: {route_info.get('category', 'N/A')}\n"
            context += f"  Keywords: {', '.join(route_info.get('keywords', []))}\n"
            
            if 'required_auth' in route_info:
                context += f"  Requires Login: {'Yes' if route_info['required_auth'] else 'No'}\n"
            
            context += "\n"
        
        return context
    
    def call_gemini_api(self, user_query: str, routes_context: str) -> Optional[str]:
        """
        Call Google Gemini API to process user query with routes context
        
        Args:
            user_query: The user's natural language query
            routes_context: The formatted routes data as context
        
        Returns:
            Gemini's response text, or None if API call fails
        """
        try:
            # Construct the prompt
            prompt = f"""You are a helpful assistant for a medical diagnostic system. A user has asked you a question.

First, determine if the user wants:
TYPE_A: To navigate to a page (e.g., "go to diagnosis", "show me patients", "main page")
TYPE_B: A general/conversational question (e.g., "hi", "hello", "what's the weather")
TYPE_C: To fill a form on CURRENT page (e.g., "enter username bilal", "add password 12345", "fill email john@test.com")
TYPE_D: To click a button on CURRENT page (e.g., "click login button", "press submit", "click add patient")

{routes_context}

USER REQUEST: "{user_query}"

Your task:
1. Determine if this is TYPE_A, TYPE_B, TYPE_C, or TYPE_D
2. If TYPE_A (navigation):
   TYPE: NAVIGATION
   ROUTE_ID: [route_id]
   PATH: [path]
   REASON: [why you matched this route]

3. If TYPE_B (conversational/general):
   TYPE: CONVERSATION
   ANSWER: [your helpful response]

4. If TYPE_C (form filling on current page):
   Extract ONLY the field values from the user request
   DO NOT include PATH or ROUTE_ID (user is already on the page)
   
   Respond with EXACTLY this format:
   TYPE: FORM_FILL
   FIELDS: {{field_name: value, field_name: value}}
   BUTTON_TO_CLICK: null
   REASON: [what fields user is filling]

5. If TYPE_D (button click on current page):
   Extract the button name/text
   DO NOT include FIELDS, ROUTE_ID, or PATH
   
   Respond with EXACTLY this format:
   TYPE: BUTTON_CLICK
   BUTTON_TO_CLICK: [exact button text]
   REASON: [why user wants to click this button]

IMPORTANT RULES:
- FORM_FILL and BUTTON_CLICK are for CURRENT PAGE ONLY (no navigation, no route info)
- Never include PATH or ROUTE_ID for FORM_FILL or BUTTON_CLICK
- Only include ROUTE_ID and PATH for NAVIGATION requests
- For FORM_FILL: extract field values accurately (username, password, email, etc.)
- For BUTTON_CLICK: identify button text exactly (Login, Submit, Add Patient, etc.)
- Set BUTTON_TO_CLICK to null if user only wants to fill fields without clicking

Example 1 - Form Filling on Current Page:
User: "enter username bilal and password bilal1234"
Response:
TYPE: FORM_FILL
FIELDS: {{"username": "bilal", "password": "bilal1234"}}
BUTTON_TO_CLICK: null
REASON: User filling login form fields on current page

Example 2 - Button Click on Current Page:
User: "click login button"
Response:
TYPE: BUTTON_CLICK
BUTTON_TO_CLICK: Login
REASON: User wants to click login button on current page

Example 3 - Navigation to Different Page:
User: "go to add patient page"
Response:
TYPE: NAVIGATION
ROUTE_ID: add_patient_record
PATH: /add_patient_record/
REASON: User wants to navigate to add patient form"""

            headers = {
                'Content-Type': 'application/json',
            }

            data = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            }

            # Call Gemini API
            response = requests.post(
                f"{self.gemini_url}?key={self.gemini_api_key}",
                headers=headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            gemini_response = result['candidates'][0]['content']['parts'][0]['text']
            
            logger.info(f"Gemini response: {gemini_response}")
            return gemini_response

        except requests.exceptions.Timeout:
            logger.error("Gemini API call timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini API error: {str(e)}")
            return None
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Gemini API call: {str(e)}")
            return None
    
    def parse_gemini_response(self, gemini_response: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[Dict], Optional[str]]:
        """
        Parse Gemini's response to extract response type and relevant data
        
        Args:
            gemini_response: The raw response from Gemini API
        
        Returns:
            Tuple of (response_type, route_id, path, reason, answer, form_fields, button_to_click)
            - For navigation: ('navigation', route_id, path, reason, None, None, None)
            - For conversation: ('conversation', None, None, None, answer, None, None)
            - For form_fill: ('form_fill', None, None, None, None, form_fields_dict, None)
            - For button_click: ('button_click', None, None, None, None, None, button_text)
            - For error: (None, None, None, None, None, None, None)
        """
        try:
            lines = gemini_response.strip().split('\n')
            
            response_type = None
            route_id = None
            path = None
            reason = None
            answer = None
            form_fields = None
            button_to_click = None
            
            for line in lines:
                if line.startswith('TYPE:'):
                    response_type = line.replace('TYPE:', '').strip().lower()
                elif line.startswith('ROUTE_ID:'):
                    route_id = line.replace('ROUTE_ID:', '').strip()
                elif line.startswith('PATH:'):
                    path = line.replace('PATH:', '').strip()
                elif line.startswith('REASON:'):
                    reason = line.replace('REASON:', '').strip()
                elif line.startswith('ANSWER:'):
                    answer = line.replace('ANSWER:', '').strip()
                elif line.startswith('FIELDS:'):
                    fields_str = line.replace('FIELDS:', '').strip()
                    try:
                        form_fields = json.loads(fields_str)
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse FIELDS JSON: {fields_str}")
                        form_fields = None
                elif line.startswith('BUTTON_TO_CLICK:'):
                    button_to_click = line.replace('BUTTON_TO_CLICK:', '').strip()
                    if button_to_click.lower() == 'null' or button_to_click == '':
                        button_to_click = None
            
            if response_type == 'navigation':
                if route_id and path:
                    logger.info(f"Parsed navigation route: {route_id} -> {path}")
                    return response_type, route_id, path, reason, None, None, None
            elif response_type == 'conversation':
                if answer:
                    logger.info(f"Parsed conversation response")
                    return response_type, None, None, None, answer, None, None
            elif response_type == 'form_fill':
                if form_fields:
                    logger.info(f"Parsed form fill with fields: {form_fields}")
                    return response_type, None, None, None, None, form_fields, None
            elif response_type == 'button_click':
                if button_to_click:
                    logger.info(f"Parsed button click: {button_to_click}")
                    return response_type, None, None, None, None, None, button_to_click
            
            logger.warning(f"Could not parse Gemini response properly. Type: {response_type}")
            return None, None, None, None, None, None, None
        
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            return None, None, None, None, None, None, None
    
    def validate_route(self, route_id: str, path: str) -> bool:
        """
        Validate that the extracted route exists in our routes.yml
        
        Args:
            route_id: The route ID from Gemini
            path: The path from Gemini
        
        Returns:
            True if route is valid, False otherwise
        """
        try:
            if not self.routes_data or 'routes' not in self.routes_data:
                return False
            
            routes = self.routes_data['routes']
            
            if route_id not in routes:
                logger.warning(f"Route ID '{route_id}' not found in routes.yml")
                return False
            
            # Verify path matches
            actual_path = routes[route_id].get('path')
            if actual_path != path:
                logger.warning(f"Path mismatch for route {route_id}: {actual_path} != {path}")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error validating route: {str(e)}")
            return False
    
    def get_fallback_route(self) -> Dict:
        """
        Get the homepage fallback route when no good match is found
        
        Returns:
            Route information dictionary
        """
        try:
            if self.routes_data and 'routes' in self.routes_data:
                routes = self.routes_data['routes']
                if 'homepage' in routes:
                    return {
                        'route_id': 'homepage',
                        'path': routes['homepage'].get('path', '/'),
                        'description': routes['homepage'].get('description', 'Home page'),
                        'reason': 'Could not match to a specific route, returning to homepage'
                    }
            
            # Ultimate fallback
            return {
                'route_id': 'homepage',
                'path': '/',
                'description': 'Home page',
                'reason': 'Fallback route'
            }
        except Exception as e:
            logger.error(f"Error getting fallback route: {str(e)}")
            return {
                'route_id': 'homepage',
                'path': '/',
                'description': 'Home page',
                'reason': 'Error occurred'
            }
    
    def get_route_info(self, route_id: str) -> Optional[Dict]:
        """
        Get complete information about a route
        
        Args:
            route_id: The route ID to look up
        
        Returns:
            Dictionary with route information or None
        """
        try:
            if not self.routes_data or 'routes' not in self.routes_data:
                return None
            
            routes = self.routes_data['routes']
            if route_id in routes:
                return routes[route_id]
            
            return None
        except Exception as e:
            logger.error(f"Error getting route info: {str(e)}")
            return None
    
    def process_query(self, user_query: str, user_roles: List[str] = None) -> Dict:
        """
        Main method to process a user query and return either a navigation route or a conversational response
        
        Args:
            user_query: The user's natural language query
            user_roles: List of user roles for filtering (e.g., ['admin', 'doctor'])
        
        Returns:
            Dictionary with:
            For navigation:
            {
                'success': bool,
                'response_type': 'navigation',
                'matched_route': {...route info...},
                'path': '/url/path/',
                'message': 'Human readable message',
                'reason': 'Why this route was matched'
            }
            
            For conversation:
            {
                'success': bool,
                'response_type': 'conversation',
                'answer': 'Bot response text',
                'message': 'Conversational answer'
            }
        """
        try:
            # Validate input
            if not user_query or not isinstance(user_query, str):
                return {
                    'success': False,
                    'response_type': 'conversation',
                    'message': 'Invalid query provided',
                    'answer': 'Sorry, I didn\'t catch that. Could you please rephrase?'
                }
            
            # Ensure routes are loaded
            if not self.routes_data:
                logger.warning("Routes not loaded, attempting to reload...")
                if not self.load_routes():
                    return {
                        'success': False,
                        'response_type': 'conversation',
                        'message': 'System error',
                        'answer': 'I\'m having technical difficulties. Please try again later.'
                    }
            
            # Format routes context
            routes_context = self.format_routes_for_context(user_roles)
            
            # Call Gemini API
            logger.info(f"Processing query: {user_query}")
            gemini_response = self.call_gemini_api(user_query, routes_context)
            
            if not gemini_response:
                logger.warning("Gemini API failed")
                return {
                    'success': False,
                    'response_type': 'conversation',
                    'message': 'API error',
                    'answer': 'I\'m having trouble connecting right now. Could you try again?'
                }
            
            # Parse Gemini response
            response_type, route_id, path, reason, answer, form_fields, button_to_click = self.parse_gemini_response(gemini_response)
            
            # Handle conversation type responses
            if response_type == 'conversation':
                logger.info("Returning conversational response")
                return {
                    'success': True,
                    'response_type': 'conversation',
                    'message': answer,
                    'answer': answer
                }
            
            # Handle button_click type responses
            if response_type == 'button_click':
                logger.info(f"Button click requested: {button_to_click}")
                if not button_to_click:
                    logger.warning("Could not parse button name from Gemini response")
                    return {
                        'success': False,
                        'response_type': 'button_click',
                        'message': 'Could not determine which button to click',
                        'button_to_click': None
                    }
                
                return {
                    'success': True,
                    'response_type': 'button_click',
                    'button_to_click': button_to_click,
                    'message': f"Clicking button: {button_to_click}",
                    'reason': reason or 'User requested button click'
                }
            
            # Handle form_fill type responses
            if response_type == 'form_fill':
                logger.info(f"Form fill requested with fields")
                if not form_fields:
                    logger.warning("Could not parse fields from Gemini response for form fill")
                    return {
                        'success': False,
                        'response_type': 'form_fill',
                        'message': 'Could not determine the form fields to fill',
                        'form_fields': None,
                        'button_to_click': None
                    }
                
                return {
                    'success': True,
                    'response_type': 'form_fill',
                    'form_fields': form_fields,
                    'button_to_click': button_to_click,
                    'message': "Filling form fields on current page",
                    'reason': reason or 'User requested form fill'
                }
            
            # Handle navigation type responses
            if response_type == 'navigation':
                if not route_id or not path:
                    logger.warning("Could not parse route from Gemini response")
                    fallback = self.get_fallback_route()
                    return {
                        'success': False,
                        'response_type': 'navigation',
                        'matched_route': fallback,
                        'path': fallback['path'],
                        'message': 'Could not determine the requested page',
                        'reason': reason or 'Parse error'
                    }
                
                # Validate route exists
                if not self.validate_route(route_id, path):
                    logger.warning(f"Route validation failed for {route_id}")
                    fallback = self.get_fallback_route()
                    return {
                        'success': False,
                        'response_type': 'navigation',
                        'matched_route': fallback,
                        'path': fallback['path'],
                        'message': 'Requested route not found',
                        'reason': f'Route {route_id} not found in system'
                    }
                
                # Get full route info
                matched_route = self.get_route_info(route_id)
                
                return {
                    'success': True,
                    'response_type': 'navigation',
                    'matched_route': matched_route,
                    'path': path,
                    'message': f"Navigating to {matched_route.get('description', 'requested page')}",
                    'reason': reason or 'Query matched successfully'
                }
            
            # If we couldn't determine type, return conversation response
            logger.warning(f"Could not determine response type for query: {user_query}")
            return {
                'success': False,
                'response_type': 'conversation',
                'message': 'Unable to process',
                'answer': 'I didn\'t quite understand that. Try asking about a specific page like "diagnosis" or "patients", or ask me a general question!'
            }
        
        except Exception as e:
            logger.error(f"Unexpected error in process_query: {str(e)}")
            return {
                'success': False,
                'response_type': 'conversation',
                'message': 'An error occurred',
                'answer': 'Oops! Something went wrong. Please try again.'
            }


# Create a singleton instance
_chatbot_service = None

def get_chatbot_service() -> ChatbotService:
    """Get or create the chatbot service singleton"""
    global _chatbot_service
    if _chatbot_service is None:
        _chatbot_service = ChatbotService()
    return _chatbot_service
