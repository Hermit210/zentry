output "service_name" {
  description = "Keycloak service name"
  value       = kubernetes_service.keycloak.metadata[0].name
}

output "admin_url" {
  description = "Keycloak admin console URL"
  value       = "https://auth.${var.domain}/admin"
}

output "realm_url" {
  description = "Keycloak realm URL"
  value       = "https://auth.${var.domain}/realms/master"
}