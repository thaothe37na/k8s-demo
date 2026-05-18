# Strimzi Operator
resource "helm_release" "strimzi_operator" {
  name             = "strimzi"
  repository       = "https://strimzi.io/charts/"
  chart            = "strimzi-kafka-operator"
  namespace        = "kafka"
  create_namespace = true
  wait             = true
  timeout          = 300

  depends_on = [kind_cluster.main]
}

# Kafka cluster (single-node cho local demo)
resource "kubernetes_manifest" "kafka_cluster" {
  manifest = {
    apiVersion = "kafka.strimzi.io/v1beta2"
    kind       = "Kafka"
    metadata = {
      name      = "kafka-cluster"
      namespace = "kafka"
    }
    spec = {
      kafka = {
        version  = "3.7.0"
        replicas = 1
        listeners = [
          {
            name = "plain"
            port = 9092
            type = "internal"
            tls  = false
          },
          {
            name = "external"
            port = 9094
            type = "nodeport"
            tls  = false
          }
        ]
        config = {
          "offsets.topic.replication.factor"         = "1"
          "transaction.state.log.replication.factor" = "1"
          "transaction.state.log.min.isr"            = "1"
        }
        storage = {
          type = "ephemeral"   # dùng persistent cho production
        }
        resources = {
          requests = { memory = "512Mi", cpu = "250m" }
          limits   = { memory = "1Gi",  cpu = "500m" }
        }
      }
      zookeeper = {
        replicas = 1
        storage  = { type = "ephemeral" }
        resources = {
          requests = { memory = "256Mi", cpu = "100m" }
          limits   = { memory = "512Mi", cpu = "250m" }
        }
      }
      entityOperator = {
        topicOperator = {}
        userOperator  = {}
      }
    }
  }
  depends_on = [helm_release.strimzi_operator]
}

# Topics cho từng service
locals {
  kafka_topics = [
    "user-events",
    "order-events",
    "payment-events",
    "notification-events",
  ]
}

resource "kubernetes_manifest" "kafka_topics" {
  for_each = toset(local.kafka_topics)

  manifest = {
    apiVersion = "kafka.strimzi.io/v1beta2"
    kind       = "KafkaTopic"
    metadata = {
      name      = each.key
      namespace = "kafka"
      labels    = { "strimzi.io/cluster" = "kafka-cluster" }
    }
    spec = {
      partitions = 3
      replicas   = 1
      config = {
        "retention.ms"  = "604800000"   # 7 ngày
        "segment.bytes" = "1073741824"
      }
    }
  }
  depends_on = [kubernetes_manifest.kafka_cluster]
}
