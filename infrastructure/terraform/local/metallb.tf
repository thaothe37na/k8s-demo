resource "helm_release" "metallb" {
  name             = "metallb"
  repository       = "https://metallb.github.io/metallb"
  chart            = "metallb"
  namespace        = "metallb-system"
  create_namespace = true
  wait             = true
  timeout          = 300

  depends_on = [kind_cluster.main]
}

resource "kubernetes_manifest" "metallb_pool" {
  manifest = {
    apiVersion = "metallb.io/v1beta1"
    kind       = "IPAddressPool"
    metadata = {
      name      = "default-pool"
      namespace = "metallb-system"
    }
    spec = {
      addresses = [
        "172.18.255.200-172.18.255.250"
      ]
    }
  }
  depends_on = [helm_release.metallb]
}

resource "kubernetes_manifest" "metallb_l2" {
  manifest = {
    apiVersion = "metallb.io/v1beta1"
    kind       = "L2Advertisement"
    metadata = {
      name      = "default-l2"
      namespace = "metallb-system"
    }
  }
  depends_on = [kubernetes_manifest.metallb_pool]
}
