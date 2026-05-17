resource "kind_cluster" "main" {
  name            = var.cluster_name
  node_image      = "kindest/node:v1.29.0"
  wait_for_ready  = true

  kind_config {
    api_version = "kind.x-k8s.io/v1alpha4"
    kind        = "Cluster"
    nodes = [
      { role = "control-plane" },
      { role = "worker" },
      { role = "worker" }
    ]
  }
}