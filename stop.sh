#!/bin/bash

echo "🛑 Stopping FYP Project services..."

# Stop all services
docker-compose down

echo "✅ All services have been stopped!"
echo ""
echo "🧹 To remove all containers and volumes: docker-compose down -v"
echo "🗑️ To remove images: docker-compose down --rmi all"


