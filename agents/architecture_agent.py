from tools.diagrams_adapter import generate_architecture
from tools.plantuml import build_cloud_arch_puml
import os
import re
from tools import mcp_client

class ArchitectureAgent:
    def __init__(self, workdir):
        self.workdir = workdir
    def run(self, context):
        images = []
        texts = []
        providers = context["prefs"].get("providers", [])
        for p in providers:
            path = generate_architecture(p, context["data"], self.workdir)
            if path:
                images.append(path)
            if p in ["aws","gcp"]:
                text_hint = (context.get("data",{}).get("spec_text","") + "\n" + context.get("data",{}).get("prompt",""))
                texts.append(build_cloud_arch_puml(p, services=None, text_hint=text_hint))
            if p == "aws" and os.environ.get("AWS_DOCS_MCP_CMD"):
                text_blob = (context.get("data",{}).get("spec_text","") + "\n" + context.get("data",{}).get("prompt","")).lower()
                keys = ["vpc","elb","api gateway","ec2","lambda","dynamodb","rds","s3","cloudfront","route53"]
                terms = [k for k in keys if re.search(rf"\\b{k}\\b", text_blob)]
                seen = set()
                for term in terms[:3]:
                    if term in seen:
                        continue
                    seen.add(term)
                    q = f"AWS {term} architecture best practices"
                    res = mcp_client.aws_docs_search(q)
                    url = None
                    if isinstance(res, dict) and res.get("text"):
                        for part in str(res.get("text","")).split():
                            if part.startswith("http"):
                                url = part
                                break
                    elif isinstance(res, str):
                        for part in res.split():
                            if part.startswith("http"):
                                url = part
                                break
                    if url:
                        page = mcp_client.aws_docs_read(url)
                        if isinstance(page, dict) and page.get("text"):
                            texts.append(page["text"])
                        elif isinstance(page, str):
                            texts.append(page)
        return {"images": images, "texts": texts}
