variable "cluster_name" {
  description = "Name of the Zentry Cloud cluster"
  type        = string
  default     = "zentry-cloud"
}

variable "domain" {
  description = "Domain name for the cloud platform"
  type        = string
  default     = "zentry.cloud"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "node_count" {
  description = "Number of worker nodes"
  type        = number
  default     = 3
}

variable "node_instance_type" {
  description = "Instance type for worker nodes"
  type        = string
  default     = "m5.large"
}

variable "storage_size" {
  description = "Size of storage in GB"
  type        = number
  default     = 100
}

variable "enable_monitoring" {
  description = "Enable Prometheus and Grafana monitoring"
  type        = bool
  default     = true
}

variable "enable_backup" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "ssl_email" {
  description = "Email for Let's Encrypt SSL certificates"
  type        = string
}

variable "keycloak_admin_password" {
  description = "Admin password for Keycloak"
  type        = string
  sensitive   = true
}

variable "postgres_password" {
  description = "Password for PostgreSQL database"
  type        = string
  sensitive   = true
}

variable "minio_access_key" {
  description = "Access key for MinIO"
  type        = string
  sensitive   = true
}

variable "minio_secret_key" {
  description = "Secret key for MinIO"
  type        = string
  sensitive   = true
}