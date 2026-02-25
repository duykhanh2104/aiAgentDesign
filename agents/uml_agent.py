from tools.plantuml import generate_uml, render_png
from tools.mermaid import generate_mermaid
import os
# UmlAgent class to generate UML diagrams
class UmlAgent:
    def __init__(self, workdir):
        self.workdir = workdir
    def run(self, context):
        images = []
        texts = []
        types_ = context["prefs"].get("uml_types", [])
        for t in types_:
            txt = generate_uml(t, context["data"])
            texts.append(txt)
            name = f"uml_{t}.png"
            out = os.path.join(self.workdir, name)
            img = render_png(txt, out)
            if img:
                images.append(img)
        for t in types_:
            m = generate_mermaid(t, context["data"])
            texts.append(m)
        return {"images": images, "texts": texts}

