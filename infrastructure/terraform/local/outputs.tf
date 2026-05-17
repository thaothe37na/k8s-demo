output "kubeconfig_command" {
  value = "kind export kubeconfig --name ${var.cluster_name}"
}

output "argocd_url"  { value = "http://localhost:8080" }
output "grafana_url" { value = "http://localhost:30082 (admin/admin)" }
output "app_url"     { value = "http://localhost/api/..." }
