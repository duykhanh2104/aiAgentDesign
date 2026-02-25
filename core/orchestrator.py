import os
from agents.architecture_agent import ArchitectureAgent
from agents.uml_agent import UmlAgent
from agents.topology_agent import TopologyAgent
from tools.parsers import parse_any
from tools.specs_builder import build_specs_md

class Orchestrator:
    def __init__(self, workdir):
        self.workdir = workdir
        self.arch = ArchitectureAgent(workdir)
        self.uml = UmlAgent(workdir)
        self.topo = TopologyAgent(workdir)

    def detect_providers(self, text):
        t = (text or "").lower()
        providers = []
        if "aws" in t: providers.append("aws")
        if "azure" in t: providers.append("azure")
        if "gcp" in t or "google" in t: providers.append("gcp")
        if "onprem" in t or "on-prem" in t: providers.append("onprem")
        return providers or ["aws"]

    def detect_uml(self, text):
        return ["class", "sequence", "deployment"]

    def run(self, documents, prompt):
        os.makedirs(self.workdir, exist_ok=True)
        data = parse_any(documents or [])
        specs_md = build_specs_md(data, prompt or "")
        context = {"data": {"spec_text": specs_md, "prompt": prompt or ""}, "prefs": {"providers": self.detect_providers(prompt or ""), "uml_types": self.detect_uml(prompt or "")}}
        arch_outputs = self.arch.run(context)
        uml_outputs = self.uml.run(context)
        topo_outputs = self.topo.run(context)
        texts = []
        for t in arch_outputs.get("texts", []): texts.append(t)
        for t in uml_outputs.get("texts", []): texts.append(t)
        for t in topo_outputs.get("texts", []): texts.append(t)
        images = arch_outputs.get("images", []) + uml_outputs.get("images", []) + topo_outputs.get("images", [])
        return {"specs_md": specs_md, "images": images, "texts": texts}

