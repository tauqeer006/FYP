#!/bin/bash

echo "🚀 Starting FYP Project with Docker Compose..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "📦 Building and starting all services..."

# Build and start all services
docker-compose up --build -d

echo "⏳ Waiting for services to be ready..."

# Wait for services to be ready
sleep 30

echo "✅ All services are starting up!"
echo ""
echo "🌐 Service URLs:"
echo "   Django Web App:     http://localhost:8000"
echo "   CNN API:            http://localhost:5001"
echo "   X-ray API:          http://localhost:5002"
echo "   Pose Detection API: http://localhost:5003"
echo ""

echo "📊 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"
echo ""
echo "🔍 Health Check URLs:"
echo "   CNN API Health:     http://localhost:5001/health"
echo "   X-ray API Health:   http://localhost:5002/health"
echo "   Pose API Health:    http://localhost:5003/health"
