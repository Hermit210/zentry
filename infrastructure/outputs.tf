output "cluster_info" {
  description = "Cluster information"
  value = {
    name        = var.cluster_name
    environment = var.environment
    domain      = var.domain
  }
}

output "api_endpoints" {
  description = "API endpoints for Zentry Cloud services"
  value = {
    api_gateway = "https://api.${var.domain}"
    keycloak    = "https://auth.${var.domain}"
    minio       = "https://storage.${var.domain}"
    dashboard   = "https://dashboard.${var.domain}"
  }
}

output "database_connection" {
  description = "Database connection information"
  value = {
    host     = module.postgresql.host
    port     = module.postgresql.port
    database = module.postgresql.database
  }
  sensitive = true
}

output "storage_info" {
  description = "Storage service information"
  value = {
    minio_endpoint = module.minio.endpoint
    minio_console  = module.minio.console_url
  }
}

output "monitoring_urls" {
  description = "Monitoring service URLs"
  value = var.enable_monitoring ? {
    prometheus = "https://prometheus.${var.domain}"
    grafana    = "https://grafana.${var.domain}"
  } : null
}

output "next_steps" {
  description = "Next steps after deployment"
  value = [
    "1. Configure DNS records for *.${var.domain}",
    "2. Access Keycloak admin at https://auth.${var.domain}",
    "3. Configure API gateway settings",
    "4. Set up monitoring dashboards",
    "5. Create first user accounts"
  ]
}