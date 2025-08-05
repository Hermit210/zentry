output "host" {
  description = "PostgreSQL host"
  value       = kubernetes_service.postgres.metadata[0].name
}

output "port" {
  description = "PostgreSQL port"
  value       = 5432
}

output "database" {
  description = "Database name"
  value       = "zentry"
}

output "username" {
  description = "Database username"
  value       = "zentry"
}