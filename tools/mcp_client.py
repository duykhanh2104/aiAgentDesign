import asyncio
import os
from typing import Any, Dict

def _no_mcp(msg: str) -> Dict[str, Any]:
    return {"error": msg}

def call_tool(server_cmd: str, tool: str, params: Dict[str, Any] | None = None, timeout: int = 30) -> Dict[str, Any] | str:
    try:
        import anyio  # type: ignore
    except Exception:
        anyio = None
    try:
        # Optional import; succeed only if mcp is installed
        from mcp import ClientSession  # type: ignore
        from mcp.transport.stdio import StdioServerTransport  # type: ignore
    except Exception:
        return _no_mcp("MCP library not installed")

    async def _run() -> Dict[str, Any] | str:
        cmd_parts = server_cmd if isinstance(server_cmd, (list, tuple)) else server_cmd.split()
        async with StdioServerTransport.create(cmd_parts[0], *cmd_parts[1:]) as transport:
            async with ClientSession(transport) as session:
                await session.initialize()
                try:
                    res = await session.call_tool(tool, params or {})
                    # Normalize a simple text/image response shape
                    if hasattr(res, "content") and isinstance(res.content, list):
                        text_chunks = []
                        for c in res.content:
                            t = getattr(c, "text", None)
                            if t:
                                text_chunks.append(t)
                        return {"text": "\n".join(text_chunks)}
                    return res  # best-effort passthrough
                finally:
                    await session.shutdown()
    try:
        if anyio is not None:
            return anyio.run(_run)
        return asyncio.run(_run())
    except Exception as e:
        return _no_mcp(f"MCP error: {e}")

def _save_base64_png(b64: str, out_path: str) -> str | None:
    try:
        import base64
        data = base64.b64decode(b64)
        d = os.path.dirname(out_path)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(data)
        return out_path
    except Exception:
        return None

def aws_diagram_list_icons() -> Dict[str, Any] | str:
    cmd = os.environ.get("AWS_DIAGRAM_MCP_CMD")
    if not cmd:
        return _no_mcp("AWS_DIAGRAM_MCP_CMD not set")
    return call_tool(cmd, "list_icons", {})

def aws_diagram_get_examples(diagram_type: str | None = None) -> Dict[str, Any] | str:
    cmd = os.environ.get("AWS_DIAGRAM_MCP_CMD")
    if not cmd:
        return _no_mcp("AWS_DIAGRAM_MCP_CMD not set")
    params = {"type": diagram_type} if diagram_type else {}
    return call_tool(cmd, "get_diagram_examples", params)

def aws_diagram_generate(code: str, out_path: str, out_format: str = "png") -> str | Dict[str, Any] | None:
    cmd = os.environ.get("AWS_DIAGRAM_MCP_CMD")
    if not cmd:
        return None
    res = call_tool(cmd, "generate_diagram", {"code": code, "format": out_format})
    if isinstance(res, dict):
        if res.get("image_b64"):
            p = _save_base64_png(res["image_b64"], out_path)
            return p
        if res.get("image_path"):
            return res["image_path"]
        if res.get("text"):
            txt = res["text"]
            if isinstance(txt, str) and len(txt) > 100 and "data:image/png;base64," in txt:
                b64 = txt.split("data:image/png;base64,")[-1].strip()
                p = _save_base64_png(b64, out_path)
                return p
            return res
        return res
    if isinstance(res, str):
        s = res.strip()
        if "data:image/png;base64," in s:
            b64 = s.split("data:image/png;base64,")[-1].strip()
            p = _save_base64_png(b64, out_path)
            return p
        if len(s) > 800 and all(c.isalnum() or c in "+/=\n\r" for c in s[:100]):
            p = _save_base64_png(s, out_path)
            return p
        return {"text": s}
    return None

def aws_docs_search(query: str) -> Dict[str, Any] | str:
    cmd = os.environ.get("AWS_DOCS_MCP_CMD")
    if not cmd:
        return _no_mcp("AWS_DOCS_MCP_CMD not set")
    return call_tool(cmd, "search_documentation", {"query": query})

def aws_docs_read(url: str) -> Dict[str, Any] | str:
    cmd = os.environ.get("AWS_DOCS_MCP_CMD")
    if not cmd:
        return _no_mcp("AWS_DOCS_MCP_CMD not set")
    return call_tool(cmd, "read_documentation", {"url": url})

def aws_docs_recommend(url: str) -> Dict[str, Any] | str:
    cmd = os.environ.get("AWS_DOCS_MCP_CMD")
    if not cmd:
        return _no_mcp("AWS_DOCS_MCP_CMD not set")
    return call_tool(cmd, "recommend", {"url": url})
