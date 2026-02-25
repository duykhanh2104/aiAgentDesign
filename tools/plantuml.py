import requests
import re

AWS_PUML_BASE = "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v20.0/dist"
GCP_PUML_BASE = "https://raw.githubusercontent.com/davidholsgrove/gcp-icons-for-plantuml/master/dist"

def generate_uml(diagram_type, data):
    if diagram_type == "class":
        return "@startuml\nclass A {+method()}\nclass B {+call()}\nA <|-- B\n@enduml"
    if diagram_type == "sequence":
        return "@startuml\nactor User\nparticipant API\nUser -> API: request\nAPI --> User: response\n@enduml"
    if diagram_type == "deployment":
        return "@startuml\nnode Client\nnode Cloud {\nnode LB\nnode App\nnode DB\n}\nClient -> LB\nLB -> App\nApp -> DB\n@enduml"
    if diagram_type == "component":
        return "@startuml\npackage UI\npackage API\npackage Service\npackage DB\nUI --> API\nAPI --> Service\nService --> DB\n@enduml"
    if diagram_type == "activity":
        return "@startuml\nstart\nif (Decision) then (yes)\n:Do;\nendif\nstop\n@enduml"
    return "@startuml\n@enduml"

def _alias_map(provider: str) -> dict:
    if provider == "aws":
        return {
            "ec2": "EC2",
            "elb": "ElasticLoadBalancing",
            "alb": "ElasticLoadBalancing",
            "nlb": "ElasticLoadBalancing",
            "s3": "SimpleStorageService",
            "rds": "RelationalDatabaseService",
            "aurora": "Aurora",
            "dynamodb": "DynamoDB",
            "lambda": "Lambda",
            "vpc": "VPC",
            "route53": "Route53",
            "cloudfront": "CloudFront",
            "api gateway": "APIGateway",
            "apigateway": "APIGateway",
            "sqs": "SimpleQueueService",
            "sns": "SimpleNotificationService",
            "elasticache": "ElastiCache",
            "eks": "ElasticKubernetesService",
            "ecr": "ElasticContainerRegistry",
            "ecs": "ElasticContainerService",
            "cloudwatch": "CloudWatch",
            "kms": "KeyManagementService",
            "iam": "IdentityAccessManagement",
            "ssm": "SystemsManager",
            "opensearch": "OpenSearchService",
            "elasticsearch": "OpenSearchService",
            "redshift": "Redshift",
            "glue": "Glue",
            "emr": "EMR",
            "kinesis": "KinesisDataStreams",
        }
    if provider == "gcp":
        return {
            "compute engine": "ComputeEngine",
            "gce": "ComputeEngine",
            "cloud run": "CloudRun",
            "run": "CloudRun",
            "gke": "KubernetesEngine",
            "kubernetes engine": "KubernetesEngine",
            "cloud sql": "CloudSQL",
            "spanner": "Spanner",
            "bigquery": "BigQuery",
            "pubsub": "PubSub",
            "cloud storage": "CloudStorage",
            "gcs": "CloudStorage",
            "memorystore": "Memorystore",
            "redis": "Memorystore",
            "firestore": "Firestore",
            "dataproc": "Dataproc",
            "dataflow": "Dataflow",
            "load balancer": "CloudLoadBalancing",
            "cloud load balancing": "CloudLoadBalancing",
            "vpc": "VPCNetwork",
            "cloud functions": "CloudFunctions",
        }
    return {}

def _normalize_services(services: list[str] | None, text_hint: str, provider: str) -> list[str]:
    services = services or []
    aliases = _alias_map(provider)
    found = set()
    src = (text_hint or "").lower()
    # Simple keyword scan
    for key, macro in aliases.items():
        if re.search(rf"\\b{re.escape(key)}\\b", src):
            found.add(macro)
    # Map provided services to macros
    for s in services:
        k = (s or "").strip().lower()
        if k in aliases:
            found.add(aliases[k])
        else:
            # Heuristic CamelCase
            macro = re.sub(r"[^a-zA-Z0-9]+", " ", k).title().replace(" ", "")
            if macro:
                found.add(macro)
    # Fallback defaults
    if not found:
        if provider == "aws":
            return ["ElasticLoadBalancing", "EC2", "RelationalDatabaseService"]
        if provider == "gcp":
            return ["CloudLoadBalancing", "ComputeEngine", "CloudSQL"]
    return list(found)

