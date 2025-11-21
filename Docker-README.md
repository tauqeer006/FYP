# FYP Project - Docker Deployment

This project contains a complete medical diagnosis and recommendation system with multiple AI-powered services.

## 🏗️ Architecture

The project consists of 4 main services:

1. **Django Web Application** (Port 8000) - Main web interface
2. **CNN API** (Port 5001) - Left/Right fracture detection
3. **X-ray Model API** (Port 5002) - General fracture detection
4. **Pose Detection API** (Port 5003) - Exercise quality assessment

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- At least 8GB RAM available
- 10GB free disk space

### Starting the Application

1. **Clone/Navigate to the project directory**
   ```bash
   cd /path/to/your/FYP/project
   ```

2. **Start all services**
   ```bash
   # Make scripts executable (Linux/Mac)
   chmod +x start.sh stop.sh
   
   # Start all services
   ./start.sh
   ```
   
   Or manually:
   ```bash
   docker-compose up --build -d
   ```

3. **Access the applications**
   - Django Web App: http://localhost:8000
   - CNN API: http://localhost:5001
   - X-ray API: http://localhost:5002
   - Pose Detection API: http://localhost:5003

## 📋 Service Details

### Django Web Application (Port 8000)
- **Purpose**: Main web interface for the medical system
- **Features**: User management, patient records, diagnosis interface
- **Health Check**: http://localhost:8000/admin/

### CNN API (Port 5001)
- **Purpose**: Detects left/right fractures in X-ray images
- **Endpoint**: `POST /predict-lr`
- **Input**: Image file
- **Health Check**: http://localhost:5001/health

### X-ray Model API (Port 5002)
- **Purpose**: General fracture detection using YOLO
- **Endpoint**: `POST /detect-fracture`
- **Input**: Image file
- **Health Check**: http://localhost:5002/health

### Pose Detection API (Port 5003)
- **Purpose**: Exercise quality assessment using pose analysis
- **Endpoint**: `POST /analyze-pose`
- **Input**: Base64 encoded image
- **Health Check**: http://localhost:5003/health


## 🔧 Management Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f django-app
docker-compose logs -f cnn-api
docker-compose logs -f xray-api
docker-compose logs -f pose-api
```

### Stop Services
```bash
./stop.sh
# or
docker-compose down
```

### Rebuild Services
```bash
docker-compose up --build -d
```

### Remove Everything
```bash
# Stop and remove containers, networks, and volumes
docker-compose down -v

# Remove images as well
docker-compose down --rmi all -v
```

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using the port
   netstat -tulpn | grep :8000
   
   # Kill the process or change ports in docker-compose.yml
   ```

2. **Out of memory**
   ```bash
   # Increase Docker memory limit in Docker Desktop settings
   # Or remove unused containers/images
   docker system prune -a
   ```

3. **Model files not found**
   ```bash
   # Ensure model files are in the correct directories
   # Check Models_Apis/ and Pose_Dection/ folders
   ```

4. **Services not starting**
   ```bash
   # Check logs for specific errors
   docker-compose logs [service-name]
   
   # Rebuild specific service
   docker-compose build [service-name]
   ```

### Health Checks

Test each service individually:

```bash
# Django
curl http://localhost:8000/admin/

# CNN API
curl http://localhost:5001/health

# X-ray API
curl http://localhost:5002/health

# Pose API
curl http://localhost:5003/health
```

## 📁 File Structure

```
FYP/
├── docker-compose.yml          # Main orchestration file
├── Dockerfile.django          # Django app container
├── Dockerfile.cnn-api         # CNN API container
├── Dockerfile.xray-api        # X-ray API container
├── Dockerfile.pose-api        # Pose detection container
├── requirements.txt           # Python dependencies
├── .dockerignore             # Docker ignore file
├── start.sh                  # Startup script
├── stop.sh                   # Stop script
├── Docker-README.md          # This file
├── FYP/                      # Django project
├── Models_Apis/              # ML model APIs
├── Pose_Dection/             # Pose detection system
```

## 🔒 Security Notes

- Change default passwords in Django settings
- Use environment variables for sensitive data
- Enable HTTPS in production
- Regularly update dependencies

## 📞 Support

If you encounter any issues:

1. Check the logs: `docker-compose logs -f`
2. Verify all model files are present
3. Ensure sufficient system resources
4. Check Docker and Docker Compose versions

## 🚀 Production Deployment

For production deployment:

1. Update `ALLOWED_HOSTS` in Django settings
2. Set `DEBUG=False`
3. Use environment variables for secrets
4. Configure proper logging
5. Set up reverse proxy (nginx)
6. Use HTTPS certificates
7. Configure backup strategies
