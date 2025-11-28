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
        # Load Gemini API key from environment variables
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', '')
        if not self.gemini_api_key:
            logger.warning("⚠️ GEMINI_API_KEY not found in environment variables. Please set it in .env file.")
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
4. Detect when users want to OPEN LINKS in new tabs
5. Detect when users want to CLOSE current tab/browser
6. Respond to general questions conversationally

{routes_context}

CRITICAL INSTRUCTIONS FOR FORM FILLING:
- User says "enter [field] [value]", "fill [field] [value]", "type [field] [value]", "put [field] [value]"
- Examples: "enter username john", "fill password 123", "type email test@example.com"
- Extract the field name and value from what user said
- Look at the route's form_schema to understand available fields
- Return TYPE: FORM_FILL with FIELDS as JSON

CRITICAL INSTRUCTIONS FOR BUTTON CLICKING:
- User says "click [button]", "press [button]", "submit [button]", "click on [button]", "click the [button]"
- Examples: "click login", "press submit", "click next button", "click on the login button", "click the login button"
- Extract JUST the button name/text from what user said
- DO NOT validate against route buttons - the frontend will find any matching button on current page
- Return TYPE: BUTTON_CLICK with BUTTON_TO_CLICK set to the button name/text user mentioned
- The frontend will search for a button matching this text on the current page
- Examples of extraction:
  * "click login button" → BUTTON_TO_CLICK: "login"
  * "click on submit" → BUTTON_TO_CLICK: "submit"
  * "press the next button" → BUTTON_TO_CLICK: "next"
  * "click the login button" → BUTTON_TO_CLICK: "login"

CRITICAL INSTRUCTIONS FOR OPENING LINKS IN NEW TAB:
- User says "open [page] in new tab", "open [page] in a new tab", "open link [url]", "open new tab"
- User says "open this page in new tab", "open current link in new tab"
- Examples: "open patient dashboard in new tab", "open recommendation page in new tab"
- Match keywords from routes list for the page name
- Return TYPE: OPEN_TAB with ROUTE_ID and PATH (same as navigation, but opens in new tab)

CRITICAL INSTRUCTIONS FOR CLOSING TABS OR BROWSER:
- CLOSE TAB: User says "close tab", "close this tab", "close current tab", "close the tab"
  * Return TYPE: CLOSE_TAB (closes only current tab)
- CLOSE BROWSER: User says "close browser", "close complete browser", "close all", "close everything", "quit browser", "exit browser", "close whole browser"
  * Return TYPE: CLOSE_BROWSER (closes entire browser window/application)
- User says "exit", "quit", "close window" → These are ambiguous, default to CLOSE_TAB
- Do NOT ask for clarification - make best guess from keywords

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
Step 1: Check if user wants to CLOSE BROWSER (keywords: "close browser", "close complete", "close whole", "close all", "quit browser", "exit browser")
  - If yes → TYPE: CLOSE_BROWSER
Step 2: Check if user wants to CLOSE TAB (keywords: "close tab", "close current tab", "close this tab")
  - If yes → TYPE: CLOSE_TAB
Step 3: Check if user wants to OPEN in new tab (keywords: "open", "new tab", "open [something] in new tab")
  - If yes → TYPE: OPEN_TAB
Step 4: Check if user is trying to FILL a form (keywords: "enter", "fill", "type", "put", "input")
  - If yes → TYPE: FORM_FILL
Step 5: Check if user is trying to CLICK a button (keywords: "click", "press", "submit", "hit")
  - If yes → TYPE: BUTTON_CLICK
Step 6: Check if user is trying to SCROLL (keywords: "scroll", "page", "down", "up", "top", "bottom")
  - If yes → TYPE: SCROLL
Step 7: Check if user is trying to NAVIGATE (keywords: "go", "navigate", "open", "show", "take me")
  - If yes → TYPE: NAVIGATION
Step 8: Otherwise → TYPE: CONVERSATION

RESPONSE FORMAT (choose ONE):

FOR CLOSING COMPLETE BROWSER:
TYPE: CLOSE_BROWSER
REASON: User wants to close entire browser

FOR CLOSING CURRENT TAB:
TYPE: CLOSE_TAB
REASON: User wants to close current tab

