#!/bin/bash

# FYP Local Development Setup
# This script sets up the local development environment

set -e

echo "=================================="
echo "FYP Local Development Setup"
echo "=================================="

# Step 1: Copy local env file
echo "Setting up .env.local configuration..."
cp .env.local .env

# Step 2: Remove old Docker resources
echo "Cleaning up old Docker resources..."
docker compose down || true
docker container prune -f || true

# Step 3: Build and start services
echo "Building and starting Docker services..."
docker compose up -d

# Step 4: Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 30

# Step 5: Run Django migrations
echo "Running Django migrations..."
docker compose exec -T django-app python manage.py migrate --noinput || true

# Step 6: Collect static files
echo "Collecting static files..."
docker compose exec -T django-app python manage.py collectstatic --noinput || true

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Your application is now running at:"
echo "  HTTP: http://localhost:8888"
echo ""
echo "Services:"
echo "  Django:    http://localhost:8888"
echo "  Nginx:     http://localhost"
echo "  CNN API:   http://localhost:5001"
echo "  X-ray API: http://localhost:5002"
echo "  Pose API:  http://localhost:5003"
echo "  PostgreSQL: localhost:5432"
echo "  Redis:     localhost:6379"
echo ""
echo "View logs: docker compose logs -f"
echo "Stop: docker compose down"
echo ""
