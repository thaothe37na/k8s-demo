# Local Basic Kubernetes Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate a basic routing and execution flow for Kubernetes backend microservices and the React frontend dashboard locally in Kind without requiring running databases or Kafka messaging systems.

**Architecture:** Disable Spring Boot datasource and Kafka auto-configurations at compile time, fix KrakenD's port clash via `enableServiceLinks: false`, deploy the React frontend via ArgoCD ApplicationSet, and implement a local sync bash script to compile, build, and load local Docker images directly into the Kind cluster.

**Tech Stack:** Kubernetes (Kind), Kustomize, ArgoCD, Docker, Spring Boot 4.0.x, React (Vite)

---

### Task 1: Disable Database & Kafka Auto-configurations in Microservices

**Files:**
* Modify: `services/user-service/src/main/java/com/demo/user/UserServiceApplication.java`
* Modify: `services/order-service/src/main/java/com/demo/order/OrderServiceApplication.java`
* Modify: `services/payment-service/src/main/java/com/demo/payment/PaymentServiceApplication.java`
* Modify: `services/notification-service/src/main/java/com/demo/notification/NotificationServiceApplication.java`

- [ ] **Step 1: Modify `UserServiceApplication.java`**
  Add imports and configure the `@SpringBootApplication` annotation to exclude `DataSourceAutoConfiguration`, `HibernateJpaAutoConfiguration`, and `KafkaAutoConfiguration`.
  
  Replace the entire content of `services/user-service/src/main/java/com/demo/user/UserServiceApplication.java` with:
  ```java
  package com.demo.user;

  import org.springframework.boot.SpringApplication;
  import org.springframework.boot.autoconfigure.SpringBootApplication;
  import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration;
  import org.springframework.boot.autoconfigure.orm.jpa.HibernateJpaAutoConfiguration;
  import org.springframework.boot.autoconfigure.kafka.KafkaAutoConfiguration;

  @SpringBootApplication(exclude = {
      DataSourceAutoConfiguration.class,
      HibernateJpaAutoConfiguration.class,
      KafkaAutoConfiguration.class
  })
  public class UserServiceApplication {

  	public static void main(String[] args) {
  		SpringApplication.run(UserServiceApplication.class, args);
  	}

  }
  ```

- [ ] **Step 2: Modify `OrderServiceApplication.java`**
  Replace the entire content of `services/order-service/src/main/java/com/demo/order/OrderServiceApplication.java` with:
  ```java
  package com.demo.order;

  import org.springframework.boot.SpringApplication;
  import org.springframework.boot.autoconfigure.SpringBootApplication;
  import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration;
  import org.springframework.boot.autoconfigure.orm.jpa.HibernateJpaAutoConfiguration;
  import org.springframework.boot.autoconfigure.kafka.KafkaAutoConfiguration;

  @SpringBootApplication(exclude = {
      DataSourceAutoConfiguration.class,
      HibernateJpaAutoConfiguration.class,
      KafkaAutoConfiguration.class
  })
  public class OrderServiceApplication {

  	public static void main(String[] args) {
  		SpringApplication.run(OrderServiceApplication.class, args);
  	}

  }
  ```

- [ ] **Step 3: Modify `PaymentServiceApplication.java`**
  Replace the entire content of `services/payment-service/src/main/java/com/demo/payment/PaymentServiceApplication.java` with:
  ```java
  package com.demo.payment;

  import org.springframework.boot.SpringApplication;
  import org.springframework.boot.autoconfigure.SpringBootApplication;
  import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration;
  import org.springframework.boot.autoconfigure.orm.jpa.HibernateJpaAutoConfiguration;
  import org.springframework.boot.autoconfigure.kafka.KafkaAutoConfiguration;

  @SpringBootApplication(exclude = {
      DataSourceAutoConfiguration.class,
      HibernateJpaAutoConfiguration.class,
      KafkaAutoConfiguration.class
  })
  public class PaymentServiceApplication {

  	public static void main(String[] args) {
  		SpringApplication.run(PaymentServiceApplication.class, args);
  	}

  }
  ```

- [ ] **Step 4: Modify `NotificationServiceApplication.java`**
  Replace the entire content of `services/notification-service/src/main/java/com/demo/notification/NotificationServiceApplication.java` with:
  ```java
  package com.demo.notification;

  import org.springframework.boot.SpringApplication;
  import org.springframework.boot.autoconfigure.SpringBootApplication;
  import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration;
  import org.springframework.boot.autoconfigure.orm.jpa.HibernateJpaAutoConfiguration;
  import org.springframework.boot.autoconfigure.kafka.KafkaAutoConfiguration;

  @SpringBootApplication(exclude = {
      DataSourceAutoConfiguration.class,
      HibernateJpaAutoConfiguration.class,
      KafkaAutoConfiguration.class
  })
  public class NotificationServiceApplication {

  	public static void main(String[] args) {
  		SpringApplication.run(NotificationServiceApplication.class, args);
  	}

  }
  ```

