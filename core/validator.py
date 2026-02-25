ALLOWED = {"ingest_docs", "build_specs", "gen_all", "mcp_tool", "reply"}

def validate_plan(plan):
    raw_steps = (plan or {}).get("steps", [])
    steps = []
    ids = set()
    for i, s in enumerate(raw_steps, start=1):
        if not isinstance(s, dict):
            continue
        action = s.get("action")
        if action not in ALLOWED:
            continue
        sid = int(s.get("id", i))
        if sid in ids:
            # skip duplicate ids
            continue
        ids.add(sid)
        args = s.get("args") if isinstance(s.get("args"), dict) else {}
        deps = s.get("depends_on") or []
        deps = [int(d) for d in deps if isinstance(d, (int, str))]
        steps.append({"id": sid, "action": action, "args": args, "depends_on": deps})

    if not steps:
        steps = [
            {"id": 1, "action": "ingest_docs", "args": {}, "depends_on": []},
            {"id": 2, "action": "build_specs", "args": {}, "depends_on": [1]},
            {"id": 3, "action": "gen_all", "args": {}, "depends_on": [2]},
            {"id": 4, "action": "reply", "args": {"text": "Generated outputs."}, "depends_on": [3]},
        ]

    # Enforce ordering constraints
    by_id = {s["id"]: s for s in steps}
    need = {"build_specs": "ingest_docs", "gen_all": "build_specs"}
    for s in steps:
        req = need.get(s["action"]) 
        if req:
            # ensure a prior step with required action exists and is a dependency
            req_ids = [x["id"] for x in steps if x["action"] == req]
            if req_ids:
                rid = req_ids[-1]
                if rid not in s["depends_on"]:
                    s["depends_on"].append(rid)
        # drop self-dependencies and unknown ids
        s["depends_on"] = [d for d in s["depends_on"] if d != s["id"] and d in by_id]

    # Basic acyclic check ()
    incoming = {s["id"]: set(s["depends_on"]) for s in steps}
    ready = [sid for sid, deps in incoming.items() if not deps]
    visited = 0
    while ready:
        sid = ready.pop()
        visited += 1
        for t in steps:
            if sid in incoming[t["id"]]:
                incoming[t["id"]].remove(sid)
                if not incoming[t["id"]]:
                    ready.append(t["id"])
    if visited != len(steps):
        # cycle detected; fall back to safe plan
        steps = [
            {"id": 1, "action": "ingest_docs", "args": {}, "depends_on": []},
            {"id": 2, "action": "build_specs", "args": {}, "depends_on": [1]},
            {"id": 3, "action": "gen_all", "args": {}, "depends_on": [2]},
            {"id": 4, "action": "reply", "args": {"text": "Generated outputs."}, "depends_on": [3]},
        ]

    return {"steps": steps}
