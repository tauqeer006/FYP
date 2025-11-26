#!/usr/bin/env python
"""
Email Configuration Diagnostic Script
This script checks if email sending is properly configured in Django
"""
import os
import sys
import django

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FYP.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail, get_connection
from django.core.exceptions import ImproperlyConfigured

print("=" * 60)
print("EMAIL CONFIGURATION DIAGNOSTIC")
print("=" * 60)

# Check email settings
print("\n1. EMAIL BACKEND CONFIGURATION:")
print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

# Test connection
print("\n2. TESTING EMAIL CONNECTION:")
try:
    connection = get_connection()
    connection.open()
    connection.close()
    print("   ✅ Connection to SMTP server successful!")
except Exception as e:
    print(f"   ❌ Connection failed: {e}")
    print(f"   Error type: {type(e).__name__}")

# Test sending email
print("\n3. TESTING EMAIL SEND:")
try:
    result = send_mail(
        'Test Email - X-Ai Password Reset System',
        'This is a test email from the X-Ai Medical Center password reset system.\n\nIf you received this, email configuration is working correctly.',
        'tauqeerqureshi112@gmail.com',
        ['tauqeerqureshi112@gmail.com'],
        fail_silently=False
    )
    print(f"   ✅ Test email sent successfully!")
    print(f"   Messages sent: {result}")
except Exception as e:
    print(f"   ❌ Email send failed: {e}")
    print(f"   Error type: {type(e).__name__}")
    
    # Try to provide helpful suggestions
    error_msg = str(e).lower()
    if 'authentication' in error_msg or 'login' in error_msg:
        print("\n   💡 SUGGESTION: Check your EMAIL_HOST_PASSWORD")
        print("      - Gmail users: Use an App Password, not your regular password")
        print("      - Visit: https://myaccount.google.com/apppasswords")
    elif 'connection' in error_msg or 'timeout' in error_msg:
        print("\n   💡 SUGGESTION: Check your internet connection")
        print("      - Verify EMAIL_HOST and EMAIL_PORT are correct")
    elif 'certificate' in error_msg:
        print("\n   💡 SUGGESTION: SSL/TLS certificate issue")
        print("      - Try disabling EMAIL_USE_TLS if not required")

print("\n" + "=" * 60)