- [ ] **Step 5: Verify compile success for all 4 microservices**
  Verify that we can package these services locally without unit test failures (since they don't have database active now).
  Run:
  ```bash
  (cd services/user-service && ./mvnw clean compile -DskipTests) && \
  (cd services/order-service && ./mvnw clean compile -DskipTests) && \
  (cd services/payment-service && ./mvnw clean compile -DskipTests) && \
  (cd services/notification-service && ./mvnw clean compile -DskipTests)
  ```
  Expected: All builds show "BUILD SUCCESS".

- [ ] **Step 6: Commit Java modifications**
  Run:
  ```bash
  git add services/*/src/main/java/com/demo/*/*Application.java
  git commit -m "refactor: disable JPA and Kafka auto-configurations for basic local run"
  ```

---

### Task 2: Resolve KrakenD API Gateway Crash Loop

**Files:**
* Modify: `gitops/base/krakend/deployment.yaml`

- [ ] **Step 1: Edit `gitops/base/krakend/deployment.yaml`**
  Add the `enableServiceLinks: false` instruction to the Pod Spec at line 16-17 to prevent KrakenD port injection collisions.
  
  Locate lines 15-20:
  ```yaml
        labels:
          app: krakend
      spec:
        containers:
          - name: krakend
  ```
  And replace it with:
  ```yaml
        labels:
          app: krakend
      spec:
        enableServiceLinks: false
        containers:
          - name: krakend
  ```

- [ ] **Step 2: Commit KrakenD fix**
  Run:
  ```bash
  git add gitops/base/krakend/deployment.yaml
  git commit -m "fix: disable service links in KrakenD deployment to prevent port clash"
  ```

---

### Task 3: Integrate React Frontend Service into GitOps

**Files:**
* Modify: `gitops/apps/applicationset.yaml`
* Create: `gitops/overlays/local/frontend/kustomization.yaml`

- [ ] **Step 1: Edit `gitops/apps/applicationset.yaml`**
  Add `frontend` to the ApplicationSet list generator.
  
  Find the list generator block (lines 9-14):
  ```yaml
          elements:
            - service: krakend
            - service: user-service
            - service: order-service
            - service: payment-service
            - service: notification-service
  ```
  Replace it with:
  ```yaml
          elements:
            - service: krakend
            - service: user-service
            - service: order-service
            - service: payment-service
            - service: notification-service
            - service: frontend
  ```

- [ ] **Step 2: Create local overlay for Frontend**
  Create a new file `gitops/overlays/local/frontend/kustomization.yaml` containing the local image registry override.
  
  Write file content:
  ```yaml
  apiVersion: kustomize.config.k8s.io/v1beta1
  kind: Kustomization
  namespace: microservices
  resources:
    - ../../../base/frontend
  images:
    - name: ghcr.io/your-org/frontend
      newName: frontend
      newTag: "latest"
  ```

- [ ] **Step 3: Commit Frontend GitOps configurations**
  Run:
  ```bash
  git add gitops/apps/applicationset.yaml gitops/overlays/local/frontend/kustomization.yaml
  git commit -m "feat: register frontend into GitOps ApplicationSet and create local overlay"
  ```

---

### Task 4: Create Local Synchronize Dev Script

**Files:**
* Create: `scripts/local-dev-sync.sh`

- [ ] **Step 1: Write `scripts/local-dev-sync.sh`**
  Create a new shell script that automates compilation, Docker build, kind loading, and applying Kustomize overlays.
  
  Write file content:
  ```bash
  #!/bin/bash
  set -e

  CLUSTER_NAME="k8s-demo"
  SERVICES=("user-service" "order-service" "payment-service" "notification-service" "frontend")

  echo "=================================================="
  echo "🚀 [Dev Sync] Staring basic local build & sync"
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
  ```

- [ ] **Step 2: Make the script executable**
  Run:
  ```bash
  chmod +x scripts/local-dev-sync.sh
  ```

- [ ] **Step 3: Commit the Dev Sync script**
  Run:
  ```bash
  git add scripts/local-dev-sync.sh
  git commit -m "chore: add shell script for local image build and kind loading"
  ```

---

### Task 5: Deploy, Sync, and Verify the Entire Flow

- [ ] **Step 1: Run the dev sync script to build and load local images**
  Run:
  ```bash
  ./scripts/local-dev-sync.sh
  ```
  Expected: Compiles and builds all 5 Docker images and loads them successfully into Kind.

- [ ] **Step 2: Push changes to GitHub repository**
  Push all commits to the remote repository so ArgoCD can fetch and reconcile.
  Run:
  ```bash
  git push origin main
  ```
  Expected: Git pushes successfully to `origin/main`.

- [ ] **Step 3: Reconcile and Sync inside ArgoCD**
  To speed up reconciliation, force ArgoCD to refresh and synchronize:
  Run:
  ```bash
  kubectl get applications -n argocd -o jsonpath='{.items[*].metadata.name}' | xargs -I {} argocd app sync {} || true
  ```
  Or refresh via ArgoCD Web UI.

- [ ] **Step 4: Verify all Pods are Running and healthy**
  Check that all pods are healthy in `microservices` namespace.
  Run:
  ```bash
  kubectl get pods -n microservices
  ```
  Expected:
  * `krakend`, `user-service`, `order-service`, `payment-service`, `notification-service`, and `frontend` pods all show `Running` (1/1 ready).

- [ ] **Step 5: Verify local routing works through localhost Ingress**
  Verify that we can hit the frontend Actuator dashboard and Backend ping endpoints.
  Run:
  ```bash
  curl -s http://localhost/api/users/ping
  ```
  Expected:
  ```json
  {"service":"user-service","status":"UP","message":"Pong from User Service!"}
  ```
  Run:
  ```bash
  curl -I http://localhost/
  ```
  Expected: `HTTP/1.1 200 OK` (routes successfully to React Frontend index.html).
