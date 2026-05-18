# Graph Report - .  (2026-05-18)

## Corpus Check
- Corpus is ~15,437 words - fits in a single context window. You may not need a graph.

## Summary
- 264 nodes · 200 edges · 68 communities (41 shown, 27 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 16 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Architecture Guide & Runbook (IMPLEMENT.md)|Architecture Guide & Runbook (IMPLEMENT.md)]]
- [[_COMMUNITY_Payment Microservice (Spring Boot & K8s)|Payment Microservice (Spring Boot & K8s)]]
- [[_COMMUNITY_Kafka Strimzi Messaging Broker & Events|Kafka Strimzi Messaging Broker & Events]]
- [[_COMMUNITY_Frontend TS Config (App)|Frontend TS Config (App)]]
- [[_COMMUNITY_Frontend TS Config (Node)|Frontend TS Config (Node)]]
- [[_COMMUNITY_Frontend Production Dependencies|Frontend Production Dependencies]]
- [[_COMMUNITY_Frontend Dev Dependencies|Frontend Dev Dependencies]]
- [[_COMMUNITY_System Apps & Core Kubernetes Addons|System Apps & Core Kubernetes Addons]]
- [[_COMMUNITY_Frontend Application Code (React)|Frontend Application Code (React)]]
- [[_COMMUNITY_Frontend Kubernetes Deployment & Service|Frontend Kubernetes Deployment & Service]]
- [[_COMMUNITY_KrakenD API Gateway (Base & Deployment)|KrakenD API Gateway (Base & Deployment)]]
- [[_COMMUNITY_User Microservice (Spring Boot & K8s)|User Microservice (Spring Boot & K8s)]]
- [[_COMMUNITY_Frontend Tsconfig Components|Frontend Tsconfig Components]]
- [[_COMMUNITY_System Apps & Core Kubernetes Addons|System Apps & Core Kubernetes Addons]]
- [[_COMMUNITY_Notification Microservice (Spring Boot & K8s)|Notification Microservice (Spring Boot & K8s)]]
- [[_COMMUNITY_Notification Microservice (Spring Boot & K8s)|Notification Microservice (Spring Boot & K8s)]]
- [[_COMMUNITY_Order Microservice (Spring Boot & K8s)|Order Microservice (Spring Boot & K8s)]]
- [[_COMMUNITY_Order Microservice (Spring Boot & K8s)|Order Microservice (Spring Boot & K8s)]]
- [[_COMMUNITY_Payment Microservice (Spring Boot & K8s)|Payment Microservice (Spring Boot & K8s)]]
- [[_COMMUNITY_Payment Microservice (Spring Boot & K8s)|Payment Microservice (Spring Boot & K8s)]]
- [[_COMMUNITY_User Microservice (Spring Boot & K8s)|User Microservice (Spring Boot & K8s)]]
- [[_COMMUNITY_User Microservice (Spring Boot & K8s)|User Microservice (Spring Boot & K8s)]]
- [[_COMMUNITY_Apps Applicationset Components|Apps Applicationset Components]]
- [[_COMMUNITY_System Apps & Core Kubernetes Addons|System Apps & Core Kubernetes Addons]]
- [[_COMMUNITY_KrakenD API Gateway (Base & Deployment)|KrakenD API Gateway (Base & Deployment)]]
- [[_COMMUNITY_Notification Microservice (Spring Boot & K8s)|Notification Microservice (Spring Boot & K8s)]]
- [[_COMMUNITY_Order Microservice (Spring Boot & K8s)|Order Microservice (Spring Boot & K8s)]]
- [[_COMMUNITY_Order Microservice (Spring Boot & K8s)|Order Microservice (Spring Boot & K8s)]]
- [[_COMMUNITY_Payment Microservice (Spring Boot & K8s)|Payment Microservice (Spring Boot & K8s)]]
- [[_COMMUNITY_User Microservice (Spring Boot & K8s)|User Microservice (Spring Boot & K8s)]]
- [[_COMMUNITY_Gitops Overlays Components|Gitops Overlays Components]]
- [[_COMMUNITY_Notification Microservice (Spring Boot & K8s)|Notification Microservice (Spring Boot & K8s)]]
- [[_COMMUNITY_Payment Microservice (Spring Boot & K8s)|Payment Microservice (Spring Boot & K8s)]]
- [[_COMMUNITY_User Microservice (Spring Boot & K8s)|User Microservice (Spring Boot & K8s)]]
- [[_COMMUNITY_PostgreSQL Database Infrastructure|PostgreSQL Database Infrastructure]]
- [[_COMMUNITY_PostgreSQL Database Infrastructure|PostgreSQL Database Infrastructure]]
- [[_COMMUNITY_PostgreSQL Database Infrastructure|PostgreSQL Database Infrastructure]]
- [[_COMMUNITY_PostgreSQL Database Infrastructure|PostgreSQL Database Infrastructure]]
- [[_COMMUNITY_PostgreSQL Database Infrastructure|PostgreSQL Database Infrastructure]]

