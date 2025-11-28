"""
Authentication service module.
Handles user authentication, password reset, and security validations.
"""

import logging
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from main.validators import validate_username, validate_password, validate_email

logger = logging.getLogger(__name__)
User = get_user_model()


class AuthenticationService:
    """Service for handling user authentication operations"""
    
    @staticmethod
    def authenticate_user(username, password, user_type=None):
        """
        Authenticate a user with username and password
        
        Args:
            username (str): Username
            password (str): Password
            user_type (str): Optional user type filter ('admin', 'doctor', 'patient')
            
        Returns:
            User object if authentication successful, None otherwise
        """
        try:
            # Validate inputs
            if not username or not password:
                logger.warning("Authentication attempt with empty credentials")
                return None
            
            # Authenticate using Django's built-in authentication
            user = authenticate(username=username, password=password)
            
            if user is None:
                logger.warning(f"Failed authentication for user: {username}")
                return None
            
            # Check user type if specified
            if user_type and hasattr(user, 'user_type'):
                if user.user_type != user_type:
                    logger.warning(f"User {username} attempted login with invalid user_type {user_type}")
                    return None
            
            logger.info(f"User {username} authenticated successfully")
            return user
            
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return None
    
    @staticmethod
    def create_user(username, email, password, user_type='doctor'):
        """
        Create a new user account
        
        Args:
            username (str): Username
            email (str): Email address
            password (str): Password
            user_type (str): User type ('admin', 'doctor', 'patient')
            
        Returns:
            User object if creation successful, raises ValidationError otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate inputs
            username = validate_username(username)
            email = validate_email(email)
            password = validate_password(password)
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                raise ValidationError(f"Username '{username}' is already taken")
            
            if User.objects.filter(email=email).exists():
                raise ValidationError(f"Email '{email}' is already registered")
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                user_type=user_type
            )
            
            logger.info(f"New user created: {username} (type: {user_type})")
            return user
            
        except ValidationError as e:
            logger.warning(f"User creation validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise ValidationError(f"Failed to create user: {str(e)}")
    
    @staticmethod
    def generate_password_reset_token(user):
        """
        Generate a password reset token for a user
        
        Args:
            user: User object
            
        Returns:
            str: Encoded token
        """
        try:
            token = default_token_generator.make_token(user)
            logger.info(f"Password reset token generated for user: {user.username}")
            return token
        except Exception as e:
            logger.error(f"Error generating password reset token: {e}")
            return None
    
    @staticmethod
    def verify_reset_token(user, token):
        """
        Verify a password reset token
        
        Args:
            user: User object
            token (str): Token to verify
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        is_valid = default_token_generator.check_token(user, token)
        if not is_valid:
            logger.warning(f"Invalid password reset token for user: {user.username}")
        return is_valid
    
    @staticmethod
    def reset_password(user, new_password):
        """
        Reset user password
        
        Args:
            user: User object
            new_password (str): New password
            
        Returns:
            bool: True if password reset successful, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate new password
            new_password = validate_password(new_password)
            
            # Set new password
            user.set_password(new_password)
            user.save()
            
            logger.info(f"Password reset for user: {user.username}")
            return True
            
        except ValidationError as e:
            logger.warning(f"Password reset validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            return False


class PasswordResetService:
    """Service for handling password reset flows"""
    
    @staticmethod
    def send_reset_email(user, request):
        """
        Send password reset email to user
        
        Args:
            user: User object
            request: Django request object
            
        Returns:
            bool: True if email sent successfully
        """
        from django.core.mail import send_mail
        from django.conf import settings
        
        try:
            # Generate token
            token = AuthenticationService.generate_password_reset_token(user)
            
            # Create reset link
            reset_link = f"{request.build_absolute_uri('/api/password-reset/verify/')}?token={token}&user={user.id}"
            
            # Send email
            subject = "Password Reset Request"
            message = f"""
Hello {user.username},

You requested to reset your password. Click the link below to proceed:

{reset_link}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
FYP Medical System
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            logger.info(f"Password reset email sent to: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")
            return False
