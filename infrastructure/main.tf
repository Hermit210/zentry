terraform {
  required_version = ">= 1.0"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

# Configure Kubernetes provider
provider "kubernetes" {
  config_path = "~/.kube/config"
}

provider "helm" {
  kubernetes {
    config_path = "~/.kube/config"
  }
}

# Create namespace for Zentry Cloud
resource "kubernetes_namespace" "zentry" {
  metadata {
    name = "zentry-cloud"
    labels = {
      name        = "zentry-cloud"
      environment = var.environment
    }
  }
}

# Create namespace for monitoring
resource "kubernetes_namespace" "monitoring" {
  count = var.enable_monitoring ? 1 : 0
  metadata {
    name = "monitoring"
    labels = {
      name = "monitoring"
    }
  }
}

# PostgreSQL Database
module "postgresql" {
  source = "./modules/postgresql"
  
  namespace = kubernetes_namespace.zentry.metadata[0].name
  password  = var.postgres_password
  
  depends_on = [kubernetes_namespace.zentry]
}

# MinIO Object Storage
module "minio" {
  source = "./modules/minio"
  
  namespace   = kubernetes_namespace.zentry.metadata[0].name
  access_key  = var.minio_access_key
  secret_key  = var.minio_secret_key
  storage_size = "${var.storage_size}Gi"
  
  depends_on = [kubernetes_namespace.zentry]
}

# Keycloak Identity Management
module "keycloak" {
  source = "./modules/keycloak"
  
  namespace      = kubernetes_namespace.zentry.metadata[0].name
  admin_password = var.keycloak_admin_password
  domain         = var.domain
  
  depends_on = [module.postgresql]
}

# Traefik Load Balancer
module "traefik" {
  source = "./modules/traefik"
  
  namespace = kubernetes_namespace.zentry.metadata[0].name
  domain    = var.domain
  ssl_email = var.ssl_email
  
  depends_on = [kubernetes_namespace.zentry]
}

# KubeVirt for VM management
module "kubevirt" {
  source = "./modules/kubevirt"
  
  namespace = kubernetes_namespace.zentry.metadata[0].name
  
  depends_on = [kubernetes_namespace.zentry]
}

# Zentry API Gateway
module "api_gateway" {
  source = "./modules/api-gateway"
  
  namespace = kubernetes_namespace.zentry.metadata[0].name
  domain    = var.domain
  
  depends_on = [module.keycloak, module.postgresql]
}

# Monitoring stack (optional)
module "monitoring" {
  count  = var.enable_monitoring ? 1 : 0
  source = "./modules/monitoring"
  
  namespace = kubernetes_namespace.monitoring[0].metadata[0].name
  domain    = var.domain
  
  depends_on = [kubernetes_namespace.monitoring]
}