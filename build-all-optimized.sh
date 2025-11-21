#!/bin/bash

echo "🚀 Building all optimized APIs..."
echo "This should be much faster and smaller than before!"
echo ""

echo "📦 Building Django App (optimized)..."
docker-compose build django-app
echo "✅ Django App build completed"
echo ""

echo "🧠 Building CNN API (PyTorch optimized)..."
docker-compose build cnn-api
echo "✅ CNN API build completed"
echo ""

echo "🔍 Building X-ray API (Ultralytics optimized)..."
docker-compose build xray-api
echo "✅ X-ray API build completed"
echo ""

echo "🏃 Building Pose API (TensorFlow optimized)..."
docker-compose build pose-api
echo "✅ Pose API build completed"
echo ""

echo "📊 Checking image sizes:"
docker images | grep -E "(django-app|cnn-api|xray-api|pose-api)"

echo ""
echo "🎉 All optimized builds completed!"
echo ""
echo "To run all services:"
echo "docker-compose up"
echo ""
echo "To run individual services:"
echo "docker-compose up django-app"
echo "docker-compose up cnn-api"
echo "docker-compose up xray-api"
echo "docker-compose up pose-api"



