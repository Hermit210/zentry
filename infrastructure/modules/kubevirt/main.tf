# KubeVirt Operator
resource "kubernetes_namespace" "kubevirt" {
  metadata {
    name = "kubevirt"
  }
}

# KubeVirt Custom Resource Definitions and Operator
resource "kubernetes_manifest" "kubevirt_operator" {
  manifest = {
    apiVersion = "apps/v1"
    kind       = "Deployment"
    metadata = {
      name      = "virt-operator"
      namespace = "kubevirt"
      labels = {
        "kubevirt.io" = ""
      }
    }
    spec = {
      replicas = 2
      selector = {
        matchLabels = {
          "kubevirt.io" = "virt-operator"
        }
      }
      template = {
        metadata = {
          labels = {
            "kubevirt.io" = "virt-operator"
          }
        }
        spec = {
          serviceAccountName = "kubevirt-operator"
          containers = [
            {
              name  = "virt-operator"
              image = "quay.io/kubevirt/virt-operator:v1.0.0"
              env = [
                {
                  name = "OPERATOR_IMAGE"
                  value = "quay.io/kubevirt/virt-operator:v1.0.0"
                },
                {
                  name = "WATCH_NAMESPACE"
                  valueFrom = {
                    fieldRef = {
                      fieldPath = "metadata.annotations['olm.targetNamespaces']"
                    }
                  }
                }
              ]
              resources = {
                requests = {
                  cpu    = "10m"
                  memory = "150Mi"
                }
              }
            }
          ]
        }
      }
    }
  }

  depends_on = [kubernetes_namespace.kubevirt]
}

# KubeVirt Custom Resource
resource "kubernetes_manifest" "kubevirt_cr" {
  manifest = {
    apiVersion = "kubevirt.io/v1"
    kind       = "KubeVirt"
    metadata = {
      name      = "kubevirt"
      namespace = "kubevirt"
    }
    spec = {
      certificateRotateStrategy = {}
      configuration = {
        developerConfiguration = {
          useEmulation = true
        }
      }
      customizeComponents = {}
      imagePullPolicy = "IfNotPresent"
      workloadUpdateStrategy = {
        workloadUpdateMethods = ["LiveMigrate"]
      }
    }
  }

  depends_on = [kubernetes_manifest.kubevirt_operator]
}

# Service Account for KubeVirt
resource "kubernetes_service_account" "kubevirt_operator" {
  metadata {
    name      = "kubevirt-operator"
    namespace = "kubevirt"
  }

  depends_on = [kubernetes_namespace.kubevirt]
}

# ClusterRole for KubeVirt
resource "kubernetes_cluster_role" "kubevirt_operator" {
  metadata {
    name = "kubevirt-operator"
  }

  rule {
    api_groups = ["kubevirt.io"]
    resources  = ["*"]
    verbs      = ["*"]
  }

  rule {
    api_groups = [""]
    resources  = ["pods", "services", "endpoints", "persistentvolumeclaims", "events", "configmaps", "secrets", "serviceaccounts"]
    verbs      = ["*"]
  }

  rule {
    api_groups = ["apps"]
    resources  = ["deployments", "daemonsets", "replicasets", "statefulsets"]
    verbs      = ["*"]
  }

  rule {
    api_groups = ["monitoring.coreos.com"]
    resources  = ["servicemonitors", "prometheusrules"]
    verbs      = ["*"]
  }

  rule {
    api_groups = ["subresources.kubevirt.io"]
    resources  = ["*"]
    verbs      = ["*"]
  }
}

# ClusterRoleBinding for KubeVirt
resource "kubernetes_cluster_role_binding" "kubevirt_operator" {
  metadata {
    name = "kubevirt-operator"
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role.kubevirt_operator.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.kubevirt_operator.metadata[0].name
    namespace = "kubevirt"
  }
}