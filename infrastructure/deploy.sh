#!/bin/bash

# Zentry Cloud Infrastructure Deployment Script

set -e

echo "🚀 Deploying Zentry Cloud Infrastructure..."

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo "❌ terraform.tfvars not found!"
    echo "📝 Please copy terraform.tfvars.example to terraform.tfvars and configure it"
    exit 1
fi

# Check if kubectl is configured
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ kubectl is not configured or cluster is not accessible"
    echo "🔧 Please configure kubectl to connect to your Kubernetes cluster"
    exit 1
fi

# Initialize Terraform
echo "🔧 Initializing Terraform..."
terraform init

# Validate configuration
echo "✅ Validating Terraform configuration..."
terraform validate

# Plan deployment
echo "📋 Planning deployment..."
terraform plan -out=tfplan

# Ask for confirmation
read -p "🤔 Do you want to apply this plan? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Apply configuration
echo "🚀 Applying configuration..."
terraform apply tfplan

# Display outputs
echo "✅ Deployment completed!"
echo "📊 Infrastructure Information:"
terraform output

echo ""
echo "🎉 Zentry Cloud is now deployed!"
echo "📝 Next steps:"
echo "   1. Configure DNS records for your domain"
echo "   2. Access services using the URLs above"
echo "   3. Set up monitoring dashboards"
echo "   4. Create your first user accounts"