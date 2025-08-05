output "endpoint" {
  description = "MinIO API endpoint"
  value       = "http://${kubernetes_service.minio_api.metadata[0].name}:9000"
}

output "console_url" {
  description = "MinIO console URL"
  value       = "http://${kubernetes_service.minio_console.metadata[0].name}:9001"
}

output "service_name" {
  description = "MinIO service name"
  value       = kubernetes_service.minio_api.metadata[0].name
}