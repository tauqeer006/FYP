#!/bin/bash

echo "========================================"
echo "FYP Project - Complete Rebuild Script"
echo "========================================"
echo ""

cd /home/ubuntu/fyp-project

# Step 1: Pull fresh code
echo "STEP 1: Pulling latest code from GitHub..."
git pull origin fyp-dev

# Step 2: Build images
echo ""
echo "STEP 2: Building Docker images..."
docker-compose build

# Step 3: Start services (just database and Django first)
echo ""
echo "STEP 3: Starting services..."
docker-compose up -d

# Step 4: Wait for database
echo ""
echo "STEP 4: Waiting for PostgreSQL to be ready..."
sleep 30

# Step 5: Run makemigrations
echo ""
echo "STEP 5: Running makemigrations..."
docker-compose exec -T django-app python manage.py makemigrations

# Step 6: Run migrations
echo ""
echo "STEP 6: Running migrations..."
docker-compose exec -T django-app python manage.py migrate

# Step 7: Collect static files
echo ""
echo "STEP 7: Collecting static files..."
docker-compose exec -T django-app python manage.py collectstatic --noinput

# Step 8: Create superuser
echo ""
echo "STEP 8: Creating superuser..."
docker-compose exec -T django-app python manage.py createsuperuser --noinput --username admin --email admin@fyp.com
docker-compose exec -T django-app python manage.py shell << END
from django.contrib.auth.models import User
u = User.objects.get(username='admin')
u.set_password('admin123')
u.save()
print("✓ Admin user: admin / admin123")
END

# Step 9: Final status check
echo ""
echo "STEP 9: Final Status Check..."
docker-compose ps

echo ""
echo "========================================"
echo "✓ Rebuild Complete!"
echo "========================================"
echo ""
echo "Website: http://54.81.102.223:8888/"
echo "Admin: admin / admin123"
echo ""
