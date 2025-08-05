output "load_balancer_ip" {
  description = "Load balancer IP address"
  value       = kubernetes_service.traefik.status[0].load_balancer[0].ingress[0].ip
}

output "dashboard_url" {
  description = "Traefik dashboard URL"
  value       = "http://${var.domain}:8080"
}