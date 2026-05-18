#!/bin/bash
set -e

CLUSTER_NAME="k8s-demo"
SERVICES=("user-service" "order-service" "payment-service" "notification-service" "frontend")

echo "=================================================="
echo "🚀 [Dev Sync] Starting basic local build & sync"
echo "=================================================="

for SERVICE in "${SERVICES[@]}"; do
  echo ""
  echo "📦 Đóng gói & Build Image: $SERVICE..."
  
  if [ "$SERVICE" == "frontend" ]; then
    docker build -t "$SERVICE:latest" services/frontend
  else
    docker build -t "$SERVICE:latest" services/$SERVICE
  fi
  
  echo "📥 Đẩy image $SERVICE vào cụm Kind '$CLUSTER_NAME'..."
  kind load docker-image "$SERVICE:latest" --name "$CLUSTER_NAME"
done

echo ""
echo "=================================================="
echo "✅ Hoàn tất build và load 5 image vào Kind!"
echo "=================================================="
