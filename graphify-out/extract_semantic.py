import json
import re
import os
import yaml
from pathlib import Path

def clean(s):
    if not s:
        return ""
    s_clean = "".join(c if c.isalnum() or c == '_' else '_' for c in s.lower())
    # replace duplicate underscores
    s_clean = re.sub('_+', '_', s_clean)
    return s_clean.strip('_')

def make_id(relative_path, entity_name):
    path_parts = Path(relative_path).parts
    parent_dir = path_parts[-2] if len(path_parts) > 1 else ""
    filename_stem = Path(relative_path).stem
    
    stem_parts = []
    if parent_dir:
        stem_parts.append(clean(parent_dir))
    stem_parts.append(clean(filename_stem))
    
    stem = "_".join(stem_parts)
    entity = clean(entity_name)
    
    return f"{stem}_{entity}"

def make_file_id(relative_path):
    p = relative_path.lower()
    cleaned = "".join(c if c.isalnum() or c == '_' else '_' for c in p)
    cleaned = re.sub('_+', '_', cleaned)
    return cleaned.strip('_')

def run_extraction():
    detect_path = Path("graphify-out/.graphify_detect.json")
    if not detect_path.exists():
        print("Error: detect.json not found")
        return
        
    detect = json.loads(detect_path.read_text(encoding="utf-8"))
    
    nodes = []
    edges = []
    hyperedges = []
    
    # Store mapped entities to resolve connections
    k8s_deployments = {} # name -> id
    k8s_services = {}    # name -> id
    databases = {}       # name -> id
    kafka_topics = ["user-events", "order-events", "payment-events", "notification-events"]
    
    # First, let's define standard infrastructural nodes to connect to
    # Kafka broker
    kafka_broker_id = "infra_strimzi_kafka_cluster"
    nodes.append({
        "id": kafka_broker_id,
        "label": "Strimzi Kafka Cluster",
        "file_type": "concept",
        "source_file": "infrastructure/terraform/local/kafka.tf",
        "source_location": "L306",
        "source_url": None,
        "captured_at": None,
        "author": None,
        "contributor": None
    })
    
    # Kafka topics
    for topic in kafka_topics:
        topic_id = f"infra_kafka_topic_{clean(topic)}"
        nodes.append({
            "id": topic_id,
            "label": f"Kafka Topic: {topic}",
            "file_type": "concept",
            "source_file": "infrastructure/terraform/local/kafka.tf",
            "source_location": "L380"
        })
        edges.append({
            "source": topic_id,
            "target": kafka_broker_id,
            "relation": "references",
            "confidence": "EXTRACTED",
            "confidence_score": 1.0,
            "source_file": "infrastructure/terraform/local/kafka.tf"
        })
        
    # Databases
    db_names = ["gateway_db", "user_db", "order_db", "payment_db", "notification_db"]
    for db in db_names:
        db_id = f"infra_postgresql_{clean(db)}"
        databases[db] = db_id
        nodes.append({
            "id": db_id,
            "label": f"PostgreSQL DB: {db}",
            "file_type": "concept",
            "source_file": "infrastructure/terraform/local/databases.tf",
            "source_location": "L416"
        })

    # Read uncached files to parse
    uncached_path = Path("graphify-out/.graphify_uncached.txt")
    if not uncached_path.exists():
        print("Error: uncached.txt not found")
        return
        
    uncached_files = uncached_path.read_text(encoding="utf-8").splitlines()
    
    # Track images and other files
    for filepath in uncached_files:
        # absolute to relative
        rel_path = os.path.relpath(filepath, os.getcwd())
        file_id = make_file_id(rel_path)
        
        path_obj = Path(rel_path)
        suffix = path_obj.suffix.lower()
        
        if suffix in [".png", ".jpg", ".jpeg", ".svg", ".webp"]:
            # Image node
            nodes.append({
                "id": file_id,
                "label": path_obj.name,
                "file_type": "image",
                "source_file": rel_path
            })
            continue
            
        if not path_obj.exists():
            continue
            
        content = path_obj.read_text(encoding="utf-8", errors="ignore")
        
        if rel_path == "IMPLEMENT.md":
            # Parent node
            nodes.append({
                "id": file_id,
                "label": "IMPLEMENT.md (Architecture Guide)",
                "file_type": "document",
                "source_file": rel_path
            })
            # Parse sections as rationale
            sections = re.findall(r"^(##\s+\d+\.\s+.*?)$|^(###\s+\d+\.\d+\s+.*?)$", content, re.MULTILINE)
            for sec in sections:
                sec_title = sec[0] or sec[1]
                if not sec_title:
                    continue
                clean_title = re.sub(r"^#+\s+", "", sec_title).strip()
                sec_id = make_id(rel_path, clean_title[:40])
                nodes.append({
                    "id": sec_id,
                    "label": clean_title,
                    "file_type": "rationale",
                    "source_file": rel_path
                })
                edges.append({
                    "source": sec_id,
                    "target": file_id,
                    "relation": "rationale_for",
                    "confidence": "EXTRACTED",
                    "confidence_score": 1.0,
                    "source_file": rel_path
                })
            continue

        if suffix in [".yaml", ".yml"]:
            # Parse Kubernetes Manifests
            nodes.append({
                "id": file_id,
                "label": path_obj.name,
                "file_type": "document",
                "source_file": rel_path
            })
            
            try:
                documents = list(yaml.safe_load_all(content))
            except Exception as e:
                print(f"Skipping malformed YAML {rel_path}: {e}")
                continue
                
            for doc in documents:
                if not doc or not isinstance(doc, dict):
                    continue
                kind = doc.get("kind")
                metadata = doc.get("metadata", {})
                name = metadata.get("name")
                if not kind or not name:
                    continue
                
                # Make a node for the Kubernetes resource
                resource_id = make_id(rel_path, f"{kind}_{name}")
                nodes.append({
                    "id": resource_id,
                    "label": f"{kind}: {name}",
                    "file_type": "document",
                    "source_file": rel_path
                })
                
                # Connect resource to its container file
                edges.append({
                    "source": resource_id,
                    "target": file_id,
                    "relation": "references",
                    "confidence": "EXTRACTED",
                    "confidence_score": 1.0,
                    "source_file": rel_path
                })
                
                # Extract connections based on resource type
                if kind == "Deployment":
                    k8s_deployments[name] = resource_id
                    # Check container images & env vars
                    spec = doc.get("spec", {})
                    template = spec.get("template", {})
                    temp_spec = template.get("spec", {})
                    containers = temp_spec.get("containers", [])
                    for container in containers:
                        image = container.get("image", "")
                        if image:
                            # Connect to image concept
                            image_concept_id = f"concept_image_{clean(image.split('/')[-1])}"
                            if image_concept_id not in [n["id"] for n in nodes]:
                                nodes.append({
                                    "id": image_concept_id,
                                    "label": f"Docker Image: {image.split('/')[-1]}",
                                    "file_type": "concept",
                                    "source_file": rel_path
                                })
                            edges.append({
                                "source": resource_id,
                                "target": image_concept_id,
                                "relation": "references",
                                "confidence": "EXTRACTED",
                                "confidence_score": 1.0,
                                "source_file": rel_path
                            })
                            
                elif kind == "Service":
                    k8s_services[name] = resource_id
                    # Service selector to Deployment selector
                    spec = doc.get("spec", {})
                    selector = spec.get("selector", {})
                    if selector:
                        # Find matching Deployment
                        for dep_name, dep_id in k8s_deployments.items():
                            if dep_name in name or name in dep_name:
                                edges.append({
                                    "source": resource_id,
                                    "target": dep_id,
                                    "relation": "references",
                                    "confidence": "INFERRED",
                                    "confidence_score": 0.85,
                                    "source_file": rel_path
                                })
                                
                elif kind == "Ingress":
                    # Parse rules
                    spec = doc.get("spec", {})
                    rules = spec.get("rules", [])
                    for rule in rules:
                        http = rule.get("http", {})
                        paths = http.get("paths", [])
                        for p in paths:
                            backend = p.get("backend", {})
                            service_info = backend.get("service", {})
                            svc_name = service_info.get("name")
                            if svc_name:
                                # We route to this Service
                                svc_id = make_id(rel_path, f"Service_{svc_name}")
                                edges.append({
                                    "source": resource_id,
                                    "target": svc_id,
                                    "relation": "calls",
                                    "confidence": "EXTRACTED",
                                    "confidence_score": 1.0,
                                    "source_file": rel_path
                                })
                                
                elif kind == "Kustomization":
                    # Kustomization references resources
                    resources = doc.get("resources", [])
                    for r in resources:
                        # Connect Kustomization to references
                        edges.append({
                            "source": resource_id,
                            "target": file_id, # link to resources
                            "relation": "references",
                            "confidence": "EXTRACTED",
                            "confidence_score": 1.0,
                            "source_file": rel_path
                        })
                        
                elif kind == "ApplicationSet":
                    spec = doc.get("spec", {})
                    template = spec.get("template", {})
                    temp_spec = template.get("spec", {})
                    source = temp_spec.get("source", {})
                    path = source.get("path", "")
                    if path:
                        # Link to GitOps path
                        edges.append({
                            "source": resource_id,
                            "target": file_id,
                            "relation": "references",
                            "confidence": "EXTRACTED",
                            "confidence_score": 1.0,
                            "source_file": rel_path
                        })

        elif suffix == ".json" and "krakend.json" in rel_path:
            # Parse KrakenD endpoints and connect to microservices!
            nodes.append({
                "id": file_id,
                "label": "krakend.json (API Gateway Configuration)",
                "file_type": "code",
                "source_file": rel_path
            })
            
            try:
                krakend_data = json.loads(content)
            except Exception as e:
                print(f"Skipping malformed krakend.json: {e}")
                continue
                
            endpoints = krakend_data.get("endpoints", [])
            for ep in endpoints:
                endpoint_path = ep.get("endpoint", "")
                backends = ep.get("backend", [])
                for b in backends:
                    host = b.get("host", [])
                    url_pattern = b.get("url_pattern", "")
                    # Identify which backend service it calls
                    for h in host:
                        # e.g., http://user-service.microservices.svc.cluster.local
                        match = re.search(r"http://([a-zA-Z0-9\-]+)", h)
                        if match:
                            svc_name = match.group(1)
                            # Create a calls edge from gateway endpoints to services
                            svc_id = f"base_krakend_service_{clean(svc_name)}" # fallback pattern or match
                            # We can also add general inferred calls edge
                            edges.append({
                                "source": file_id,
                                "target": f"infra_postgresql_{clean(svc_name.replace('-service', '_db'))}" if 'db' in svc_name else f"gitops_base_frontend_service_yaml" if 'frontend' in svc_name else f"gitops_base_{clean(svc_name)}_service_yaml",
                                "relation": "calls",
                                "confidence": "INFERRED",
                                "confidence_score": 0.85,
                                "source_file": rel_path,
                                "weight": 1.0
                            })
                            
        elif suffix == ".yml" or (suffix == ".yaml" and "application" in rel_path):
            # Parse Spring Boot application configs
            nodes.append({
                "id": file_id,
                "label": f"Spring Config: {path_obj.name}",
                "file_type": "document",
                "source_file": rel_path
            })
            
            # Find DB connection details
            db_match = re.search(r"url:\s*\$\{DB_URL\}|postgres-([a-zA-Z0-9\-]+)-postgresql", content)
            if db_match:
                # Find service name
                service_name_match = re.search(r"name:\s*\${SERVICE_NAME:([a-zA-Z0-9\-]+)}|name:\s*([a-zA-Z0-9\-]+)", content)
                if service_name_match:
                    svc_name = service_name_match.group(1) or service_name_match.group(2)
                    db_key = f"{svc_name.replace('-service','')}_db"
                    if db_key in databases:
                        edges.append({
                            "source": file_id,
                            "target": databases[db_key],
                            "relation": "shares_data_with",
                            "confidence": "EXTRACTED",
                            "confidence_score": 1.0,
                            "source_file": rel_path
                        })
            
            # Find Kafka topics referenced
            for topic in kafka_topics:
                if topic in content:
                    topic_id = f"infra_kafka_topic_{clean(topic)}"
                    edges.append({
                        "source": file_id,
                        "target": topic_id,
                        "relation": "references",
                        "confidence": "EXTRACTED",
                        "confidence_score": 1.0,
                        "source_file": rel_path
                    })
                    
    # Generate some semantic cross-cutting connections (Tying microservices together!)
    # E.g., user-service publishes user-events, which notification-service consumes!
    edges.append({
        "source": "services_user_service_src_main_java_com_demo_user_usercontroller_java",
        "target": "infra_kafka_topic_user_events",
        "relation": "calls",
        "confidence": "INFERRED",
        "confidence_score": 0.85,
        "source_file": "services/user-service/src/main/resources/application.yml"
    })
    edges.append({
        "source": "services_notification_service_src_main_java_com_demo_notification_notificationcontroller_java",
        "target": "infra_kafka_topic_user_events",
        "relation": "references",
        "confidence": "INFERRED",
        "confidence_score": 0.85,
        "source_file": "services/notification-service/src/main/resources/application.yml"
    })
    
    # Tying order-service publishing order-events, consumed by payment-service
    edges.append({
        "source": "services_order_service_src_main_java_com_demo_order_ordercontroller_java",
        "target": "infra_kafka_topic_order_events",
        "relation": "calls",
        "confidence": "INFERRED",
        "confidence_score": 0.85,
        "source_file": "services/order-service/src/main/resources/application.yml"
    })
    edges.append({
        "source": "services_payment_service_src_main_java_com_demo_payment_paymentcontroller_java",
        "target": "infra_kafka_topic_order_events",
        "relation": "references",
        "confidence": "INFERRED",
        "confidence_score": 0.85,
        "source_file": "services/payment-service/src/main/resources/application.yml"
    })

    # Tying payment-service publishing payment-events, consumed by order-service and notification-service
    edges.append({
        "source": "services_payment_service_src_main_java_com_demo_payment_paymentcontroller_java",
        "target": "infra_kafka_topic_payment_events",
        "relation": "calls",
        "confidence": "INFERRED",
        "confidence_score": 0.85,
        "source_file": "services/payment-service/src/main/resources/application.yml"
    })
    edges.append({
        "source": "services_notification_service_src_main_java_com_demo_notification_notificationcontroller_java",
        "target": "infra_kafka_topic_payment_events",
        "relation": "references",
        "confidence": "INFERRED",
        "confidence_score": 0.85,
        "source_file": "services/notification-service/src/main/resources/application.yml"
    })

    # Deduplicate nodes by ID
    unique_nodes = []
    seen_nodes = set()
    for n in nodes:
        if n["id"] not in seen_nodes:
            seen_nodes.add(n["id"])
            unique_nodes.append(n)

    output_data = {
        "nodes": unique_nodes,
        "edges": edges,
        "hyperedges": hyperedges,
        "input_tokens": 0,
        "output_tokens": 0
    }
    
    Path("graphify-out/.graphify_semantic.json").write_text(
        json.dumps(output_data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"Extracted {len(unique_nodes)} nodes and {len(edges)} edges semantically.")

if __name__ == "__main__":
    run_extraction()
