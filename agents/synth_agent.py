import os
# SynthAgent class to generate architecture report
class SynthAgent:
    def __init__(self, workdir):
        self.workdir = workdir
    def run(self, outputs):
        report = []
        if outputs.get("architecture"):
            report.append("Architecture generated with provider icons")
        if outputs.get("uml"):
            report.append("UML generated using PlantUML and Mermaid")
        if outputs.get("topology"):
            report.append("Topology code generated using Mermaid")
        return {"report": "\n".join(report)}

