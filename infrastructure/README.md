# Zentry Cloud Infrastructure

This directory contains Terraform configurations for deploying the Zentry Cloud MVP infrastructure.

## Architecture Overview

```
┌─────────────────────────────┐
│      Load Balancer          │ ← Traefik (SSL termination)
└────────────┬────────────────┘
             │
┌────────────▼────────────────┐
│    Kubernetes Cluster       │ ← K3s/K8s for orchestration
└────────────┬────────────────┘
             │
┌────────────▼────────────────┐
│  Core Services              │
│  ├── Identity (Keycloak)    │ ← OAuth2/OIDC
│  ├── API Gateway           │ ← FastAPI/Express
│  ├── Billing Service       │ ← Usage tracking
│  └── VM Manager            │ ← KubeVirt for VMs
└─────────────────────────────┘
             │
┌────────────▼────────────────┐
│  Storage Layer              │
│  ├── Object Storage (MinIO) │ ← S3-compatible
│  ├── Block Storage (Ceph)   │ ← Persistent volumes
│  └── Database (PostgreSQL)  │ ← Metadata & billing
└─────────────────────────────┘
```

## Components

- **Compute**: KubeVirt for VM management on Kubernetes
- **Storage**: MinIO for object storage, Ceph for block storage
- **Networking**: Traefik for load balancing and SSL
- **Identity**: Keycloak for authentication and authorization
- **Database**: PostgreSQL for metadata and billing data

## Quick Start

1. Install dependencies:
   ```bash
   terraform init
   ```

2. Configure variables:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your settings
   ```

3. Deploy infrastructure:
   ```bash
   terraform plan
   terraform apply
   ```

## Directory Structure

- `main.tf` - Main infrastructure configuration
- `variables.tf` - Input variables
- `outputs.tf` - Output values
- `modules/` - Reusable Terraform modules
- `environments/` - Environment-specific configurations