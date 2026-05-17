variable "kube_host" {
  description = "Kubernetes API server host"
}

variable "kube_cert" {
  description = "Client certificate for Kubernetes"
}

variable "kube_key" {
  description = "Client key for Kubernetes"
}

variable "kube_ca" {
  description = "Cluster CA certificate for Kubernetes"
}

variable "cluster_name" {
  default = "k8s-demo"
}

variable "argocd_admin_password" {
  description = "ArgoCD admin password (plaintext — sẽ được bcrypt tự động)"
  sensitive   = true
}

variable "gitops_repo_url" {
  description = "URL của gitops repo"
  default     = "https://github.com/your-org/gitops"
}

variable "docker_registry" {
  description = "Docker registry prefix (vd: ghcr.io/your-org)"
}
