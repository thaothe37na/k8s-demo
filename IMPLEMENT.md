# IMPLEMENT.md — 5 Spring Boot Microservices trên Kubernetes (GitOps / Production-first)

> **Môi trường demo:** MacBook (Kind cluster) · **GitOps:** ArgoCD + Kustomize · **CI:** GitHub Actions  
> **Infra:** Terraform · **Messaging:** Kafka (Strimzi) · **DB:** PostgreSQL per-service  
> **VPS:** K3s (sẵn sàng mở rộng, không sửa code)

---

## Mục lục

1. [Cấu trúc thư mục tổng thể](#1-cấu-trúc-thư-mục-tổng-thể)
2. [Chuẩn bị môi trường MacBook](#2-chuẩn-bị-môi-trường-macbook)
3. [Terraform — Kind cluster local](#3-terraform--kind-cluster-local)
4. [Terraform — Infrastructure components](#4-terraform--infrastructure-components)
5. [Containerize Spring Boot](#5-containerize-spring-boot)
6. [GitOps repo — Kustomize structure](#6-gitops-repo--kustomize-structure)
7. [ArgoCD ApplicationSet](#7-argocd-applicationset)
8. [CI/CD — GitHub Actions](#8-cicd--github-actions)
9. [Observability stack](#9-observability-stack)
10. [Truy cập local & kiểm tra](#10-truy-cập-local--kiểm-tra)
11. [Mở rộng lên VPS](#11-mở-rộng-lên-vps)
12. [Production checklist](#12-production-checklist)

---

## 1. Cấu trúc thư mục tổng thể

```
.
├── services/                          # Code Spring Boot
│   ├── gateway-service/
│   ├── user-service/
│   ├── order-service/
│   ├── payment-service/
│   └── notification-service/
│
├── infrastructure/
│   └── terraform/
│       ├── local/                     # Kind + toàn bộ stack local
│       │   ├── providers.tf
│       │   ├── main.tf                # Kind cluster
│       │   ├── ingress.tf
│       │   ├── argocd.tf
│       │   ├── monitoring.tf          # Prometheus + Grafana
│       │   ├── logging.tf             # Loki + Promtail
│       │   ├── tracing.tf             # Jaeger
│       │   ├── variables.tf
│       │   ├── outputs.tf
│       │   └── terraform.tfvars
│       └── vps/                       # K3s production
│           ├── providers.tf
│           ├── main.tf
│           └── ...
│
└── gitops/                            # ArgoCD theo dõi repo này
    ├── apps/                          # ArgoCD Application manifests
    │   └── applicationset.yaml
    ├── base/                          # Manifest gốc, không đổi theo môi trường
    │   ├── gateway-service/
    │   ├── user-service/
    │   ├── order-service/
    │   ├── payment-service/
    │   └── notification-service/
    └── overlays/
        ├── local/                     # Overrides cho Kind
        │   ├── gateway-service/
        │   ├── user-service/
        │   ├── ...
        └── production/                # Overrides cho VPS/K3s
            ├── gateway-service/
            ├── user-service/
            └── ...
```

---

## 2. Chuẩn bị môi trường MacBook

```bash
# Homebrew (nếu chưa có)
# /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Tất cả tools cần thiết
# brew install --cask docker
brew install kubectl helm terraform kind argocd gh yq

# Verify
docker version && kubectl version --client && helm version && terraform version && kind version
```

<!-- > **RAM tối thiểu cho Docker Desktop:** 8 GB (khuyến nghị 12 GB để chạy đủ Kafka + 5 DB + monitoring)   -->
> **CPU:** Cấp ít nhất 4 cores trong Docker Desktop → Settings → Resources

---

## 3. Terraform — Kind cluster local

### 3.1 `infrastructure/terraform/local/providers.tf`

```hcl
terraform {
  required_version = ">= 1.7"
  required_providers {
    kind = {
      source  = "tehcyx/kind"
      version = "0.4.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "kind" {}

# Dùng locals để DRY — tránh lặp lại cluster credentials
locals {
  kube_host      = kind_cluster.main.endpoint
  kube_cert      = kind_cluster.main.client_certificate
  kube_key       = kind_cluster.main.client_key
  kube_ca        = kind_cluster.main.cluster_ca_certificate
}

provider "helm" {
  kubernetes {
    host                   = local.kube_host
    client_certificate     = local.kube_cert
    client_key             = local.kube_key
    cluster_ca_certificate = local.kube_ca
  }
}

provider "kubernetes" {
  host                   = local.kube_host
  client_certificate     = local.kube_cert
  client_key             = local.kube_key
  cluster_ca_certificate = local.kube_ca
}
```

### 3.2 `infrastructure/terraform/local/main.tf` — Kind cluster

```hcl
# FIX: thêm extraPortMappings để ingress expose ra localhost đúng cách
resource "kind_cluster" "main" {
  name            = var.cluster_name
  node_image      = "kindest/node:v1.29.0"
  wait_for_ready  = true

  kind_config = <<-EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 30080
    hostPort: 80
    protocol: TCP
  - containerPort: 30443
    hostPort: 443
    protocol: TCP
  - containerPort: 30081
    hostPort: 8080
    protocol: TCP
- role: worker
- role: worker
EOF
}
```

### 3.3 `infrastructure/terraform/local/variables.tf`

```hcl
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
```

### 3.4 `infrastructure/terraform/local/terraform.tfvars`

```hcl
cluster_name          = "k8s-demo"
argocd_admin_password = "changeme_local_only"
gitops_repo_url       = "https://github.com/your-org/gitops"
docker_registry       = "ghcr.io/your-org"
```

---

## 4. Terraform — Infrastructure components

### 4.1 `infrastructure/terraform/local/ingress.tf`

```hcl
resource "helm_release" "ingress_nginx" {
  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  chart            = "ingress-nginx"
  namespace        = "ingress-nginx"
  create_namespace = true
  wait             = true
  timeout          = 300

  set { name = "controller.service.type";                    value = "NodePort" }
  set { name = "controller.hostPort.enabled";                value = "true" }
  set { name = "controller.service.nodePorts.http";          value = "30080" }
  set { name = "controller.service.nodePorts.https";         value = "30443" }
  set { name = "controller.tolerations[0].key";              value = "node-role.kubernetes.io/control-plane" }
  set { name = "controller.tolerations[0].operator";         value = "Equal" }
  set { name = "controller.tolerations[0].effect";           value = "NoSchedule" }
  set { name = "controller.nodeSelector.ingress-ready";      value = "true" }

  depends_on = [kind_cluster.main]
}

resource "helm_release" "cert_manager" {
  name             = "cert-manager"
  repository       = "https://charts.jetstack.io"
  chart            = "cert-manager"
  namespace        = "cert-manager"
  create_namespace = true
  wait             = true
  timeout          = 300

  set { name = "installCRDs"; value = "true" }

  depends_on = [kind_cluster.main]
}

# Self-signed ClusterIssuer cho local
resource "kubernetes_manifest" "selfsigned_issuer" {
  manifest = {
    apiVersion = "cert-manager.io/v1"
    kind       = "ClusterIssuer"
    metadata   = { name = "selfsigned-issuer" }
    spec       = { selfSigned = {} }
  }
  depends_on = [helm_release.cert_manager]
}
```

### 4.2 `infrastructure/terraform/local/argocd.tf`

```hcl
resource "random_password" "argocd" {
  length  = 16
  special = false
}

# FIX: dùng random_password + bcrypt thay vì hardcode placeholder
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
    server.insecure: true       # local only — bỏ khi production
  secret:
    argocdServerAdminPassword: "${bcrypt(var.argocd_admin_password)}"
EOF
  ]

  depends_on = [kind_cluster.main]
}
```

### 4.3 `infrastructure/terraform/local/kafka.tf` ← **MỚI**

```hcl
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

# Topics cho từng service (thêm/bớt tuỳ domain)
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
```

### 4.4 `infrastructure/terraform/local/databases.tf` ← **MỚI**

```hcl
locals {
  services = {
    "gateway"      = { db = "gateway_db",      port = 5432 }
    "user"         = { db = "user_db",         port = 5433 }
    "order"        = { db = "order_db",        port = 5434 }
    "payment"      = { db = "payment_db",      port = 5435 }
    "notification" = { db = "notification_db", port = 5436 }
  }
}

resource "random_password" "db" {
  for_each = local.services
  length   = 20
  special  = false
}

# 1 PostgreSQL instance riêng cho từng service — Database per Service pattern
resource "helm_release" "postgresql" {
  for_each = local.services

  name             = "postgres-${each.key}"
  repository       = "https://charts.bitnami.com/bitnami"
  chart            = "postgresql"
  namespace        = "databases"
  create_namespace = true
  wait             = true
  timeout          = 300

  set { name = "auth.database";         value = each.value.db }
  set { name = "auth.username";         value = "${each.key}_user" }
  set { name = "auth.password";         value = random_password.db[each.key].result }
  set { name = "primary.resources.requests.memory"; value = "128Mi" }
  set { name = "primary.resources.requests.cpu";    value = "100m" }
  set { name = "primary.resources.limits.memory";   value = "256Mi" }
  set { name = "primary.resources.limits.cpu";      value = "200m" }
  # Lưu credentials vào Secret để Spring Boot đọc
  set { name = "primary.extraEnvVars[0].name";  value = "POSTGRES_DB" }
  set { name = "primary.extraEnvVars[0].value"; value = each.value.db }

  depends_on = [kind_cluster.main]
}

# Tạo K8s Secret chứa DB URL cho từng service — Spring Boot đọc qua envFrom
resource "kubernetes_secret" "db_credentials" {
  for_each = local.services

  metadata {
    name      = "${each.key}-db-secret"
    namespace = "microservices"
  }

  data = {
    DB_URL      = "jdbc:postgresql://postgres-${each.key}-postgresql.databases.svc.cluster.local:5432/${each.value.db}"
    DB_USERNAME = "${each.key}_user"
    DB_PASSWORD = random_password.db[each.key].result
  }

  depends_on = [helm_release.postgresql]
}

# Lưu passwords ra output để debug (sensitive)
output "db_passwords" {
  value     = { for k, v in random_password.db : k => v.result }
  sensitive = true
}
```

### 4.5 `infrastructure/terraform/local/monitoring.tf`

```hcl
resource "helm_release" "monitoring" {
  name             = "monitoring"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  namespace        = "monitoring"
  create_namespace = true
  wait             = true
  timeout          = 600

  values = [<<-EOF
grafana:
  adminPassword: "admin"
  service:
    type: NodePort
    nodePort: 30082
  sidecar:
    datasources:
      enabled: true
prometheus:
  prometheusSpec:
    # Scrape tất cả ServiceMonitor trong mọi namespace
    serviceMonitorSelectorNilUsesHelmValues: false
    podMonitorSelectorNilUsesHelmValues: false
    retention: 7d
    resources:
      requests:
        memory: "512Mi"
        cpu: "250m"
      limits:
        memory: "1Gi"
        cpu: "500m"
EOF
  ]

  depends_on = [kind_cluster.main]
}
```

### 4.6 `infrastructure/terraform/local/logging.tf`

```hcl
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
  # FIX: Loki dùng ClusterIP, Grafana truy cập nội bộ qua service discovery
  service:
    type: ClusterIP
    port: 3100
  persistence:
    enabled: false   # true khi production
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
```

### 4.7 `infrastructure/terraform/local/tracing.tf` ← **MỚI**

```hcl
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
```

### 4.8 `infrastructure/terraform/local/outputs.tf`

```hcl
output "kubeconfig_command" {
  value = "kind export kubeconfig --name ${var.cluster_name}"
}

output "argocd_url"  { value = "http://localhost:8080" }
output "grafana_url" { value = "http://localhost:30082 (admin/admin)" }
output "app_url"     { value = "http://localhost/api/..." }

output "kafka_bootstrap" {
  value = "kafka-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092"
}
```

### 4.9 Khởi tạo cluster

```bash
cd infrastructure/terraform/local

terraform init
terraform plan
terraform apply -auto-approve

# Export kubeconfig
kind export kubeconfig --name k8s-demo

# Verify
kubectl get nodes
kubectl get pods -A

# Xem mật khẩu DB (nếu cần debug)
terraform output -json db_passwords
```

---

## 5. Containerize Spring Boot

### 5.1 `Dockerfile` (mỗi service dùng template này)

```dockerfile
# Stage 1: Build
FROM eclipse-temurin:17-jdk-alpine AS builder
WORKDIR /app
COPY mvnw pom.xml ./
COPY .mvn .mvn
# Cache dependencies riêng để layer không bị invalidate mỗi lần build
RUN chmod +x mvnw && ./mvnw dependency:go-offline -q
COPY src src
RUN ./mvnw package -DskipTests -q

# Stage 2: Runtime — image tối giản, non-root
FROM eclipse-temurin:17-jre-alpine
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar
RUN chown appuser:appgroup app.jar
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://localhost:8080/actuator/health/liveness || exit 1
ENTRYPOINT ["java", \
  "-XX:MaxRAMPercentage=75.0", \
  "-XX:+UseContainerSupport", \
  "-Djava.security.egd=file:/dev/./urandom", \
  "-jar", "app.jar"]
```

### 5.2 `pom.xml` — Dependencies cần thiết

```xml
<!-- Actuator: health probes + metrics endpoint -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>

<!-- Prometheus metrics -->
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-registry-prometheus</artifactId>
</dependency>

<!-- OpenTelemetry tracing (Jaeger) -->
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-tracing-bridge-otel</artifactId>
</dependency>
<dependency>
    <groupId>io.opentelemetry.instrumentation</groupId>
    <artifactId>opentelemetry-spring-boot-starter</artifactId>
    <version>2.4.0-alpha</version>
</dependency>

<!-- Kafka -->
<dependency>
    <groupId>org.springframework.kafka</groupId>
    <artifactId>spring-kafka</artifactId>
</dependency>
```

### 5.3 `src/main/resources/application.yml`

```yaml
spring:
  application:
    name: ${SERVICE_NAME:user-service}

  datasource:
    url: ${DB_URL}                      # inject từ K8s Secret
    username: ${DB_USERNAME}
    password: ${DB_PASSWORD}
    hikari:
      maximum-pool-size: 5
      minimum-idle: 2

  kafka:
    bootstrap-servers: ${KAFKA_BOOTSTRAP_SERVERS:kafka-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092}
    producer:
      key-serializer: org.apache.kafka.common.serialization.StringSerializer
      value-serializer: org.springframework.kafka.support.serializer.JsonSerializer
    consumer:
      group-id: ${spring.application.name}
      auto-offset-reset: earliest
      key-deserializer: org.apache.kafka.common.serialization.StringDeserializer
      value-deserializer: org.springframework.kafka.support.serializer.JsonDeserializer

management:
  endpoints:
    web:
      exposure:
        include: health, metrics, prometheus, info
  endpoint:
    health:
      probes:
        enabled: true        # /actuator/health/liveness + /readiness
      show-details: always
  metrics:
    tags:
      application: ${spring.application.name}
      environment: ${ENVIRONMENT:local}

# Tracing → Jaeger
management.tracing:
  sampling.probability: 1.0   # 100% cho demo; giảm xuống 0.1 cho production

logging:
  pattern:
    console: "%d{ISO8601} [%thread] %-5level %logger{36} traceId=%X{traceId} - %msg%n"
```

### 5.4 `gateway-service/application.yml` — Routing

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: http://user-service.microservices.svc.cluster.local:80
          predicates:
            - Path=/api/users/**
          filters:
            - StripPrefix=1
        - id: order-service
          uri: http://order-service.microservices.svc.cluster.local:80
          predicates:
            - Path=/api/orders/**
          filters:
            - StripPrefix=1
        - id: payment-service
          uri: http://payment-service.microservices.svc.cluster.local:80
          predicates:
            - Path=/api/payments/**
          filters:
            - StripPrefix=1
        - id: notification-service
          uri: http://notification-service.microservices.svc.cluster.local:80
          predicates:
            - Path=/api/notifications/**
          filters:
            - StripPrefix=1
```

---

## 6. GitOps repo — Kustomize structure

### 6.1 `gitops/base/<service-name>/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  labels:
    app: user-service
    version: "1.0"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/actuator/prometheus"
    spec:
      # FIX: imagePullSecrets cho private registry (GHCR)
      imagePullSecrets:
        - name: ghcr-secret
      containers:
        - name: user-service
          image: ghcr.io/your-org/user-service:latest   # CI sẽ update tag này
          ports:
            - containerPort: 8080
          envFrom:
            - secretRef:
                name: user-db-secret         # DB credentials từ Terraform
            - configMapRef:
                name: user-service-config
          env:
            - name: SERVICE_NAME
              value: "user-service"
            - name: ENVIRONMENT
              valueFrom:
                fieldRef:
                  fieldPath: metadata.namespace
          livenessProbe:
            httpGet:
              path: /actuator/health/liveness
              port: 8080
            initialDelaySeconds: 60
            periodSeconds: 15
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /actuator/health/readiness
              port: 8080
            initialDelaySeconds: 20
            periodSeconds: 10
            failureThreshold: 3
          resources:
            requests:
              memory: "256Mi"
              cpu: "200m"
            limits:
              memory: "512Mi"
              cpu: "500m"
```

### 6.2 `gitops/base/<service-name>/service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: user-service
spec:
  selector:
    app: user-service
  ports:
    - name: http
      port: 80
      targetPort: 8080
```

### 6.3 `gitops/base/<service-name>/configmap.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: user-service-config
data:
  KAFKA_BOOTSTRAP_SERVERS: "kafka-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092"
  OTEL_EXPORTER_OTLP_ENDPOINT: "http://jaeger-collector.tracing.svc.cluster.local:4318"
  SPRING_PROFILES_ACTIVE: "kubernetes"
```

### 6.4 `gitops/base/<service-name>/hpa.yaml`

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: user-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: user-service
  minReplicas: 1
  maxReplicas: 5
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### 6.5 `gitops/base/<service-name>/kustomization.yaml`

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml
  - hpa.yaml
```

### 6.6 `gitops/overlays/local/<service-name>/kustomization.yaml`

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: microservices
resources:
  - ../../../base/user-service
images:
  - name: ghcr.io/your-org/user-service
    newTag: "latest"                      # CI tự động update dòng này
```

### 6.7 `gitops/overlays/local/ingress.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: microservices-ingress
  namespace: microservices
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
    cert-manager.io/cluster-issuer: selfsigned-issuer
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - localhost
      secretName: local-tls
  rules:
    - host: localhost
      http:
        paths:
          # Gateway nhận tất cả /api/* và route nội bộ
          - path: /api(/|$)(.*)
            pathType: ImplementationSpecific
            backend:
              service:
                name: gateway-service
                port:
                  number: 80
          # ArgoCD UI
          - path: /argocd(/|$)(.*)
            pathType: ImplementationSpecific
            backend:
              service:
                name: argocd-server
                port:
                  number: 80
```

---

## 7. ArgoCD ApplicationSet

### `gitops/apps/applicationset.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: microservices
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - service: gateway-service
          - service: user-service
          - service: order-service
          - service: payment-service
          - service: notification-service
  template:
    metadata:
      name: "{{service}}"
      annotations:
        notifications.argoproj.io/subscribe.on-sync-failed.slack: dev-alerts
    spec:
      project: default
      source:
        repoURL: https://github.com/your-org/gitops
        targetRevision: main
        path: "overlays/local/{{service}}"
      destination:
        server: https://kubernetes.default.svc
        namespace: microservices
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
          allowEmpty: false
        syncOptions:
          - CreateNamespace=true
          - ServerSideApply=true
        retry:
          limit: 3
          backoff:
            duration: 5s
            factor: 2
            maxDuration: 3m
```

### Áp dụng ApplicationSet

```bash
# Đăng nhập ArgoCD
argocd login localhost:8080 --username admin --password changeme_local_only --insecure

# Apply ApplicationSet
kubectl apply -f gitops/apps/applicationset.yaml

# Theo dõi sync status
argocd app list
argocd app get user-service
```

---

## 8. CI/CD — GitHub Actions

### `services/user-service/.github/workflows/ci.yml`

```yaml
name: CI — user-service

on:
  push:
    branches: [main]
    paths:
      - "services/user-service/**"
  pull_request:
    paths:
      - "services/user-service/**"

env:
  SERVICE: user-service
  REGISTRY: ghcr.io
  IMAGE: ghcr.io/${{ github.repository_owner }}/user-service

jobs:
  # ── Job 1: Build + Test ─────────────────────────────────────────
  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "17"
          cache: maven

      - name: Build & test
        working-directory: services/user-service
        run: ./mvnw verify -q

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: services/user-service/target/surefire-reports/

  # ── Job 2: Build & Push Docker image ────────────────────────────
  docker:
    needs: build-test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write        # cần để push lên GHCR
    outputs:
      image_tag: ${{ steps.meta.outputs.tags }}
      image_digest: ${{ steps.push.outputs.digest }}

    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract image metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.IMAGE }}
          tags: |
            type=sha,prefix=,format=short
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push
        id: push
        uses: docker/build-push-action@v5
        with:
          context: services/user-service
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      # Optional: quét vulnerability
      - name: Scan image with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.IMAGE }}:${{ github.sha }}
          format: table
          exit-code: "0"       # set "1" nếu muốn fail pipeline khi tìm thấy lỗi HIGH

  # ── Job 3: Update GitOps repo ────────────────────────────────────
  # FIX: checkout manifest repo đúng cách với token riêng
  update-gitops:
    needs: docker
    runs-on: ubuntu-latest
    steps:
      - name: Checkout GitOps repo
        uses: actions/checkout@v4
        with:
          repository: your-org/gitops
          token: ${{ secrets.GITOPS_PAT }}     # Personal Access Token có quyền write vào gitops repo
          path: gitops

      - name: Update image tag
        run: |
          SHORT_SHA=$(echo "${{ github.sha }}" | cut -c1-7)
          cd gitops
          # dùng yq để update đúng field, không dùng sed dễ sai
          yq e ".images[0].newTag = \"${SHORT_SHA}\"" \
            -i overlays/local/user-service/kustomization.yaml

      - name: Commit and push
        run: |
          SHORT_SHA=$(echo "${{ github.sha }}" | cut -c1-7)
          cd gitops
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add overlays/local/user-service/kustomization.yaml
          git diff --staged --quiet || \
            git commit -m "ci: update user-service image to ${SHORT_SHA} [skip ci]"
          git push
```

> **Lưu ý secrets cần cấu hình trong GitHub:**
> - `GITOPS_PAT` — Personal Access Token có quyền `repo` write vào gitops repo
> - `GITHUB_TOKEN` — tự động có sẵn (cho GHCR push)

---

## 9. Observability stack

### 9.1 Grafana datasources

Sau khi Grafana lên, thêm 2 datasources:

| Datasource | URL |
|---|---|
| Prometheus | `http://monitoring-kube-prometheus-prometheus.monitoring:9090` |
| Loki       | `http://loki.logging:3100` |
| Jaeger     | `http://jaeger-query.tracing:80` |

### 9.2 ServiceMonitor cho Spring Boot

```yaml
# gitops/base/user-service/servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: user-service-monitor
  labels:
    release: monitoring      # match với kube-prometheus-stack label
spec:
  selector:
    matchLabels:
      app: user-service
  endpoints:
    - port: http
      path: /actuator/prometheus
      interval: 15s
```

### 9.3 Grafana dashboards nên import

| Dashboard ID | Tên |
|---|---|
| 4701 | JVM Micrometer |
| 17175 | Spring Boot Observability |
| 15141 | Kafka Overview (Strimzi) |
| 9628 | PostgreSQL Database |
| 315 | Kubernetes cluster monitoring |

```bash
# Port-forward Grafana nếu không qua Ingress
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
open http://localhost:3000
```

---

## 10. Truy cập local & kiểm tra

```bash
# Cluster status
kubectl get nodes
kubectl get pods -A

# Microservices
kubectl get pods -n microservices
kubectl get ingress -n microservices

# Theo dõi log một service
kubectl logs -n microservices -l app=user-service -f

# Test API qua ingress
curl http://localhost/api/users/health
curl http://localhost/api/orders/health

# Kafka — kiểm tra topic
kubectl -n kafka exec -it kafka-cluster-kafka-0 -- \
  bin/kafka-topics.sh --bootstrap-server localhost:9092 --list

# ArgoCD — xem trạng thái sync
argocd app list
argocd app sync user-service     # manual sync nếu cần

# Xem DB connection
kubectl get secret user-db-secret -n microservices -o jsonpath='{.data.DB_URL}' | base64 -d
```

---

## 11. Mở rộng lên VPS

Khi mày sẵn sàng chuyển lên VPS, **không sửa gì trong code services**, chỉ:

### Bước 1 — Cài K3s lên VPS

```bash
# SSH vào VPS rồi chạy
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable traefik" sh -

# Copy kubeconfig về MacBook
scp root@your-vps-ip:/etc/rancher/k3s/k3s.yaml ~/.kube/config-vps
sed -i 's/127.0.0.1/your-vps-ip/g' ~/.kube/config-vps
export KUBECONFIG=~/.kube/config-vps
```

### Bước 2 — Chạy Terraform cho VPS

`infrastructure/terraform/vps/` — giữ nguyên cấu trúc, chỉ thay:

```hcl
# Thay provider kind → kubernetes remote
provider "kubernetes" {
  config_path = "~/.kube/config-vps"
}

# cert-manager dùng Let's Encrypt thay self-signed
resource "kubernetes_manifest" "letsencrypt_issuer" {
  manifest = {
    apiVersion = "cert-manager.io/v1"
    kind       = "ClusterIssuer"
    metadata   = { name = "letsencrypt-prod" }
    spec = {
      acme = {
        server = "https://acme-v02.api.letsencrypt.org/directory"
        email  = "your-email@domain.com"
        privateKeySecretRef = { name = "letsencrypt-prod" }
        solvers = [{ http01 = { ingress = { class = "nginx" } } }]
      }
    }
  }
}
```

### Bước 3 — Tạo overlay production

```bash
# overlays/production/user-service/kustomization.yaml
# Chỉ thay: domain thật, TLS issuer, resource cao hơn
```

### Bước 4 — Apply ApplicationSet production

```yaml
# Thay path: overlays/local → overlays/production
# ArgoCD tự sync toàn bộ
```

---

## 12. Production checklist

| Hạng mục | Tool | Trạng thái |
|---|---|---|
| Network Policies | Cilium / Calico | ☐ |
| Pod Security Admission | Baseline profile | ☐ |
| Secrets management | Sealed Secrets hoặc External Secrets + Vault | ☐ |
| Image vulnerability scan | Trivy trong CI | ☐ |
| Pod Disruption Budget | PDB per Deployment | ☐ |
| Horizontal Pod Autoscaler | HPA (đã có base manifest) | ✓ |
| Anti-affinity rules | topologySpreadConstraints | ☐ |
| ResourceQuota + LimitRange | Per namespace | ☐ |
| Backup | Velero | ☐ |
| Distributed tracing | OpenTelemetry + Jaeger (đã có) | ✓ |
| Kafka persistence | Strimzi + PVC | ☐ production |
| DB persistence | PostgreSQL + PVC | ☐ production |
| Chaos testing | LitmusChaos | ☐ |
| Multi-replica services | replicas ≥ 2 | ☐ production |

---

## Quick start — TL;DR

```bash
# 1. Clone repos
git clone https://github.com/your-org/services
git clone https://github.com/your-org/gitops

# 2. Dựng cluster + toàn bộ infra (~10 phút)
cd services/infrastructure/terraform/local
terraform init && terraform apply -auto-approve
kind export kubeconfig --name k8s-demo

# 3. Đăng nhập ArgoCD
argocd login localhost:8080 --username admin --password changeme_local_only --insecure

# 4. Apply ApplicationSet → ArgoCD tự deploy 5 services
kubectl apply -f ../../gitops/apps/applicationset.yaml

# 5. Theo dõi
watch kubectl get pods -n microservices

# 6. Test
curl http://localhost/api/users/health
```

> Từ bước này trở đi, mỗi lần `git push` lên `services/`, GitHub Actions build xong → tự update `gitops/` → ArgoCD phát hiện trong 3 phút → deploy tự động. Không cần làm gì thêm.
