resource "random_password" "argocd" {
  length  = 16
  special = false
}

resource "helm_release" "argocd" {
  name             = "argocd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  namespace        = "argocd"
  create_namespace = true
  wait             = true
  timeout          = 600

  values = [<<-EOF
server:
  service:
    type: NodePort
    nodePortHttp: 30081
configs:
  params:
    server.insecure: true
  secret:
    argocdServerAdminPassword: "${bcrypt(var.argocd_admin_password)}"
EOF
  ]

  depends_on = [kind_cluster.main]
}