def build_cloud_arch_puml(provider: str, services: list[str] | None = None, text_hint: str = "") -> str:
    if provider == "aws":
        macros = _normalize_services(services, text_hint, provider)
        includes = [
            f"!define AWSPuml {AWS_PUML_BASE}",
            "!include AWSPuml/AWSCommon.puml",
            "!include AWSPuml/Analytics/all.puml",
            "!include AWSPuml/ApplicationIntegration/all.puml",
            "!include AWSPuml/BusinessApplications/all.puml",
            "!include AWSPuml/Compute/all.puml",
            "!include AWSPuml/Database/all.puml",
            "!include AWSPuml/DeveloperTools/all.puml",
            "!include AWSPuml/EndUserComputing/all.puml",
            "!include AWSPuml/General/all.puml",
            "!include AWSPuml/InternetOfThings/all.puml",
            "!include AWSPuml/MachineLearning/all.puml",
            "!include AWSPuml/ManagementGovernance/all.puml",
            "!include AWSPuml/MediaServices/all.puml",
            "!include AWSPuml/MigrationTransfer/all.puml",
            "!include AWSPuml/NetworkingContentDelivery/all.puml",
            "!include AWSPuml/SecurityIdentityCompliance/all.puml",
            "!include AWSPuml/Storage/all.puml",
        ]
        nodes = []
        aliases = []
        for i, m in enumerate(macros):
            alias = f"n{i}"
            aliases.append(alias)
            nodes.append(f'{m}({alias}, "{m}")')
        edges = []
        for i in range(len(aliases) - 1):
            edges.append(f"{aliases[i]} --> {aliases[i+1]}")
        content = "\n".join(nodes + edges)
        return "@startuml\n" + "\n".join(includes) + "\nleft to right direction\n" + content + "\n@enduml"
    if provider == "gcp":
        macros = _normalize_services(services, text_hint, provider)
        includes = [
            f"!define GCPPuml {GCP_PUML_BASE}",
            "!includeurl GCPPuml/GCPCommon.puml",
            "!includeurl GCPPuml/AIAndMachineLearning/all.puml",
            "!includeurl GCPPuml/Analytics/all.puml",
            "!includeurl GCPPuml/Compute/all.puml",
            "!includeurl GCPPuml/Databases/all.puml",
            "!includeurl GCPPuml/DeveloperTools/all.puml",
            "!includeurl GCPPuml/ManagementTools/all.puml",
            "!includeurl GCPPuml/Networking/all.puml",
            "!includeurl GCPPuml/Operations/all.puml",
            "!includeurl GCPPuml/SecurityIdentityCompliance/all.puml",
            "!includeurl GCPPuml/Storage/all.puml",
            "!includeurl GCPPuml/Serverless/all.puml",
        ]
        nodes = []
        aliases = []
        for i, m in enumerate(macros):
            alias = f"n{i}"
            aliases.append(alias)
            nodes.append(f'{m}({alias}, "{m}")')
        edges = []
        for i in range(len(aliases) - 1):
            edges.append(f"{aliases[i]} --> {aliases[i+1]}")
        content = "\n".join(nodes + edges)
        return "@startuml\n" + "\n".join(includes) + "\ndirected left to right\n" + content + "\n@enduml"
    # Fallback generic
    return "@startuml\nrectangle Cloud\n@enduml"

def render_png(uml_text, output_path):
    try:
        url = "https://www.plantuml.com/plantuml/png"
        r = requests.post(url, data=uml_text.encode("utf-8"), timeout=30)
        if r.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(r.content)
            return output_path
        return None
    except Exception:
        return None
