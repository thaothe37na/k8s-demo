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
