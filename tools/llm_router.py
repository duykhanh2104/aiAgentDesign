import os
import logging
from typing import List, Dict, Any
import base64
import requests
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def NB(sv, default):
    try:
        return int(os.getenv(sv, str(default)))
    except Exception:
        return default

def _docs_to_context(documents: List[str]) -> str:
    try:
        from .parsers import parse_any
        data = parse_any(documents)
        max_docs = NB("DOC_CONTEXT_MAX_DOCS", 3)
        max_chars = NB("DOC_CONTEXT_MAX_CHARS", 1500)
        parts = []
        for k, v in list(data.items())[:max_docs]:
            if isinstance(v, dict):
                content = v.get("content", "")[:max_chars]
                if content:
                    parts.append(f"[{k}] {v.get('file','')}:\n{content}")
        total = "\n\n".join(parts)
        hard_cap = NB("DOC_CONTEXT_TOTAL_CHARS", 6000)
        return total[:hard_cap]
    except Exception:
        return ""

def _call_openai(model: str, messages: List[Dict[str, str]]) -> str:
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return "OPENAI_API_KEY not configured"
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(model=model, messages=messages)
        return resp.choices[0].message.content or ""
    except Exception as e:
        return f"OpenAI error: {e}"

def _call_anthropic(model: str, messages: List[Dict[str, str]]) -> str:
    try:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return "ANTHROPIC_API_KEY not configured"
        client = anthropic.Anthropic(api_key=api_key)
        # Convert to Anthropic format: system + user turns
        system_msg = "" 
        content = []
        for m in messages:
            if m.get("role") == "system":
                system_msg = m.get("content", "")
            elif m.get("role") == "user":
                content.append({"role": "user", "content": m.get("content", "")})
            elif m.get("role") == "assistant":
                content.append({"role": "assistant", "content": m.get("content", "")})
        msg = client.messages.create(model=model, max_tokens=1000, system=system_msg or None, messages=content)
        return "".join([b.text for b in msg.content if hasattr(b, "text")])
    except Exception as e:
        return f"Anthropic error: {e}"

def _call_gemini(model: str, messages: List[Dict[str, str]]) -> str:
    try:
        import google.generativeai as genai
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return "GOOGLE_API_KEY not configured"
        genai.configure(api_key=api_key)
        sys = "" 
        parts = []
        for m in messages:
            if m.get("role") == "system":
                sys = m.get("content", "")
            elif m.get("role") in ("user", "assistant"):
                parts.append(f"{m.get('role')}: {m.get('content','')}")
        model_obj = genai.GenerativeModel(model)
        prompt = (sys + "\n\n" + "\n".join(parts)).strip()
        resp = model_obj.generate_content(prompt)
        return getattr(resp, "text", "") or ""
    except Exception as e:
        return f"Gemini error: {e}"

def _images_to_context(images: List[str]) -> List[Dict[str, Any]]:
    items = []
    for p in images or []:
        try:
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            mime = "image/png"
            if p.lower().endswith(".jpg") or p.lower().endswith(".jpeg"): mime = "image/jpeg"
            elif p.lower().endswith(".webp"): mime = "image/webp"
            items.append({"data": b64, "mime": mime, "name": os.path.basename(p)})
        except Exception:
            items.append({"data": None, "mime": None, "name": os.path.basename(p)})
    return items

def call_openai_chat(model: str, messages: list) -> str:
    """
    messages: list of {"role": "system|user|assistant", "content": "..."}
    Returns assistant text or raises Exception
    """
    try:
        resp = client.chat.completions.create(model=model, messages=messages)
        # safe-extract content
        choice = resp.choices[0]
        # choice.message may be dict-like
        content = None
        if hasattr(choice, "message"):
            msg = choice.message
            content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)
        if content is None:
            content = str(choice)
        return content
    except Exception as e:
        logging.exception("OpenAI call failed")
        raise

def route(models: List[str], documents: List[str], chat_messages: List[Dict[str, str]], images: List[str] | None = None, include_docs: bool = True) -> str:
    ctx = _docs_to_context(documents) if include_docs else ""
    imgs = _images_to_context(images or [])
    messages = chat_messages.copy()
    if ctx:
        messages = [{"role": "system", "content": "Document context:\n" + ctx}] + messages
    for m in models or []:
        if m.startswith("openai:"):
            model = m.split(":",1)[1]
            if imgs:
                try:
                    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                    content = []
                    content.append({"type":"text","text":"".join([x.get('content','') for x in messages if x.get('role')=='user'])})
                    for im in imgs:
                        if im["data"]:
                            content.append({"type":"image_url","image_url":{"url":f"data:{im['mime']};base64,{im['data']}"}})
                    resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":content}])
                    out = resp.choices[0].message.content or ""
                except Exception as e:
                    out = f"OpenAI error: {e}"
            else:
                out = _call_openai(model, messages)
            if out and "API_KEY" not in out and "error" not in out.lower():
                return out
        elif m.startswith("anthropic:"):
            model = m.split(":",1)[1]
            out = _call_anthropic(model, messages)
            if out and "API_KEY" not in out and "error" not in out.lower():
                return out
        elif m.startswith("vertex:") or m.startswith("google:") or m.startswith("gemini:"):
            model = m.split(":",1)[1]
            try:
                import google.generativeai as genai
                api_key = os.environ.get("GOOGLE_API_KEY")
                if not api_key:
                    out = "GOOGLE_API_KEY not configured"
                else:
                    genai.configure(api_key=api_key)
                    sys = "" 
                    parts = []
                    for mobj in messages:
                        if mobj.get("role") == "system": sys = mobj.get("content", "")
                        elif mobj.get("role") in ("user","assistant"):
                            parts.append(mobj.get("content",""))
                    model_obj = genai.GenerativeModel(model)
                    # Gemini can take images via bytes
                    gem_parts = [sys + "\n\n" + "\n".join(parts)]
                    for im in imgs:
                        if im["data"]:
                            import base64
                            gem_parts.append({"mime_type": im["mime"] or "image/png", "data": base64.b64decode(im["data"])})
                    resp = model_obj.generate_content(gem_parts)
                    out = getattr(resp, "text", "") or ""
            except Exception as e:
                out = f"Gemini error: {e}"
            if out and "API_KEY" not in out and "error" not in out.lower():
                return out
    return "Cannot call model. Check model choices and environment API keys."

def preflight(models: List[str]) -> Dict[str, bool]:
    status = {}
    for m in models or []:
        try:
            if m.startswith("openai:"):
                api_key = os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    status["openai"] = False
                else:
                    r = requests.get("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {api_key}"}, timeout=5)
                    status["openai"] = (r.status_code == 200)
            elif m.startswith("anthropic:"):
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                status["anthropic"] = bool(api_key)
            elif m.startswith("gemini:") or m.startswith("google:") or m.startswith("vertex:"):
                api_key = os.environ.get("GOOGLE_API_KEY")
                status["gemini"] = bool(api_key)
        except Exception:
            if m.startswith("openai:"):
                status["openai"] = False
    return status
