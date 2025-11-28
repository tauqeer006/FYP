#!/usr/bin/env bash
# Docker Build Script for FYP with all updates

echo "============================================"
echo "FYP Docker Build - Complete Project Refined"
echo "============================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Stop existing containers
echo -e "\n${YELLOW}[Step 1]${NC} Stopping existing containers..."
docker compose down 2>/dev/null || true

# Step 2: Remove old images (optional)
echo -e "${YELLOW}[Step 2]${NC} Removing old images..."
docker rmi fyp-django:latest 2>/dev/null || true
docker image prune -f 2>/dev/null || true

# Step 3: Build new image with no cache
echo -e "${YELLOW}[Step 3]${NC} Building Django image (this may take 5-10 minutes)..."
docker compose build --no-cache django-app

if [ $? -ne 0 ]; then
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Build successful${NC}"

# Step 4: Start containers
echo -e "\n${YELLOW}[Step 4]${NC} Starting containers..."
docker compose up -d

# Wait for Django to be ready
echo -e "${YELLOW}[Step 5]${NC} Waiting for Django to be ready..."
sleep 10

# Step 5: Run migrations
echo -e "${YELLOW}[Step 6]${NC} Running database migrations..."
docker compose exec -T web python manage.py migrate

if [ $? -ne 0 ]; then
    echo -e "${RED}Migrations failed!${NC}"
    docker compose logs web
    exit 1
fi

echo -e "${GREEN}✓ Migrations successful${NC}"

# Step 6: Run tests
echo -e "\n${YELLOW}[Step 7]${NC} Running tests..."
docker compose exec -T web python manage.py test main

# Step 7: Show status
echo -e "\n${YELLOW}[Step 8]${NC} Container status:"
docker compose ps

echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${GREEN}============================================${NC}"

echo -e "\nAccess your application:"
echo -e "  Web:     http://localhost:8000"
echo -e "  Admin:   http://localhost:8000/admin"
echo -e "\nUseful commands:"
echo -e "  Logs:    docker compose logs -f web"
echo -e "  Shell:   docker compose exec web python manage.py shell"
echo -e "  Stop:    docker compose down"

