resource "helm_release" "loki" {
  name             = "loki"
  repository       = "https://grafana.github.io/helm-charts"
  chart            = "loki-stack"
  namespace        = "logging"
  create_namespace = true
  wait             = true
  timeout          = 300

  values = [<<-EOF
loki:
  enabled: true
  service:
    type: ClusterIP
    port: 3100
  persistence:
    enabled: false
  resources:
    requests:
      memory: "128Mi"
      cpu: "100m"
    limits:
      memory: "256Mi"
      cpu: "200m"
promtail:
  enabled: true
  config:
    clients:
      - url: http://loki:3100/loki/api/v1/push
EOF
  ]

  depends_on = [kind_cluster.main]
}
