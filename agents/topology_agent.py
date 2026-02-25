from tools.mermaid import generate_topology
import os
# TopologyAgent class to generate topology diagrams
class TopologyAgent:
    def __init__(self, workdir):
        self.workdir = workdir
    def run(self, context):
        code = generate_topology(context["prefs"].get("providers", []), context["data"]) 
        return {"images": [], "texts": [code]}

