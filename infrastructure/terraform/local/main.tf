resource "kind_cluster" "main" {
  name            = var.cluster_name
  node_image      = "kindest/node:v1.29.0"
  wait_for_ready  = true

  kind_config = <<-EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
EOF
}
