

import json
from tools.llm_router import route

PLANNING_SYSTEM = (
    "You are a planning agent. Return ONLY JSON following this schema (no prose):\n"
    "{\n  \"steps\": [\n    {\n      \"id\": <integer>,\n      \"action\": \"ingest_docs|build_specs|gen_all|mcp_tool|reply\",\n      \"args\": {},\n      \"depends_on\": [<integer>, ...]  // optional\n    }\n  ]\n}\n"
    "Rules: (1) ingest_docs before build_specs; (2) build_specs before gen_all; (3) Use mcp_tool for external tools when configured; (4) reply last; (5) Use small number of steps with minimal args."
)

def _coerce_list(x):
    if isinstance(x, (list, tuple)):
        return list(x)
    if x is None:
        return []
    return [x]

def make_plan(models, documents, images, message, history):
    msgs = [
        {"role": "system", "content": PLANNING_SYSTEM},
        {"role": "user", "content": message or ""},
    ]
    model_list = _coerce_list(models)
    # Cost optimization: planning does not require full document context
    out = route(model_list, documents, msgs, images, include_docs=False)
    try:
        obj = json.loads(out)
        if isinstance(obj, dict) and isinstance(obj.get("steps", []), list):
            # Normalize fields
            norm = []
            for i, s in enumerate(obj.get("steps", []), start=1):
                if not isinstance(s, dict):
                    continue
                step = {
                    "id": int(s.get("id", i)),
                    "action": s.get("action"),
                    "args": s.get("args") if isinstance(s.get("args"), dict) else {},
                    "depends_on": [int(d) for d in (s.get("depends_on") or []) if isinstance(d, (int, str))],
                }
                norm.append(step)
            return {"steps": norm}
    except Exception:
        pass
    # Safe default plan with explicit IDs and dependencies
    return {
        "steps": [
            {"id": 1, "action": "ingest_docs", "args": {}, "depends_on": []},
            {"id": 2, "action": "build_specs", "args": {}, "depends_on": [1]},
            {"id": 3, "action": "gen_all", "args": {}, "depends_on": [2]},
            {"id": 4, "action": "reply", "args": {"text": "Generated architecture artifacts from documents."}, "depends_on": [3]},
        ]
    }
