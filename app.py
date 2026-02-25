import gradio as gr
import os
from tools.llm_router import route, preflight
from core.orchestrator import Orchestrator
from core.planner import make_plan
from core.validator import validate_plan
from core.executor import execute
import concurrent.futures
import logging

def _env_bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return str(val).strip().lower() in ("1", "true", "yes", "on")

def _mcp_tools_ready() -> bool:
    return bool(os.environ.get("AWS_DIAGRAM_MCP_CMD") or os.environ.get("AWS_DOCS_MCP_CMD"))

def _use_mcp_first() -> bool:
    return _env_bool("USE_MCP_FIRST", False) and _mcp_tools_ready()

def run_llm(documents, images, models, message, history, timeout=30):
    sel_models = models if isinstance(models, (list, tuple)) else ([models] if models else [])
    prompt_history = (history or []) + [{"role": "user", "content": message or ""}]
    pf = preflight(sel_models)
    if pf and not any(pf.values()):
        return "Error connecting/API key: Please check API key and internet connection."
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        for attempt in range(2):
            future = executor.submit(route, sel_models, documents, prompt_history, images)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                future.cancel()
                logging.exception("LLM timeout")
                if attempt == 0:
                    continue
                return f"Error: LLM did not respond after {timeout}s (timeout)."
            except Exception as e:
                logging.exception("LLM call failed")
                if attempt == 0:
                    continue
                return f"Error calling LLM: {e}"

def run_tools_and_draw(documents, message):
    orch = Orchestrator(os.path.join(os.getcwd(), "outputs"))
    out = orch.run(documents, message)
    summary = "Generated specs.md and diagrams. Files:\n" + "\n".join(out.get("images", []))
    code = "\n\n" + "\n\n".join(out.get("texts", [])) if out.get("texts") else ""
    return summary + code

def run_agent(documents, images, models, message, history):
    plan = make_plan(models, documents, images, message, history)
    vplan = validate_plan(plan)
    return execute(vplan, documents, images, message)

def chat_submit(documents, images, models, message, history):
    try:
        if _use_mcp_first():
            assistant_reply = run_tools_and_draw(documents, message)
        else:
            state = run_agent(documents, images, models, message, history)
            assistant_reply = state.get("reply", "")
        messages = history or []
        messages.append({"role": "user", "content": message or ""})
        messages.append({"role": "assistant", "content": assistant_reply})
        return (
            gr.update(value=messages),
            messages,
            gr.update(visible=True),
        )
    except Exception:
        logging.exception("Unexpected error in chat_submit")
        messages = history or []
        messages.append({"role": "user", "content": message or ""})
        if _use_mcp_first():
            assistant_reply = "Tool execution failed. Please verify MCP servers configuration and try again."
        else:
            assistant_reply = run_llm(documents, images, models, message, history, timeout=30)
            if ("Error:" in assistant_reply) or ("Cannot call model" in assistant_reply):
                assistant_reply = run_tools_and_draw(documents, message)
        messages.append({"role": "assistant", "content": assistant_reply})
        return (
            gr.update(value=messages),
            messages,
            gr.update(visible=True),
        )

def set_processing():
    return gr.update(value="Processing...", interactive=False), gr.update(visible=True)

def reset_processing():
    return gr.update(value="Send", interactive=True), gr.update(visible=False)

CUSTOM_CSS = """
#stop-btn {
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s ease-in-out;
}
#send-btn:disabled:hover + #stop-btn {
    opacity: 1; 
    pointer-events: auto;
}
"""

with gr.Blocks(title="AI Architecture Chat", css=CUSTOM_CSS) as agentDesign:
    gr.Markdown("Upload documents / chat with the AI to generate architecture")
    documents = gr.File(label="Documents", file_count="multiple", type="filepath", file_types=[".pdf", ".md", ".txt", ".csv", ".json", ".docx", ".xls", ".xlsx"])
    images = gr.File(label="Images", file_count="multiple", type="filepath", file_types=[".png", ".jpg", ".jpeg", ".webp"])
    models = gr.Dropdown(choices=["openai:gpt-4o-mini", "anthropic:claude-3.5-sonnet", "gemini:gemini-1.5-flash"], label="Model", value="openai:gpt-4o-mini")
    chatbot = gr.Chatbot(label="Chat")
    with gr.Row():
        chat_input = gr.Textbox(placeholder="Enter your message...", scale=9)
        send_btn = gr.Button("Send", scale=1, elem_id="send-btn")
        stop_btn = gr.Button("Stop", scale=1, visible=False, elem_id="stop-btn")
    chat_history = gr.State([])

    start_click = send_btn.click(set_processing, inputs=None, outputs=[send_btn, stop_btn])
    run_click = start_click.then(chat_submit, inputs=[documents, images, models, chat_input, chat_history], outputs=[chatbot, chat_history, send_btn])
    end_click = run_click.then(reset_processing, inputs=None, outputs=[send_btn, stop_btn])

    start_submit = chat_input.submit(set_processing, inputs=None, outputs=[send_btn, stop_btn])
    run_submit = start_submit.then(chat_submit, inputs=[documents, images, models, chat_input, chat_history], outputs=[chatbot, chat_history, send_btn])
    end_submit = run_submit.then(reset_processing, inputs=None, outputs=[send_btn, stop_btn])

    stop_btn.click(fn=reset_processing, inputs=None, outputs=[send_btn, stop_btn], cancels=[run_click, run_submit])

if __name__ == "__main__":
    agentDesign.queue()
    agentDesign.launch()
