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
        self.gemini_api_key = "AIzaSyB7fwNrYMa4T05ilokA3YQwjasZcwYRG5Y"
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
            Formatted string with all available routes, form schemas, and buttons
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
            
            # Include form_schema information for form filling
            if 'form_schema' in route_info and route_info['form_schema']:
                form_schema = route_info['form_schema']
                if 'fields' in form_schema:
                    context += "  FORM FIELDS (for voice form filling):\n"
                    for field in form_schema['fields']:
                        context += f"    - {field.get('name', 'N/A')}: {field.get('label', 'N/A')} ({field.get('type', 'text')})\n"
            
            # Include buttons information for button clicking
            if 'buttons' in route_info and route_info['buttons']:
                context += "  BUTTONS (for voice button clicking):\n"
                for button in route_info['buttons']:
                    button_text = button.get('text', button.get('name', 'N/A'))
                    context += f"    - {button_text}\n"
            
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
            prompt = f"""You are an intelligent assistant for a medical diagnostic system. Your job is to:
1. Match user navigation requests to routes using keywords
2. Detect when users want to FILL FORM FIELDS
3. Detect when users want to CLICK BUTTONS
4. Respond to general questions conversationally

{routes_context}

CRITICAL INSTRUCTIONS FOR FORM FILLING:
- User says "enter [field] [value]", "fill [field] [value]", "type [field] [value]", "put [field] [value]"
- Examples: "enter username john", "fill password 123", "type email test@example.com"
- Extract the field name and value from what user said
- Look at the route's form_schema to understand available fields
- Return TYPE: FORM_FILL with FIELDS as JSON

CRITICAL INSTRUCTIONS FOR BUTTON CLICKING:
- User says "click [button]", "press [button]", "submit [button]", "click on [button]"
- Examples: "click login", "press submit", "click next button"
- Extract the button name from what user said
- Look at the route's buttons array to match button names
- Return TYPE: BUTTON_CLICK with BUTTON_TO_CLICK

CRITICAL INSTRUCTIONS FOR PAGE SCROLLING:
- User says "scroll down", "scroll up", "scroll", "page down", "page up"
- Examples: "scroll down", "scroll up", "go down", "go up", "back to top"
- Detect keywords: "scroll", "page", "down", "up", "top", "bottom"
- Return TYPE: SCROLL with SCROLL_DIRECTION (up or down)
- Do NOT navigate to a different page - just scroll the current page

CRITICAL INSTRUCTIONS FOR NAVIGATION:
- User asks to "go to", "navigate to", "open", "show me" a page
- Match keywords from the routes list
- Return TYPE: NAVIGATION with ROUTE_ID and PATH

USER REQUEST: "{user_query}"

DETECTION LOGIC:
Step 1: Check if user is trying to FILL a form (keywords: "enter", "fill", "type", "put", "input")
  - If yes → TYPE: FORM_FILL
Step 2: Check if user is trying to CLICK a button (keywords: "click", "press", "submit", "hit")
  - If yes → TYPE: BUTTON_CLICK
Step 3: Check if user is trying to SCROLL (keywords: "scroll", "page", "down", "up", "top", "bottom")
  - If yes → TYPE: SCROLL
Step 4: Check if user is trying to NAVIGATE (keywords: "go", "navigate", "open", "show", "take me")
  - If yes → TYPE: NAVIGATION
Step 5: Otherwise → TYPE: CONVERSATION

RESPONSE FORMAT (choose ONE):

FOR FORM FILLING (user wants to enter data on current page):
TYPE: FORM_FILL
FIELDS: {{"field_name": "value", "another_field": "another_value"}}
BUTTON_TO_CLICK: "Submit" or null
REASON: User wants to fill form fields

FOR BUTTON CLICKING (user wants to click a button on current page):
TYPE: BUTTON_CLICK
BUTTON_TO_CLICK: exact button text to click
REASON: User wants to click a button

FOR PAGE SCROLLING (user wants to scroll the page):
TYPE: SCROLL
SCROLL_DIRECTION: up or down
REASON: User wants to scroll the page

FOR NAVIGATION (user wants to go to a different page):
TYPE: NAVIGATION
ROUTE_ID: exact_route_id
PATH: /exact/path/
REASON: Keywords matched: list which keywords matched

FOR CONVERSATION (user asking a general question):
TYPE: CONVERSATION
ANSWER: helpful response about the question

EXAMPLES:
1. User: "enter username john password 123" → TYPE: FORM_FILL, FIELDS: {{"username": "john", "password": "123"}}
2. User: "fill email test@test.com" → TYPE: FORM_FILL, FIELDS: {{"email": "test@test.com"}}
3. User: "click login button" → TYPE: BUTTON_CLICK, BUTTON_TO_CLICK: "Login"
4. User: "press submit" → TYPE: BUTTON_CLICK, BUTTON_TO_CLICK: "Submit"
5. User: "scroll down" → TYPE: SCROLL, SCROLL_DIRECTION: down
6. User: "scroll up" → TYPE: SCROLL, SCROLL_DIRECTION: up
7. User: "go to patient dashboard" → TYPE: NAVIGATION, ROUTE_ID: patient_dashboard, PATH: /Patient_dashboard/
8. User: "what is diabetes?" → TYPE: CONVERSATION, ANSWER: explanation

IMPORTANT: 
- For FORM_FILL: Return the extracted field names and values as JSON
- For BUTTON_CLICK: Return the exact button text you want clicked
- For SCROLL: Return "up" or "down" as SCROLL_DIRECTION
- For NAVIGATION: Use exact route IDs and paths from the routes list
- Do NOT confuse form filling with navigation - if user is filling a form on current page, return FORM_FILL, not NAVIGATION
- Do NOT confuse scrolling with navigation - if user says "scroll down", return SCROLL, not NAVIGATION"""

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
    
    def parse_gemini_response(self, gemini_response: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[Dict], Optional[str], Optional[str]]:
        """
        Parse Gemini's response to extract response type and relevant data
        
        Args:
            gemini_response: The raw response from Gemini API
        
        Returns:
            Tuple of (response_type, route_id, path, reason, answer, form_fields, button_to_click, scroll_direction)
            - For navigation: ('navigation', route_id, path, reason, None, None, None, None)
            - For conversation: ('conversation', None, None, None, answer, None, None, None)
            - For form_fill: ('form_fill', None, None, None, None, form_fields_dict, None, None)
            - For button_click: ('button_click', None, None, None, None, None, button_text, None)
            - For scroll: ('scroll', None, None, None, None, None, None, scroll_direction)
            - For error: (None, None, None, None, None, None, None, None)
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
            scroll_direction = None
            
            for line in lines:
                if line.startswith('TYPE:'):
                    response_type = line.replace('TYPE:', '').strip().lower()
                elif line.startswith('SCROLL_DIRECTION:'):
                    scroll_direction = line.replace('SCROLL_DIRECTION:', '').strip().lower()
                    if scroll_direction not in ['up', 'down']:
                        scroll_direction = None
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
                    return response_type, route_id, path, reason, None, None, None, None
            elif response_type == 'conversation':
                if answer:
                    logger.info(f"Parsed conversation response")
                    return response_type, None, None, None, answer, None, None, None
            elif response_type == 'form_fill':
                if form_fields:
                    logger.info(f"Parsed form fill with fields: {form_fields}")
                    return response_type, None, None, None, None, form_fields, None, None
            elif response_type == 'button_click':
                if button_to_click:
                    logger.info(f"Parsed button click: {button_to_click}")
                    return response_type, None, None, None, None, None, button_to_click, None
            elif response_type == 'scroll':
                if scroll_direction:
                    logger.info(f"Parsed scroll: {scroll_direction}")
                    return response_type, None, None, None, None, None, None, scroll_direction
            
            logger.warning(f"Could not parse Gemini response properly. Type: {response_type}")
            return None, None, None, None, None, None, None, None
        
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            return None, None, None, None, None, None, None, None
    
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
            response_type, route_id, path, reason, answer, form_fields, button_to_click, scroll_direction = self.parse_gemini_response(gemini_response)
            
            # Handle conversation type responses
            if response_type == 'conversation':
                logger.info("Returning conversational response")
                return {
                    'success': True,
                    'response_type': 'conversation',
                    'message': answer,
                    'answer': answer
                }
            
            # Handle scroll type responses
            if response_type == 'scroll':
                logger.info(f"Scroll requested: {scroll_direction}")
                if not scroll_direction or scroll_direction not in ['up', 'down']:
                    logger.warning("Could not parse scroll direction from Gemini response")
                    return {
                        'success': False,
                        'response_type': 'scroll',
                        'message': 'Could not determine scroll direction',
                        'scroll_direction': None
                    }
                
                return {
                    'success': True,
                    'response_type': 'scroll',
                    'scroll_direction': scroll_direction,
                    'message': f"Scrolling page {scroll_direction}",
                    'reason': reason or 'User requested scroll'
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
