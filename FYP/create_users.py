#!/usr/bin/env python
"""
Script to create test users in the database
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FYP.settings')
django.setup()

from main.models import User, Admin, Doctor

# Create Admin user
admin_user = User.objects.create_user(
    username='tauqeer',
    email='tauqeerqureshi112@gmail.com',
    password='tauqeer056',
    user_type='admin'
)
admin_user.is_staff = True
admin_user.is_superuser = True
admin_user.is_active = True
admin_user.save()
print(f"✓ Created admin user: {admin_user.username}")

# Create Doctor user
doctor_user = User.objects.create_user(
    username='bilal112233',
    email='bilal@example.com',
    password='123',
    user_type='doctor'
)
doctor_user.is_active = True
doctor_user.save()
# Create Doctor profile
Doctor.objects.create(
    user=doctor_user,
    specialization='Orthopedics'
)
print(f"✓ Created doctor user: {doctor_user.username}")

# Create Patient user
patient_user = User.objects.create_user(
    username='sameer34',
    email='sameer@example.com',
    password='1234',
    user_type='patient'
)
patient_user.is_active = True
patient_user.save()
print(f"✓ Created patient user: {patient_user.username}")

print("\n✓ All users created successfully!")
