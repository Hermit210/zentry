resource "kubernetes_secret" "keycloak_secret" {
  metadata {
    name      = "keycloak-secret"
    namespace = var.namespace
  }

  data = {
    admin-password = var.admin_password
  }

  type = "Opaque"
}

resource "kubernetes_persistent_volume_claim" "keycloak_pvc" {
  metadata {
    name      = "keycloak-pvc"
    namespace = var.namespace
  }

  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "10Gi"
      }
    }
  }
}

resource "kubernetes_deployment" "keycloak" {
  metadata {
    name      = "keycloak"
    namespace = var.namespace
    labels = {
      app = "keycloak"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "keycloak"
      }
    }

    template {
      metadata {
        labels = {
          app = "keycloak"
        }
      }

      spec {
        container {
          image = "quay.io/keycloak/keycloak:22.0"
          name  = "keycloak"

          args = ["start-dev"]

          env {
            name  = "KEYCLOAK_ADMIN"
            value = "admin"
          }

          env {
            name = "KEYCLOAK_ADMIN_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.keycloak_secret.metadata[0].name
                key  = "admin-password"
              }
            }
          }

          env {
            name  = "KC_DB"
            value = "postgres"
          }

          env {
            name  = "KC_DB_URL"
            value = "jdbc:postgresql://postgres:5432/zentry"
          }

          env {
            name  = "KC_DB_USERNAME"
            value = "zentry"
          }

          env {
            name  = "KC_DB_PASSWORD"
            value = "postgres123" # This should be from a secret in production
          }

          env {
            name  = "KC_HOSTNAME"
            value = "auth.${var.domain}"
          }

          env {
            name  = "KC_HTTP_ENABLED"
            value = "true"
          }

          port {
            container_port = 8080
          }

          volume_mount {
            name       = "keycloak-data"
            mount_path = "/opt/keycloak/data"
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

          readiness_probe {
            http_get {
              path = "/realms/master"
              port = 8080
            }
            initial_delay_seconds = 60
            period_seconds        = 10
          }

          liveness_probe {
            http_get {
              path = "/realms/master"
              port = 8080
            }
            initial_delay_seconds = 120
            period_seconds        = 30
          }
        }

        volume {
          name = "keycloak-data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.keycloak_pvc.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "keycloak" {
  metadata {
    name      = "keycloak"
    namespace = var.namespace
  }

  spec {
    selector = {
      app = "keycloak"
    }

    port {
      port        = 8080
      target_port = 8080
    }

    type = "ClusterIP"
  }
}