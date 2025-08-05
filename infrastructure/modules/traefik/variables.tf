variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
}

variable "domain" {
  description = "Domain name"
  type        = string
}

variable "ssl_email" {
  description = "Email for Let's Encrypt SSL certificates"
  type        = string
}