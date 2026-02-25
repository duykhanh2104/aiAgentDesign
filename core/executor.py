import os
from tools.parsers import parse_any
from tools.specs_builder import build_specs_md
from core.orchestrator import Orchestrator
from tools import mcp_client

def _toposort(steps):
    by_id = {s["id"]: s for s in steps}
    incoming = {sid: set(s.get("depends_on") or []) for sid, s in by_id.items()}
    ready = [sid for sid, deps in incoming.items() if not deps]
    order = []
    while ready:
        sid = ready.pop()
        order.append(by_id[sid])
        for tid, deps in incoming.items():
            if sid in deps:
                deps.remove(sid)
                if not deps:
                    ready.append(tid)
    if len(order) != len(steps):
        # cycle or unresolved deps; fall back to given order
        return steps
    return order

def execute(plan, documents, images, message):
    state = {"docs": None, "specs": None, "images": [], "texts": [], "reply": None, "logs": []}
    steps = plan.get("steps", [])
    for step in _toposort(steps):
        action = step.get("action")
        sid = step.get("id")
        state["logs"].append(f"Executing step {sid}:{action}")
        if action == "ingest_docs":
            state["docs"] = parse_any(documents or [])
        elif action == "build_specs":
            if state.get("docs") is None:
                state["docs"] = parse_any(documents or [])
            state["specs"] = build_specs_md(state["docs"], message or "")
        elif action == "gen_all":
            orch = Orchestrator(os.path.join(os.getcwd(), "outputs"))
            out = orch.run(documents, message)
            state["images"] = out.get("images", [])
            state["texts"] = out.get("texts", [])
        elif action == "mcp_tool":
            args = step.get("args", {}) or {}
            server_cmd = args.get("server_cmd") or os.environ.get("MCP_SERVER_CMD")
            tool = args.get("tool")
            params = args.get("params") or {}
            if not server_cmd or not tool:
                state["logs"].append("mcp_tool skipped: server_cmd or tool missing")
            else:
                try:
                    res = mcp_client.call_tool(server_cmd, tool, params, timeout=30)
                    if isinstance(res, dict) and res.get("image_path"):
                        state["images"].append(res["image_path"])
                    if isinstance(res, dict) and res.get("text"):
                        state["texts"].append(res["text"])
                    elif isinstance(res, str):
                        state["texts"].append(res)
                    state["logs"].append(f"mcp_tool {tool} OK")
                except Exception as e:
                    state["logs"].append(f"mcp_tool error: {e}")
        elif action == "reply":
            text = step.get("args", {}).get("text")
            if not text:
                text = "Generated files:\n" + "\n".join(state.get("images", []))
                if state.get("texts"):
                    text += "\n\n" + "\n\n".join(state["texts"])
            state["reply"] = text
    if not state.get("reply"):
        text = "Generated files:\n" + "\n".join(state.get("images", []))
        if state.get("texts"):
            text += "\n\n" + "\n\n".join(state["texts"])
        state["reply"] = text
    return state
