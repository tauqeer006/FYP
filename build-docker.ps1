# Docker Build Script for FYP - Windows PowerShell Version
# Run this to rebuild Docker with all updates

Write-Host "============================================" -ForegroundColor Green
Write-Host "FYP Docker Build - Complete Project Refined" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green

# Step 1: Stop existing containers
Write-Host "`n[Step 1] Stopping existing containers..." -ForegroundColor Yellow
docker compose down 2>$null

# Step 2: Remove old images
Write-Host "[Step 2] Removing old images..." -ForegroundColor Yellow
docker rmi fyp-django:latest 2>$null
docker image prune -f 2>$null

# Step 3: Build new image
Write-Host "[Step 3] Building Django image (this may take 5-10 minutes)..." -ForegroundColor Yellow
docker compose build --no-cache django-app

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Build successful" -ForegroundColor Green

# Step 4: Start containers
Write-Host "`n[Step 4] Starting containers..." -ForegroundColor Yellow
docker compose up -d

# Step 5: Wait for Django
Write-Host "[Step 5] Waiting for Django to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Step 6: Run migrations
Write-Host "[Step 6] Running database migrations..." -ForegroundColor Yellow
docker compose exec -T web python manage.py migrate

if ($LASTEXITCODE -ne 0) {
    Write-Host "Migrations failed!" -ForegroundColor Red
    docker compose logs web
    exit 1
}

Write-Host "✓ Migrations successful" -ForegroundColor Green

# Step 7: Run tests
Write-Host "`n[Step 7] Running tests..." -ForegroundColor Yellow
docker compose exec -T web python manage.py test main

# Step 8: Show status
Write-Host "`n[Step 8] Container status:" -ForegroundColor Yellow
docker compose ps

Write-Host "`n============================================" -ForegroundColor Green
Write-Host "Build Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green

Write-Host "`nAccess your application:"
Write-Host "  Web:     http://localhost:8000"
Write-Host "  Admin:   http://localhost:8000/admin"

Write-Host "`nUseful commands:"
Write-Host "  Logs:    docker compose logs -f web"
Write-Host "  Shell:   docker compose exec web python manage.py shell"
Write-Host "  Stop:    docker compose down"
