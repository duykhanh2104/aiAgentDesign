import os
from tools.parsers import parse_any

class SearchAgent:
    def run(self, documents, providers, uml_types, models=None, api_keys=None, prompt=None):
        data = parse_any(documents or [])
        data["prompt"] = prompt or ""
        prefs = {
            "providers": providers or [],
            "uml_types": uml_types or ["class", "sequence", "deployment"],
            "models": models or [],
            "api_keys": api_keys or {},
        }
        return {"data": data, "prefs": prefs, "workdir": os.path.join(os.getcwd(), "outputs")}
