def build_specs_md(data, prompt):
    parts = ["# Specification"]
    if prompt:
        parts.append("## User Prompt")
        parts.append(prompt)
    for key, val in (data or {}).items():
        if isinstance(val, dict):
            parts.append(f"## {key} - {val.get('file','')}")
            parts.append(val.get("content", "")[:4000])
    return "\n\n".join(parts)

