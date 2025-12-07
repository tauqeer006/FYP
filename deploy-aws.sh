#!/bin/bash

# FYP HTTPS Setup Script for AWS Deployment
# This script sets up SSL/TLS certificates and deploys the application

set -e

DOMAIN_NAME="medxai.duckdns.org"
EMAIL="tauqeerqureshi112@gmail.com"

echo "=================================="
echo "FYP AWS HTTPS Deployment Setup"
echo "=================================="

# Step 1: Create certbot directories
echo "Creating certbot directories..."
mkdir -p certbot/conf
mkdir -p certbot/www

# Step 2: Pull latest code
echo "Pulling latest code from git..."
git pull origin fyp-dev

# Step 3: Copy AWS env file
echo "Setting up .env.aws configuration..."
cp .env.aws .env

# Step 4: Remove old Docker resources
echo "Cleaning up old Docker resources..."
docker compose down || true
docker container prune -f || true
docker image prune -a -f || true
docker volume prune -f || true

# Step 5: Obtain SSL Certificate
echo "Obtaining SSL certificate from Let's Encrypt..."
docker run --rm \
  -v ./certbot/conf:/etc/letsencrypt \
  -v ./certbot/www:/var/www/certbot \
  -p 80:80 \
  certbot/certbot certonly \
  --standalone \
  --agree-tos \
  --non-interactive \
  --preferred-challenges http \
  -d $DOMAIN_NAME \
  -m $EMAIL

# Step 6: Build and start services
echo "Building and starting Docker services..."
docker compose up -d

# Step 7: Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 30

# Step 8: Run Django migrations
echo "Running Django migrations..."
docker compose exec -T django-app python manage.py migrate --noinput || true

# Step 9: Collect static files
echo "Collecting static files..."
docker compose exec -T django-app python manage.py collectstatic --noinput || true

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Your application is now running at:"
echo "  HTTPS: https://$DOMAIN_NAME"
echo "  HTTP:  http://$DOMAIN_NAME (redirects to HTTPS)"
echo ""
echo "Important Notes:"
echo "1. Make sure your DuckDNS domain points to: 54.81.102.223"
echo "2. SSL certificate will auto-renew every 90 days"
echo "3. Check logs: docker compose logs -f"
echo "4. Stop services: docker compose down"
echo ""
