variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
}

variable "admin_password" {
  description = "Keycloak admin password"
  type        = string
  sensitive   = true
}

variable "domain" {
  description = "Domain name for Keycloak"
  type        = string
}