variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
}

variable "access_key" {
  description = "MinIO access key"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "MinIO secret key"
  type        = string
  sensitive   = true
}

variable "storage_size" {
  description = "Storage size for MinIO"
  type        = string
  default     = "100Gi"
}