# Zentry Cloud Backend Startup Script

Write-Host "Starting Zentry Cloud Backend..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python version: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python is not installed. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Please edit .env with your Supabase credentials before running again!" -ForegroundColor Red
    Write-Host "Required: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY, SECRET_KEY" -ForegroundColor Yellow
    exit 1
}

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Blue
pip install -r requirements.txt

# Start the backend
Write-Host "Starting FastAPI server..." -ForegroundColor Blue
Write-Host ""
Write-Host "Backend Services:" -ForegroundColor Cyan
Write-Host "  API:          http://localhost:8000" -ForegroundColor White
Write-Host "  Health:       http://localhost:8000/health" -ForegroundColor White
Write-Host "  Docs:         http://localhost:8000/docs" -ForegroundColor White
Write-Host "  ReDoc:        http://localhost:8000/redoc" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python main.py