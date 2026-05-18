import json
from pathlib import Path
import re

def clean(s):
    if not s:
        return ""
    s_clean = "".join(c if c.isalnum() or c == '_' else '_' for c in s.lower())
    s_clean = re.sub('_+', '_', s_clean)
    return s_clean.strip('_')

def get_community_label(nodes):
    # Heuristic for descriptive community labeling
    if any("tsconfig_app" in n for n in nodes):
        return "Frontend TS Config (App)"
    if any("tsconfig_node" in n for n in nodes):
        return "Frontend TS Config (Node)"
    if any("package_dependencies" in n for n in nodes):
        return "Frontend Production Dependencies"
    if any("package_devdependencies" in n for n in nodes):
        return "Frontend Dev Dependencies"
    if any("kafka" in n for n in nodes):
        return "Kafka Strimzi Messaging Broker & Events"
    if any("postgres" in n or "db" in n for n in nodes):
        return "PostgreSQL Database Infrastructure"
    if any("implement_" in n for n in nodes):
        return "Architecture Guide & Runbook (IMPLEMENT.md)"
    if any("frontend_src" in n or "src_app" in n for n in nodes):
        return "Frontend Application Code (React)"
    if any("frontend_deployment" in n or "frontend_service" in n for n in nodes):
        return "Frontend Kubernetes Deployment & Service"
    if any("cert_manager" in n or "metallb" in n or "ingress_nginx" in n for n in nodes):
        return "System Apps & Core Kubernetes Addons"
    if any("payment" in n for n in nodes):
        return "Payment Microservice (Spring Boot & K8s)"
    if any("order" in n for n in nodes):
        return "Order Microservice (Spring Boot & K8s)"
    if any("user" in n for n in nodes):
        return "User Microservice (Spring Boot & K8s)"
    if any("notification" in n for n in nodes):
        return "Notification Microservice (Spring Boot & K8s)"
    if any("krakend" in n for n in nodes):
        return "KrakenD API Gateway (Base & Deployment)"
    
    # Generic fallback based on node prefixes
    for node in nodes:
        parts = node.split('_')
        if len(parts) > 1:
            clean_part1 = clean(parts[0]).capitalize()
            clean_part2 = clean(parts[1]).capitalize()
            return f"{clean_part1} {clean_part2} Components"
            
    return "Core Infrastructure Component"

def run_labeling():
    # Load analysis
    analysis_path = Path("graphify-out/.graphify_analysis.json")
    if not analysis_path.exists():
        print("Error: analysis.json not found")
        return
        
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    communities = analysis["communities"]
    
    # Create plain-language labels
    labels = {}
    for cid, nodes in communities.items():
        labels[int(cid)] = get_community_label(nodes)
        
    # Re-generate the report and graph with these labels
    from graphify.build import build_from_json
    from graphify.report import generate
    from graphify.export import to_json
    from graphify.analyze import suggest_questions
    
    extraction = json.loads(Path("graphify-out/.graphify_extract.json").read_text(encoding="utf-8"))
    detection  = json.loads(Path("graphify-out/.graphify_detect.json").read_text(encoding="utf-8"))
    
    G = build_from_json(extraction)
    
    # Load typed communities
    typed_communities = {int(k): v for k, v in communities.items()}
    cohesion = {int(k): v for k, v in analysis["cohesion"].items()}
    gods = analysis["gods"]
    surprises = analysis["surprises"]
    tokens = {"input": extraction.get("input_tokens", 0), "output": extraction.get("output_tokens", 0)}
    
    # Generate tailored suggested questions based on labels
    questions = suggest_questions(G, typed_communities, labels)
    
    # Generate final report
    report = generate(
        G, 
        typed_communities, 
        cohesion, 
        labels, 
        gods, 
        surprises, 
        detection, 
        tokens, 
        ".", 
        suggested_questions=questions
    )
    
    # Write output report
    Path("graphify-out/GRAPH_REPORT.md").write_text(report, encoding="utf-8")
    
    # Write final graph.json
    to_json(G, typed_communities, "graphify-out/graph.json")
    
    print(f"Successfully labeled {len(labels)} communities and updated GRAPH_REPORT.md and graph.json")

if __name__ == "__main__":
    run_labeling()
