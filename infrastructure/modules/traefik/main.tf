resource "kubernetes_config_map" "traefik_config" {
  metadata {
    name      = "traefik-config"
    namespace = var.namespace
  }

  data = {
    "traefik.yml" = <<-EOT
      api:
        dashboard: true
        insecure: true

      entryPoints:
        web:
          address: ":80"
        websecure:
          address: ":443"

      certificatesResolvers:
        letsencrypt:
          acme:
            email: ${var.ssl_email}
            storage: /data/acme.json
            httpChallenge:
              entryPoint: web

      providers:
        kubernetes:
          endpoints:
            - "https://kubernetes.default.svc"
    EOT
  }
}

resource "kubernetes_persistent_volume_claim" "traefik_pvc" {
  metadata {
    name      = "traefik-pvc"
    namespace = var.namespace
  }

  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "1Gi"
      }
    }
  }
}

resource "kubernetes_deployment" "traefik" {
  metadata {
    name      = "traefik"
    namespace = var.namespace
    labels = {
      app = "traefik"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "traefik"
      }
    }

    template {
      metadata {
        labels = {
          app = "traefik"
        }
      }

      spec {
        service_account_name = kubernetes_service_account.traefik.metadata[0].name

        container {
          image = "traefik:v3.0"
          name  = "traefik"

          args = [
            "--configfile=/config/traefik.yml"
          ]

          port {
            name           = "web"
            container_port = 80
          }

          port {
            name           = "websecure"
            container_port = 443
          }

          port {
            name           = "dashboard"
            container_port = 8080
          }

          volume_mount {
            name       = "config"
            mount_path = "/config"
          }

          volume_mount {
            name       = "data"
            mount_path = "/data"
          }

          resources {
            limits = {
              cpu    = "500m"
              memory = "512Mi"
            }
            requests = {
              cpu    = "250m"
              memory = "256Mi"
            }
          }
        }

        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.traefik_config.metadata[0].name
          }
        }

        volume {
          name = "data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.traefik_pvc.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service_account" "traefik" {
  metadata {
    name      = "traefik"
    namespace = var.namespace
  }
}

resource "kubernetes_cluster_role" "traefik" {
  metadata {
    name = "traefik"
  }

  rule {
    api_groups = [""]
    resources  = ["services", "endpoints", "secrets"]
    verbs      = ["get", "list", "watch"]
  }

  rule {
    api_groups = ["extensions", "networking.k8s.io"]
    resources  = ["ingresses", "ingressclasses"]
    verbs      = ["get", "list", "watch"]
  }
}

resource "kubernetes_cluster_role_binding" "traefik" {
  metadata {
    name = "traefik"
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role.traefik.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.traefik.metadata[0].name
    namespace = var.namespace
  }
}

resource "kubernetes_service" "traefik" {
  metadata {
    name      = "traefik"
    namespace = var.namespace
  }

  spec {
    selector = {
      app = "traefik"
    }

    port {
      name        = "web"
      port        = 80
      target_port = 80
    }

    port {
      name        = "websecure"
      port        = 443
      target_port = 443
    }

    port {
      name        = "dashboard"
      port        = 8080
      target_port = 8080
    }

    type = "LoadBalancer"
  }
}