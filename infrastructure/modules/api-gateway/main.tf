resource "kubernetes_config_map" "api_gateway_config" {
  metadata {
    name      = "api-gateway-config"
    namespace = var.namespace
  }

  data = {
    "config.json" = jsonencode({
      database = {
        host     = "postgres"
        port     = 5432
        database = "zentry"
        username = "zentry"
      }
      keycloak = {
        url   = "http://keycloak:8080"
        realm = "master"
      }
      minio = {
        endpoint   = "minio-api:9000"
        access_key = "admin"
        secret_key = "password"
      }
      server = {
        port = 8000
        host = "0.0.0.0"
      }
    })
  }
}

resource "kubernetes_deployment" "api_gateway" {
  metadata {
    name      = "api-gateway"
    namespace = var.namespace
    labels = {
      app = "api-gateway"
    }
  }

  spec {
    replicas = 2

    selector {
      match_labels = {
        app = "api-gateway"
      }
    }

    template {
      metadata {
        labels = {
          app = "api-gateway"
        }
      }

      spec {
        container {
          image = "zentry/api-gateway:latest"
          name  = "api-gateway"

          env {
            name  = "CONFIG_PATH"
            value = "/config/config.json"
          }

          env {
            name  = "ENVIRONMENT"
            value = "production"
          }

          port {
            container_port = 8000
          }

          volume_mount {
            name       = "config"
            mount_path = "/config"
          }

          resources {
            limits = {
              cpu    = "1000m"
              memory = "1Gi"
            }
            requests = {
              cpu    = "500m"
              memory = "512Mi"
            }
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 30
            period_seconds        = 10
          }

          readiness_probe {
            http_get {
              path = "/ready"
              port = 8000
            }
            initial_delay_seconds = 15
            period_seconds        = 5
          }
        }

        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.api_gateway_config.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "api_gateway" {
  metadata {
    name      = "api-gateway"
    namespace = var.namespace
  }

  spec {
    selector = {
      app = "api-gateway"
    }

    port {
      port        = 8000
      target_port = 8000
    }

    type = "ClusterIP"
  }
}

# Ingress for API Gateway
resource "kubernetes_ingress_v1" "api_gateway" {
  metadata {
    name      = "api-gateway-ingress"
    namespace = var.namespace
    annotations = {
      "traefik.ingress.kubernetes.io/router.entrypoints" = "websecure"
      "traefik.ingress.kubernetes.io/router.tls"         = "true"
      "cert-manager.io/cluster-issuer"                   = "letsencrypt"
    }
  }

  spec {
    tls {
      hosts       = ["api.${var.domain}"]
      secret_name = "api-gateway-tls"
    }

    rule {
      host = "api.${var.domain}"
      http {
        path {
          path      = "/"
          path_type = "Prefix"
          backend {
            service {
              name = kubernetes_service.api_gateway.metadata[0].name
              port {
                number = 8000
              }
            }
          }
        }
      }
    }
  }
}