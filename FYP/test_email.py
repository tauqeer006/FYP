#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FYP.settings')
django.setup()

from django.core.mail import send_mail

try:
    result = send_mail(
        'Test Email - Password Reset',
        'This is a test email from the FYP system. If you received this, email configuration is working!',
        'tauqeerqureshi112@gmail.com',
        ['tauqeerqureshi112@gmail.com'],
        fail_silently=False
    )
    print(f"✅ Email sent successfully! Messages sent: {result}")
except Exception as e:
    print(f"❌ Error sending email: {e}")
    print(f"Error type: {type(e).__name__}")
