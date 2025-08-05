# Zentry Cloud Deployment Script (PowerShell)
param(
    [string]$Environment = "development"
)

# Colors for output
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"

# Configuration
$ComposeFile = "docker-compose.yml"

if ($Environment -eq "production") {
    $ComposeFile = "docker-compose.prod.yml"
}

Write-Host "🚀 Deploying Zentry Cloud - Environment: $Environment" -ForegroundColor $Green

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker is not running. Please start Docker and try again." -ForegroundColor $Red
    exit 1
}

# Check if required environment variables are set for production
if ($Environment -eq "production") {
    $requiredVars = @("DATABASE_URL", "SUPABASE_URL", "SUPABASE_KEY", "JWT_SECRET_KEY", "CORS_ORIGINS", "NEXT_PUBLIC_API_URL")
    
    foreach ($var in $requiredVars) {
        if (-not (Get-Variable -Name $var -ErrorAction SilentlyContinue)) {
            Write-Host "❌ Required environment variable $var is not set" -ForegroundColor $Red
            exit 1
        }
    }
}

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Creating .env file from template" -ForegroundColor $Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "⚠️  Please update .env file with your configuration" -ForegroundColor $Yellow
}

# Stop existing containers
Write-Host "🛑 Stopping existing containers..." -ForegroundColor $Yellow
docker-compose -f $ComposeFile down

# Pull latest images
Write-Host "📥 Pulling latest images..." -ForegroundColor $Yellow
docker-compose -f $ComposeFile pull

# Build and start containers
Write-Host "🔨 Building and starting containers..." -ForegroundColor $Yellow
docker-compose -f $ComposeFile up --build -d

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor $Yellow
Start-Sleep -Seconds 10

# Check service health
Write-Host "🏥 Checking service health..." -ForegroundColor $Yellow

# Check backend health
try {
    Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing | Out-Null
    Write-Host "✅ Backend is healthy" -ForegroundColor $Green
} catch {
    Write-Host "❌ Backend health check failed" -ForegroundColor $Red
    docker-compose -f $ComposeFile logs backend
}

# Check frontend health (if not production)
if ($Environment -ne "production") {
    try {
        Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing | Out-Null
        Write-Host "✅ Frontend is healthy" -ForegroundColor $Green
    } catch {
        Write-Host "❌ Frontend health check failed" -ForegroundColor $Red
        docker-compose -f $ComposeFile logs frontend
    }
}

# Show running containers
Write-Host "📋 Running containers:" -ForegroundColor $Green
docker-compose -f $ComposeFile ps

# Show logs
Write-Host "📝 Recent logs:" -ForegroundColor $Green
docker-compose -f $ComposeFile logs --tail=20

Write-Host "🎉 Deployment complete!" -ForegroundColor $Green
Write-Host "🌐 Backend API: http://localhost:8000" -ForegroundColor $Green
if ($Environment -ne "production") {
    Write-Host "🌐 Frontend: http://localhost:3000" -ForegroundColor $Green
}
Write-Host "📚 API Documentation: http://localhost:8000/docs" -ForegroundColor $Green