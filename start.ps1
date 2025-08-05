# Zentry Cloud Frontend Startup

Write-Host "Starting Zentry Cloud..." -ForegroundColor Green

# Check if Node.js is installed
try {
    $nodeVersion = node --version 2>&1
    Write-Host "Node.js version: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "Node.js is not installed. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Blue
npm install

# Start the frontend
Write-Host "Starting development server..." -ForegroundColor Blue
Write-Host "Zentry Cloud will be available at: http://localhost:3000" -ForegroundColor Cyan

npm run dev