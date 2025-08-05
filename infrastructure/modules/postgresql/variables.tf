variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
}

variable "password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}