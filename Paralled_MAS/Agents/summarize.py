from state import PipelineState
import json
import markdown2
from io import BytesIO
from utils import query_bedrock_with_multiple_files
from model_registry import ModelRegistry
from prompt_loader import TASK_PROMPT_REGISTRY
from weasyprint import HTML

def summarize_and_generate_pdf(state: PipelineState) -> PipelineState:
    summary_data = extract_summary(state)
    markdown = summarize_with_claude(summary_data)
    pdf_bytes = markdown_to_pdf_bytes(markdown)
    return {"pdf_summary": pdf_bytes}

def extract_summary(state: dict) -> dict:
    return {
        "Checklist": state.get("checklist_result"),
        "PO Exists": state.get("po_check"),
        "PO Validation": state.get("validation_result"),
        "Union Job Check": state.get("union_result"),
        "PHI Agreement": state.get("phi_check"),
        "PC Classification": state.get("pc_classification"),
        "Data Security Classification": state.get("data_sec_result"),
    }

def summarize_with_claude(summary_json: dict) -> str:
    base_prompt = TASK_PROMPT_REGISTRY.get("SUMMARY_PROMPT", "")
    full_prompt = base_prompt + "\n\n" + json.dumps(summary_json, indent=2)

    response = query_bedrock_with_multiple_files(
        prompt=full_prompt,
        files=[],
        model_id=ModelRegistry.haiku_3_5
    )
    return response

def markdown_to_pdf_bytes(markdown_string: str) -> bytes:
    # Convert Markdown to HTML
    html_body = markdown2.markdown(markdown_string)

    # Basic styling and wrapping
    html_content = f"""
    <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: 'Helvetica', sans-serif;
                    margin: 40px;
                    line-height: 1.6;
                }}
                h1, h2 {{
                    color: #2c3e50;
                }}
                ul {{
                    margin-left: 20px;
                }}
                .section {{
                    margin-bottom: 30px;
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 20px;
                }}
            </style>
        </head>
        <body>
            {html_body}
        </body>
    </html>
    """

    # Generate PDF from HTML using WeasyPrint
    buffer = BytesIO()
    HTML(string=html_content).write_pdf(buffer)
    buffer.seek(0)
    return buffer.read()
