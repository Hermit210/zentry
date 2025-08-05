# Start Both Frontend and Backend for Zentry Cloud

Write-Host "Starting Zentry Cloud (Frontend + Backend)..." -ForegroundColor Green

# Check if Python is installed
try {
    python --version | Out-Null
    Write-Host "Python is available" -ForegroundColor Green
} catch {
    Write-Host "Python is not installed. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check if Node.js is installed
try {
    node --version | Out-Null
    Write-Host "Node.js is available" -ForegroundColor Green
} catch {
    Write-Host "Node.js is not installed. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Start Backend
Write-Host "Starting Backend API..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-Command", "cd backend; python simple_main.py"

# Wait for backend to start
Start-Sleep -Seconds 3

# Start Frontend
Write-Host "Starting Frontend..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-Command", "npm run dev"

# Wait for services to start
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "Zentry Cloud is now running!" -ForegroundColor Green
Write-Host ""
Write-Host "Available Services:" -ForegroundColor Cyan
Write-Host "   Frontend:     http://localhost:3000" -ForegroundColor White
Write-Host "   Backend API:  http://localhost:8001" -ForegroundColor White
Write-Host "   API Docs:     http://localhost:8001/docs" -ForegroundColor White
Write-Host ""
Write-Host "You can now:" -ForegroundColor Yellow
Write-Host "   1. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "   2. Click 'Get Started' to create an account" -ForegroundColor White
Write-Host "   3. Create projects and launch VMs" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C in each window to stop the services" -ForegroundColor Red