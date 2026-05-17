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