FOR OPENING IN NEW TAB:
TYPE: OPEN_TAB
ROUTE_ID: exact_route_id
PATH: /exact/path/
REASON: User wants to open in new tab

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
5. User: "open patient dashboard in new tab" → TYPE: OPEN_TAB, ROUTE_ID: patient_dashboard, PATH: /Patient_dashboard/
6. User: "open recommendation page in new tab" → TYPE: OPEN_TAB, ROUTE_ID: recommendation, PATH: /recommendation/
7. User: "close tab" → TYPE: CLOSE_TAB
8. User: "close current tab" → TYPE: CLOSE_TAB
9. User: "close browser" → TYPE: CLOSE_BROWSER
10. User: "close complete browser" → TYPE: CLOSE_BROWSER
11. User: "close whole browser" → TYPE: CLOSE_BROWSER
12. User: "scroll down" → TYPE: SCROLL, SCROLL_DIRECTION: down
13. User: "scroll up" → TYPE: SCROLL, SCROLL_DIRECTION: up
14. User: "go to patient dashboard" → TYPE: NAVIGATION, ROUTE_ID: patient_dashboard, PATH: /Patient_dashboard/
15. User: "what is diabetes?" → TYPE: CONVERSATION, ANSWER: explanation

IMPORTANT: 
- For FORM_FILL: Return the extracted field names and values as JSON
- For BUTTON_CLICK: Return the exact button text you want clicked
- For OPEN_TAB: Return route_id and path (same as navigation but with OPEN_TAB type)
- For CLOSE_TAB: Return just the type (no other parameters needed)
- For CLOSE_BROWSER: Return just the type (no other parameters needed)
- For SCROLL: Return "up" or "down" as SCROLL_DIRECTION
- For NAVIGATION: Use exact route IDs and paths from the routes list
- CLOSE_BROWSER closes entire browser/application, CLOSE_TAB only closes current tab
- Do NOT confuse form filling with navigation - if user is filling a form on current page, return FORM_FILL, not NAVIGATION
- Do NOT confuse scrolling with navigation - if user says "scroll down", return SCROLL, not NAVIGATION
- Do NOT confuse OPEN_TAB with NAVIGATION - OPEN_TAB opens in new tab, NAVIGATION replaces current page
- Do NOT confuse CLOSE_BROWSER with CLOSE_TAB - CLOSE_BROWSER closes entire browser, CLOSE_TAB closes current tab only"""

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
    
    def process_multi_commands(self, commands: List[str], user_roles: List[str] = None) -> Dict:
        """
        Process multiple commands sequentially and return results for each
        
        Args:
            commands: List of individual commands to process
            user_roles: List of user roles for filtering
        
        Returns:
            Dictionary with multi_command response containing results for each command
        """
        logger.info(f"Processing {len(commands)} commands: {commands}")
        
        # Ensure routes are loaded
        if not self.routes_data:
            if not self.load_routes():
                return {
                    'success': False,
                    'response_type': 'conversation',
                    'message': 'System error',
                    'answer': 'I\'m having technical difficulties. Please try again later.'
                }
        
        processed_commands = []
        routes_context = self.format_routes_for_context(user_roles)
        
        for idx, command in enumerate(commands, 1):
            logger.info(f"Processing command {idx}/{len(commands)}: {command}")
            
            # Call Gemini API for each command
            gemini_response = self.call_gemini_api(command, routes_context)
            
            if not gemini_response:
                logger.warning(f"Gemini API failed for command {idx}: {command}")
                processed_commands.append({
                    'command_index': idx,
                    'command': command,
                    'success': False,
                    'response_type': 'conversation',
                    'message': 'Could not process this command',
                    'answer': f'I had trouble processing: "{command}"'
                })
                continue
            
            # Parse Gemini response
            response_type, route_id, path, reason, answer, form_fields, button_to_click, scroll_direction = self.parse_gemini_response(gemini_response)
            
            # Build response based on type
            command_response = {
                'command_index': idx,
                'command': command,
                'response_type': response_type,
                'success': True if response_type else False
            }
            
            if response_type == 'conversation':
                command_response.update({
                    'success': True,  # ← Conversation responses are successful (informational)
                    'message': answer,
                    'answer': answer
                })
            
            elif response_type == 'scroll':
                if scroll_direction not in ['up', 'down']:
                    command_response.update({
                        'success': False,
                        'message': 'Could not determine scroll direction'
                    })
                else:
                    command_response.update({
                        'scroll_direction': scroll_direction,
                        'message': f"Scrolling page {scroll_direction}"
                    })
            
            elif response_type == 'button_click':
                if not button_to_click:
                    command_response.update({
                        'success': False,
                        'message': 'Could not determine which button to click'
                    })
                else:
                    command_response.update({
                        'success': True,  # ← Button clicks are successful (frontend will find and click)
                        'button_to_click': button_to_click,
                        'message': f"Clicking button: {button_to_click}"
                    })
            
            elif response_type == 'form_fill':
                if not form_fields:
                    command_response.update({
                        'success': False,
                        'message': 'Could not determine the form fields to fill'
                    })
                else:
                    command_response.update({
                        'form_fields': form_fields,
                        'button_to_click': button_to_click,
                        'message': "Filling form fields on current page"
                    })
            
            elif response_type == 'navigation':
                if not route_id or not path:
                    command_response.update({
                        'success': False,
                        'message': 'Could not determine the requested page'
                    })
                elif not self.validate_route(route_id, path):
                    command_response.update({
                        'success': False,
                        'message': f'Route not found: {route_id}'
                    })
                else:
                    matched_route = self.get_route_info(route_id)
                    command_response.update({
                        'success': True,  # ← FIXED: Set success to True for valid navigation
                        'matched_route': matched_route,
                        'path': path,
                        'message': f"Navigating to {matched_route.get('description', 'requested page')}"
                    })
            
            else:
                command_response.update({
                    'success': False,
                    'message': 'Could not determine action for this command'
                })
            
            processed_commands.append(command_response)
        
        # Calculate success rate
        successful = sum(1 for cmd in processed_commands if cmd.get('success', False))
        
        return {
            'success': successful > 0,
            'response_type': 'multi_command',
            'commands': processed_commands,
            'message': f"Processed {len(commands)} commands ({successful}/{len(commands)} successful)",
            'total_commands': len(commands),
            'successful_commands': successful
        }
    
    def split_multi_commands(self, user_query: str) -> List[str]:
        """
        Split a single voice input into multiple commands
        
        Detects separators like: "then", "and", "next", "after that", "also"
        Examples:
            "scroll down then login" → ["scroll down", "login"]
            "enter name tauqeer and click login" → ["enter name tauqeer", "click login"]
            "fill email test@test.com then enter password 123" → ["fill email test@test.com", "enter password 123"]
        
        Args:
            user_query: The full voice input
        
        Returns:
            List of individual commands
        """
        import re
        
        # List of separators used to split commands (case-insensitive)
        separators = [
            r'\bthen\b',
            r'\band\b',
            r'\bnext\b',
            r'\bafter\s+that\b',
            r'\balso\b',
            r'\bfinally\b',
            r'\bthen\s+(?!I)',  # "then" but not "then I" (which is conversational)
            r',',  # Comma as separator
        ]
        
        # Create regex pattern for all separators
        separator_pattern = '|'.join(separators)
        
        # Split by separators, keeping track of what's removed
        commands = re.split(separator_pattern, user_query, flags=re.IGNORECASE)
        
        # Clean up: strip whitespace and remove empty strings
        commands = [cmd.strip() for cmd in commands if cmd and cmd.strip()]
        
        return commands if len(commands) > 1 else [user_query]
    
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
            
            For multi_command:
            {
                'success': bool,
                'response_type': 'multi_command',
                'commands': [
                    {response for command 1},
                    {response for command 2},
                    ...
                ],
                'message': 'Processing multiple commands',
                'total_commands': 3
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
            
            # Check if this is a multi-command request
            commands = self.split_multi_commands(user_query)
            
            # If multiple commands detected, process each one
            if len(commands) > 1:
                logger.info(f"Multi-command detected: {len(commands)} commands")
                return self.process_multi_commands(commands, user_roles)
            
            # Single command processing - continue with existing logic
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
