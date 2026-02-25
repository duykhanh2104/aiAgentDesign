def generate_mermaid(diagram_type, data):
    if diagram_type == "class":
        return "classDiagram\nClassA <|-- ClassB\nClassA : +method()\nClassB : +call()"
    if diagram_type == "sequence":
        return "sequenceDiagram\nparticipant A\nparticipant B\nA->>B: request\nB-->>A: response"
    if diagram_type == "activity":
        return "flowchart TD\nA[Start] --> B{Decision} -->|Yes| C[Do] --> D[End]"
    if diagram_type == "deployment":
        return "flowchart LR\nClient --> LB --> App --> DB"
    if diagram_type == "component":
        return "flowchart LR\nUI --> API --> Service --> DB"
    return "flowchart LR\nA --> B"

def generate_topology(providers, data):
    text = ""
    try:
        text = (data.get("spec_text","") + "\n" + data.get("prompt","")).lower()
    except Exception:
        text = ""
    svc = []
    aws_keys = ["elb","ec2","lambda","s3","rds","dynamodb","vpc","api gateway","sqs","sns"]
    gcp_keys = ["cloud load balancing","compute engine","cloud run","cloud storage","cloud sql","pubsub","gke"]
    keys = []
    if "aws" in (providers or ["aws"]):
        keys += aws_keys
    if "gcp" in (providers or []):
        keys += gcp_keys
    for k in keys:
        if k in text:
            svc.append(k.upper().replace(" ", "_"))
    if not svc:
        svc = ["INTERNET","LB","APP","DB"]
    chain = " --> ".join(svc)
    return "flowchart LR\n" + chain
