output "service_name" {
  description = "API Gateway service name"
  value       = kubernetes_service.api_gateway.metadata[0].name
}

output "api_url" {
  description = "API Gateway URL"
  value       = "https://api.${var.domain}"
}