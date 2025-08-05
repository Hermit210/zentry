# Start Zentry Cloud Frontend

Write-Host "Starting Zentry Cloud Frontend..." -ForegroundColor Green

# Check if Node.js is installed
try {
    $nodeVersion = node --version 2>&1
    Write-Host "Node.js version: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "Node.js is not installed. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "Installing Node.js dependencies..." -ForegroundColor Blue
npm install

# Start the frontend
Write-Host "Starting Next.js development server..." -ForegroundColor Blue
Write-Host "Frontend will be available at: http://localhost:3000" -ForegroundColor Cyan

npm run dev