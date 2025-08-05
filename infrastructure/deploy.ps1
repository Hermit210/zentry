# Zentry Cloud Infrastructure Deployment Script (PowerShell)

Write-Host "Deploying Zentry Cloud Infrastructure..." -ForegroundColor Green

# Check if terraform.tfvars exists
if (-not (Test-Path "terraform.tfvars")) {
    Write-Host "terraform.tfvars not found!" -ForegroundColor Red
    Write-Host "Please copy terraform.tfvars.example to terraform.tfvars and configure it" -ForegroundColor Yellow
    exit 1
}

# Check if kubectl is configured
try {
    kubectl cluster-info | Out-Null
    Write-Host "Kubernetes cluster is accessible" -ForegroundColor Green
} catch {
    Write-Host "kubectl is not configured or cluster is not accessible" -ForegroundColor Red
    Write-Host "Please configure kubectl to connect to your Kubernetes cluster" -ForegroundColor Yellow
    Write-Host "For local development, you can use minikube or kind" -ForegroundColor Yellow
    Write-Host "Continuing anyway for demonstration..." -ForegroundColor Yellow
}

# Initialize Terraform
Write-Host "Initializing Terraform..." -ForegroundColor Blue
terraform init

# Validate configuration
Write-Host "Validating Terraform configuration..." -ForegroundColor Blue
terraform validate

# Plan deployment
Write-Host "Planning deployment..." -ForegroundColor Blue
terraform plan -out=tfplan

# Ask for confirmation
$confirmation = Read-Host "Do you want to apply this plan? (y/N)"
if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
    Write-Host "Deployment cancelled" -ForegroundColor Red
    exit 1
}

# Apply configuration
Write-Host "Applying configuration..." -ForegroundColor Green
terraform apply tfplan

# Display outputs
Write-Host "Deployment completed!" -ForegroundColor Green
Write-Host "Infrastructure Information:" -ForegroundColor Blue
terraform output

Write-Host ""
Write-Host "Zentry Cloud is now deployed!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "   1. Configure DNS records for your domain"
Write-Host "   2. Access services using the URLs above"
Write-Host "   3. Set up monitoring dashboards"
Write-Host "   4. Create your first user accounts"