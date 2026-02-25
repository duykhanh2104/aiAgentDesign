# AI Architecture Agent Orchestration

## What This App Does

- Chat-based architecture assistant with document ingestion (PDF, DOCX, Excel, CSV, JSON, Markdown).
- Generates architecture diagrams with official cloud icons (AWS/GCP via PlantUML; Azure/on‑prem via diagrams).
- Optionally uses AWS MCP servers to render diagrams and fetch official AWS documentation.
- Produces UML (PlantUML) and topology (Mermaid) alongside diagrams.
- Gradio UI with Processing/Stop controls for long-running tasks.

## Quick Start

1) Prerequisites
- Python 3.10+
- Windows PowerShell or any terminal

2) Create virtual environment and install dependencies
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

3) Optional: Set LLM API keys (only used if MCP-first is off or you choose an LLM in UI)
- PowerShell examples:
```
$env:OPENAI_API_KEY = "sk-..."
$env:ANTHROPIC_API_KEY = "sk-ant-..."
$env:GOOGLE_API_KEY   = "AIza..."
```

4) Graphviz (only needed for Azure/on‑prem fallback via diagrams)
- Download from https://graphviz.org/download/ and ensure `dot` is on PATH.
- You do NOT need Graphviz when using AWS MCP or PlantUML paths for AWS/GCP.

5) Run the app
```
python app.py
```
Open http://127.0.0.1:7860/ and:
- Upload documents and/or images
- Choose model (if not using MCP-first)
- Enter your prompt and click Send
- You can hover over the disabled “Processing…” button to reveal Stop and cancel the run

## MCP-First Mode (Recommended for AWS)

When MCP-first is enabled, the app uses tools instead of LLMs whenever possible:
- AWS Diagram MCP server for rendering PNG diagrams with official AWS icons
- AWS Documentation MCP server for searching/reading official AWS docs in Markdown

Enable MCP-first and configure servers:
```
$env:USE_MCP_FIRST = "true"
$env:AWS_DIAGRAM_MCP_CMD = "uvx awslabs.aws-diagram-mcp-server"
$env:AWS_DOCS_MCP_CMD   = "uvx awslabs.aws-documentation-mcp-server"
```
Notes:
- You may need `pip install uv` and (if required by the server) Graphviz on your system.
- With MCP-first on and at least one MCP server configured, UI avoids LLM fallback for errors and runs tool pipeline directly.

## Cost Controls for LLM Mode

The planner is optimized to avoid sending document context. For direct LLM chats, you can further cap context:
```
$env:DOC_CONTEXT_MAX_DOCS  = "3"
$env:DOC_CONTEXT_MAX_CHARS = "1500"
$env:DOC_CONTEXT_TOTAL_CHARS = "6000"
```

## Typical Prompts
Reference: https://aws.amazon.com/vi/blogs/machine-learning/build-aws-architecture-diagrams-using-amazon-q-cli-and-mcp/
- "Please create a diagram showing an EC2 instance in a VPC connecting to an external S3 bucket. Include essential networking components (VPC, subnets, Internet Gateway, Route Table), security elements (Security Groups, NACLs), and clearly mark the connection between EC2 and S3. Label everything appropriately concisely and indicate that all resources are in the us-east-1 region. Check for AWS documentation to ensure it adheres to AWS best practices before you create the diagram."


## Troubleshooting

- No AWS icons in Graphviz Online: the app does not rely on local images for AWS/GCP; diagrams are rendered via PlantUML or MCP servers.
- `dot` not found: install Graphviz and add to PATH (only for Azure/on‑prem fallback).
- LLM errors: ensure the corresponding API key is set (OPENAI_API_KEY / ANTHROPIC_API_KEY / GOOGLE_API_KEY).
- MCP errors: ensure `USE_MCP_FIRST=true` and `AWS_DIAGRAM_MCP_CMD` / `AWS_DOCS_MCP_CMD` are set and resolvable on PATH.

## Repository Entry Points

- App/UI: `app.py`
- Orchestrator: `core/orchestrator.py`
- Agents: `agents/architecture_agent.py`, `agents/uml_agent.py`, `agents/topology_agent.py`
- Diagram generation: `tools/diagrams_adapter.py`, `tools/plantuml.py`
- MCP tooling: `tools/mcp_client.py`
- LLM routing: `tools/llm_router.py`
