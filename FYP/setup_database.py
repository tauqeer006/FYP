#!/usr/bin/env python
"""
Database Migration Setup Script
Run this after code changes to apply database migrations
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FYP.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.core.management import call_command

print("=" * 80)
print("FYP Database Migration Setup")
print("=" * 80)

# Step 1: Create migrations
print("\n[Step 1] Creating migrations...")
try:
    call_command('makemigrations', 'main', verbosity=2)
    print("✓ Migrations created successfully")
except Exception as e:
    print(f"✗ Error creating migrations: {e}")
    sys.exit(1)

# Step 2: Show migration plan
print("\n[Step 2] Showing migration plan...")
try:
    call_command('showmigrations', 'main', verbosity=2)
except Exception as e:
    print(f"✗ Error showing migrations: {e}")

# Step 3: Apply migrations
print("\n[Step 3] Applying migrations...")
try:
    call_command('migrate', 'main', verbosity=2)
    print("✓ Migrations applied successfully")
except Exception as e:
    print(f"✗ Error applying migrations: {e}")
    print("Note: This is expected if running with existing data")

# Step 4: Create superuser (optional)
print("\n[Step 4] Creating superuser (optional)...")
from main.models import User
if not User.objects.filter(username='admin').exists():
    try:
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123', user_type='admin')
        print("✓ Superuser 'admin' created successfully")
    except Exception as e:
        print(f"Note: Superuser creation optional: {e}")
else:
    print("Note: Superuser 'admin' already exists")

print("\n" + "=" * 80)
print("Database setup complete!")
print("=" * 80)
print("\nNext steps:")
print("1. Test the application: python manage.py runserver")
print("2. Run tests: python manage.py test main")
print("3. Create admin user: python manage.py createsuperuser")
print("=" * 80)
