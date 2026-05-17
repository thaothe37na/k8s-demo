resource "helm_release" "jaeger" {
  name             = "jaeger"
  repository       = "https://jaegertracing.github.io/helm-charts"
  chart            = "jaeger"
  namespace        = "tracing"
  create_namespace = true
  wait             = true
  timeout          = 300

  values = [<<-EOF
provisionDataStore:
  cassandra: false
allInOne:
  enabled: true
  resources:
    requests:
      memory: "256Mi"
      cpu: "100m"
    limits:
      memory: "512Mi"
      cpu: "300m"
storage:
  type: memory
agent:
  enabled: false
collector:
  enabled: false
query:
  enabled: false
EOF
  ]

  depends_on = [kind_cluster.main]
}
