"""
Input validation module for FYP application.
Provides validation functions for user inputs, form data, and API requests.
"""

import re
import logging
from django.core.exceptions import ValidationError
from django.utils.text import slugify

logger = logging.getLogger(__name__)


# ==================== USER INPUT VALIDATORS ====================

def validate_username(username):
    """
    Validate username format
    
    Rules:
    - Length: 3-100 characters
    - Alphanumeric and underscores only
    - Cannot start with number
    
    Args:
        username (str): Username to validate
        
    Raises:
        ValidationError: If username is invalid
    """
    if not username:
        raise ValidationError("Username cannot be empty")
    
    username = username.strip()
    
    if len(username) < 3:
        raise ValidationError("Username must be at least 3 characters long")
    
    if len(username) > 100:
        raise ValidationError("Username must be at most 100 characters long")
    
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', username):
        raise ValidationError("Username can only contain letters, numbers, and underscores. Must start with letter or underscore.")
    
    return username.strip()


def validate_email(email):
    """
    Validate email format
    
    Args:
        email (str): Email to validate
        
    Raises:
        ValidationError: If email is invalid
    """
    if not email:
        raise ValidationError("Email cannot be empty")
    
    email = email.strip().lower()
    
    # RFC 5322 simplified pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError("Invalid email format")
    
    if len(email) > 254:
        raise ValidationError("Email is too long (max 254 characters)")
    
    return email


def validate_password(password):
    """
    Validate password strength
    
    Rules:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    
    Args:
        password (str): Password to validate
        
    Raises:
        ValidationError: If password doesn't meet requirements
    """
    if not password:
        raise ValidationError("Password cannot be empty")
    
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    
    if len(password) > 128:
        raise ValidationError("Password must be at most 128 characters long")
    
    if not any(c.isupper() for c in password):
        raise ValidationError("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        raise ValidationError("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        raise ValidationError("Password must contain at least one digit")
    
    return password


def validate_phone_number(phone):
    """
    Validate phone number format
    
    Accepts:
    - 10-15 digits
    - Optional +/country code
    - Spaces and hyphens
    
    Args:
        phone (str): Phone number to validate
        
    Raises:
        ValidationError: If phone is invalid
    """
    if not phone:
        raise ValidationError("Phone number cannot be empty")
    
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone)
    
    if not re.match(r'^\+?[1-9]\d{9,14}$', cleaned):
        raise ValidationError("Invalid phone number format. Use format like: +1234567890 or 123-456-7890")
    
    return phone.strip()


# ==================== FILE VALIDATORS ====================

def validate_image_file(file_obj, max_size_mb=10):
    """
    Validate image file upload
    
    Args:
        file_obj: File object from request.FILES
        max_size_mb (int): Maximum file size in MB
        
    Raises:
        ValidationError: If file is invalid
    """
    if not file_obj:
        raise ValidationError("No file provided")
    
    # Check file size (convert MB to bytes)
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_obj.size > max_size_bytes:
        raise ValidationError(f"File is too large. Maximum size is {max_size_mb}MB")
    
    # Check file type
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
    file_ext = file_obj.name.split('.')[-1].lower()
    
    if file_ext not in allowed_extensions:
        raise ValidationError(f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")
    
    # Check MIME type
    if not file_obj.content_type.startswith('image/'):
        raise ValidationError("File must be an image")
    
    return file_obj


# ==================== DATA VALIDATORS ====================

def validate_voice_query(query):
    """
    Validate voice command input
    
    Rules:
    - Length: 1-500 characters
    - No SQL injection patterns
    - Basic profanity check (optional)
    
    Args:
        query (str): Voice query to validate
        
    Raises:
        ValidationError: If query is invalid
    """
    if not query:
        raise ValidationError("Query cannot be empty")
    
    query = query.strip()
    
    if len(query) < 1:
        raise ValidationError("Query must contain at least 1 character")
    
    if len(query) > 500:
        raise ValidationError("Query is too long (maximum 500 characters)")
    
    # Check for potential SQL injection patterns
    sql_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'SELECT', 'UNION', '--', ';']
    query_upper = query.upper()
    
    for keyword in sql_keywords:
        if keyword in query_upper:
            logger.warning(f"Suspicious query pattern detected: {keyword}")
            raise ValidationError("Invalid query format")
    
    return query


def validate_patient_data(fname, lname, age, gender, contact):
    """
    Validate patient creation/update data
    
    Args:
        fname (str): First name
        lname (str): Last name
        age (int): Age
        gender (str): Gender (M/F/O)
        contact (str): Contact number
        
    Raises:
        ValidationError: If any field is invalid
    """
    # Validate names
    if not fname or not fname.strip():
        raise ValidationError("First name cannot be empty")
    
    if not lname or not lname.strip():
        raise ValidationError("Last name cannot be empty")
    
    if len(fname) > 100:
        raise ValidationError("First name is too long")
    
    if len(lname) > 100:
        raise ValidationError("Last name is too long")
    
    # Validate age
    try:
        age_int = int(age)
        if age_int < 0 or age_int > 150:
            raise ValidationError("Age must be between 0 and 150")
    except (ValueError, TypeError):
        raise ValidationError("Age must be a valid number")
    
    # Validate gender
    if gender not in ['M', 'F', 'O']:
        raise ValidationError("Gender must be M, F, or O")
    
    # Validate contact
    validate_phone_number(contact)
    
    return {
        'fname': fname.strip(),
        'lname': lname.strip(),
        'age': age_int,
        'gender': gender,
        'contact': contact.strip()
    }


def validate_xray_data(fracture_type, affected_hand, finding):
    """
    Validate X-ray record data
    
    Args:
        fracture_type (str): Type of fracture detected
        affected_hand (str): Affected hand (left/right)
        finding (str): Medical finding description
        
    Raises:
        ValidationError: If any field is invalid
    """
    if not fracture_type or not fracture_type.strip():
        raise ValidationError("Fracture type cannot be empty")
    
    if len(fracture_type) > 100:
        raise ValidationError("Fracture type is too long")
    
    if affected_hand not in ['left', 'right']:
        raise ValidationError("Affected hand must be 'left' or 'right'")
    
    if not finding or not finding.strip():
        raise ValidationError("Finding description cannot be empty")
    
    if len(finding) > 2000:
        raise ValidationError("Finding description is too long")
    
    return {
        'fracture_type': fracture_type.strip(),
        'affected_hand': affected_hand.lower(),
        'finding': finding.strip()
    }


# ==================== UTILITY VALIDATORS ====================

def sanitize_string(text, max_length=None, allow_special=False):
    """
    Sanitize user input string
    
    Args:
        text (str): Text to sanitize
        max_length (int): Maximum length (optional)
        allow_special (bool): Allow special characters
        
    Returns:
        str: Sanitized text
    """
    if not text:
        return ""
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    if not allow_special:
        # Remove potentially dangerous characters
        text = re.sub(r'[<>\"\'%;()&+]', '', text)
    
    return text


def validate_request_data(data, required_fields):
    """
    Validate that request data contains all required fields
    
    Args:
        data (dict): Request data
        required_fields (list): List of required field names
        
    Raises:
        ValidationError: If required fields are missing
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    return True
