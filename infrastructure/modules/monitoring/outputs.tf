output "prometheus_url" {
  description = "Prometheus URL"
  value       = "https://prometheus.${var.domain}"
}

output "grafana_url" {
  description = "Grafana URL"
  value       = "https://grafana.${var.domain}"
}

output "grafana_admin_password" {
  description = "Grafana admin password"
  value       = "admin123"
  sensitive   = true
}