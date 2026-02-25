import os
import pandas as pd

def parse_pdf(path):
    try:
        from pypdf import PdfReader
        reader = PdfReader(path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return {"pdf": {"file": os.path.basename(path), "content": text[:5000]}}
    except Exception:
        return {"pdf": {"file": os.path.basename(path), "content": ""}}

def parse_docx(path):
    try:
        import docx
        doc = docx.Document(path)
        text = "\n".join(p.text for p in doc.paragraphs)
        return {"docx": {"file": os.path.basename(path), "content": text[:5000]}}
    except Exception:
        return {"docx": {"file": os.path.basename(path), "content": ""}}

def read_text(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def parse_spec(path):
    return {"spec_text": read_text(path)} if path else {"spec_text": ""}

def parse_analytic(path):
    if not path:
        return {"analytics": {}}
    name = os.path.basename(path)
    ext = os.path.splitext(name)[1].lower()
    if ext in [".csv"]:
        df = pd.read_csv(path)
        return {"analytics": {"file": name, "columns": list(df.columns), "rows": len(df)}}
    if ext in [".json"]:
        import json
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            obj = json.load(f)
        return {"analytics": {"file": name, "keys": list(obj.keys())}}
    return {"analytics": {"file": name, "content": read_text(path)[:1000]}}

def parse_survey(path):
    return {"survey": {"file": os.path.basename(path), "content": read_text(path)[:2000]}} if path else {"survey": {}}

def parse_inputs(spec_file, analytics_files, survey_files):
    data = {}
    if spec_file:
        data.update(parse_spec(spec_file))
    for a in analytics_files:
        data.update(parse_analytic(a))
    for s in survey_files:
        data.update(parse_survey(s))
    return data

def parse_any(files):
    data = {}
    for f in files or []:
        ext = os.path.splitext(f)[1].lower()
        if ext in [".md", ".txt"]:
            data.update({"doc": {"file": os.path.basename(f), "content": read_text(f)[:5000]}})
        elif ext == ".csv":
            data.update(parse_analytic(f))
        elif ext == ".json":
            data.update(parse_analytic(f))
        elif ext in [".xls", ".xlsx"]:
            try:
                df = pd.read_excel(f)
                data.update({"excel": {"file": os.path.basename(f), "columns": list(df.columns), "rows": len(df)}})
            except Exception:
                data.update({"excel": {"file": os.path.basename(f), "content": ""}})
        elif ext == ".pdf":
            data.update(parse_pdf(f))
        elif ext == ".docx":
            data.update(parse_docx(f))
        else:
            data.update({"file": {"file": os.path.basename(f), "content": read_text(f)[:2000]}})
    return data