## God Nodes (most connected - your core abstractions)
1. `IMPLEMENT.md (Architecture Guide)` - 39 edges
2. `compilerOptions` - 17 edges
3. `compilerOptions` - 16 edges
4. `scripts` - 5 edges
5. `Strimzi Kafka Cluster` - 4 edges
6. `NotificationController` - 3 edges
7. `PaymentController` - 3 edges
8. `OrderController` - 3 edges
9. `UserController` - 3 edges
10. `Kafka Topic: user-events` - 3 edges

## Surprising Connections (you probably didn't know these)
- `Service: frontend` --references--> `Deployment: frontend`  [INFERRED]
  gitops/base/frontend/service.yaml → gitops/base/frontend/deployment.yaml
- `Service: notification-service` --references--> `Deployment: notification-service`  [INFERRED]
  gitops/base/notification-service/service.yaml → gitops/base/notification-service/deployment.yaml
- `Service: payment-service` --references--> `Deployment: payment-service`  [INFERRED]
  gitops/base/payment-service/service.yaml → gitops/base/payment-service/deployment.yaml
- `Service: order-service` --references--> `Deployment: order-service`  [INFERRED]
  gitops/base/order-service/service.yaml → gitops/base/order-service/deployment.yaml
- `Service: krakend` --references--> `Deployment: krakend`  [INFERRED]
  gitops/base/krakend/service.yaml → gitops/base/krakend/deployment.yaml

## Communities (68 total, 27 thin omitted)

### Community 0 - "Architecture Guide & Runbook (IMPLEMENT.md)"
Cohesion: 0.05
Nodes (40): 10. Truy cập local & kiểm tra, 11. Mở rộng lên VPS, 12. Production checklist, 1. Cấu trúc thư mục tổng thể, 2. Chuẩn bị môi trường MacBook, 3.1 `infrastructure/terraform/local/providers.tf`, 3.2 `infrastructure/terraform/local/main.tf` — Kind cluster, 3.3 `infrastructure/terraform/local/variables.tf` (+32 more)

### Community 1 - "Payment Microservice (Spring Boot & K8s)"
Cohesion: 0.09
Nodes (16): Docker Image: notification-service:latest, Docker Image: order-service:latest, Docker Image: payment-service:latest, cache_ttl, endpoints, name, output_encoding, port (+8 more)

### Community 2 - "Kafka Strimzi Messaging Broker & Events"
Cohesion: 0.10
Nodes (9): Kafka Topic: notification-events, Kafka Topic: order-events, Kafka Topic: payment-events, Kafka Topic: user-events, Strimzi Kafka Cluster, NotificationController, OrderController, PaymentController (+1 more)

### Community 3 - "Frontend TS Config (App)"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection, moduleResolution (+10 more)

### Community 4 - "Frontend TS Config (Node)"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, moduleResolution, noEmit (+9 more)

### Community 5 - "Frontend Production Dependencies"
Cohesion: 0.15
Nodes (12): dependencies, react, react-dom, name, private, scripts, build, dev (+4 more)

### Community 6 - "Frontend Dev Dependencies"
Cohesion: 0.15
Nodes (13): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals, @types/node, @types/react (+5 more)

### Community 7 - "System Apps & Core Kubernetes Addons"
Cohesion: 0.25
Nodes (7): Application: cert-manager, Application: cert-manager-issuer, Application: ingress-nginx, Application: logging, Application: metallb-config, Application: monitoring, Application: tracing

### Community 8 - "Frontend Application Code (React)"
Cohesion: 0.33
Nodes (3): initialServices, ServiceData, ServiceStatus

### Community 9 - "Frontend Kubernetes Deployment & Service"
Cohesion: 0.40
Nodes (3): Docker Image: frontend:latest, Deployment: frontend, Service: frontend

### Community 10 - "KrakenD API Gateway (Base & Deployment)"
Cohesion: 0.40
Nodes (3): Docker Image: krakend:2.6.0, Deployment: krakend, Service: krakend

### Community 11 - "User Microservice (Spring Boot & K8s)"
Cohesion: 0.40
Nodes (3): Docker Image: user-service:latest, Deployment: user-service, Service: user-service

## Knowledge Gaps
- **100 isolated node(s):** `version`, `name`, `port`, `timeout`, `cache_ttl` (+95 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `devDependencies` connect `Frontend Dev Dependencies` to `Frontend Production Dependencies`?**
  _High betweenness centrality (0.006) - this node is a cross-community bridge._
- **What connects `version`, `name`, `port` to the rest of the system?**
  _139 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Architecture Guide & Runbook (IMPLEMENT.md)` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Should `Payment Microservice (Spring Boot & K8s)` be split into smaller, more focused modules?**
  _Cohesion score 0.08695652173913043 - nodes in this community are weakly interconnected._
- **Should `Kafka Strimzi Messaging Broker & Events` be split into smaller, more focused modules?**
  _Cohesion score 0.10476190476190476 - nodes in this community are weakly interconnected._
- **Should `Frontend TS Config (App)` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Should `Frontend TS Config (Node)` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._