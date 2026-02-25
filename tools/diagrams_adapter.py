import os
from .plantuml import build_cloud_arch_puml, render_png
import re
from . import mcp_client

def generate_architecture(provider, data, workdir):
    # Prefer PlantUML icon sets hosted online to avoid local icon paths in DOT
    try:
        text_hint = ""
        try:
            text_hint = (data.get("spec_text","") + "\n" + data.get("prompt","")).lower()
        except Exception:
            text_hint = ""
        # Detect service hints from text using simple keywords
        svc = []
        for word in ["ec2","s3","rds","elb","lambda","dynamodb","vpc","route53","cloudfront",
                    "api gateway","sqs","sns","eks","ecs","ecr","kms","iam","cloudwatch",
                    "gce","compute engine","cloud sql","bigquery","pubsub","gke",
                    "cloud storage","cloud run","cloud functions","spanner","memorystore"]:
            if re.search(rf"\\b{re.escape(word)}\\b", text_hint):
                svc.append(word)
        name = os.path.join(workdir, f"arch_{provider}")
        if provider == "aws" and os.environ.get("AWS_DIAGRAM_MCP_CMD"):
            code_lines = []
            code_lines.append("from diagrams import Diagram")
            code_lines.append("from diagrams.aws.network import ELB, APIGateway, CloudFront, Route53")
            code_lines.append("from diagrams.aws.compute import EC2, Lambda, ECS, EKS")
            code_lines.append("from diagrams.aws.database import RDS, DynamoDB")
            code_lines.append("from diagrams.aws.storage import S3")
            code_lines.append("from diagrams.aws.security import KMS, IAM")
            code_lines.append("from diagrams.aws.management import Cloudwatch")
            code_lines.append("from diagrams.aws.integration import SQS, SNS")
            code_lines.append("from diagrams.aws.network import VPC")
            code_lines.append(f"with Diagram('AWS Architecture', filename='{os.path.splitext(name)[0]}', show=False, outformat='png'):")
            chain = []
            if any("cloudfront" in x for x in svc): chain.append("CloudFront('cdn')")
            if any("route53" in x for x in svc): chain.append("Route53('dns')")
            if any("elb" in x for x in svc) or any('api gateway' in x for x in svc):
                if any('api gateway' in x for x in svc): chain.append(\"APIGateway('api')\")
                else: chain.append(\"ELB('lb')\")
            if any("lambda" in x for x in svc): chain.append(\"Lambda('fn')\")
            elif any("ecs" in x for x in svc): chain.append(\"ECS('svc')\")
            elif any("eks" in x for x in svc): chain.append(\"EKS('k8s')\")
            else: chain.append(\"EC2('app')\")
            if any("rds" in x for x in svc): chain.append(\"RDS('db')\")
            elif any("dynamodb" in x for x in svc): chain.append(\"DynamoDB('kv')\")
            if any("s3" in x for x in svc): chain.append(\"S3('bucket')\")
            if not chain: chain = [\"ELB('lb')\",\"EC2('app')\",\"RDS('db')\"]
            code_lines.append(\"    \" + \" >> \".join(chain))
            code = \"\\n\".join(code_lines)
            out = name + \".png\"
            p = mcp_client.aws_diagram_generate(code, out)
            if isinstance(p, str) and os.path.exists(p):
                return p
            if isinstance(p, dict) and p.get(\"text\"):
                txt = p[\"text\"]
                if isinstance(txt, str) and os.path.exists(out):
                    return out
        if provider in ["aws","gcp"]:
            puml = build_cloud_arch_puml(provider, services=svc, text_hint=text_hint)
            out = name + ".png"
            png = render_png(puml, out)
            if png and os.path.exists(png):
                return png
        # Fallback to diagrams library for other providers or when PlantUML fails
        from diagrams import Diagram
        if provider == "azure":
            from diagrams.azure.network import LoadBalancers
            from diagrams.azure.compute import AppServices
            from diagrams.azure.database import SQLDatabases
            with Diagram("Azure Architecture", filename=name, show=False):
                LoadBalancers("lb") >> AppServices("app") >> SQLDatabases("db")
            path = name + ".png"
            return path if os.path.exists(path) else None
        if provider == "onprem":
            from diagrams.onprem.network import Nginx
            from diagrams.onprem.compute import Server
            from diagrams.onprem.database import PostgreSQL
            with Diagram("On-Prem Architecture", filename=name, show=False):
                Nginx("lb") >> Server("app") >> PostgreSQL("db")
            path = name + ".png"
            return path if os.path.exists(path) else None
        return None
    except Exception:
        return None
