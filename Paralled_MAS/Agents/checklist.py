from utils import query_bedrock_with_multiple_pdfs, try_parse_json_like
from prompt_loader import TASK_PROMPT_REGISTRY
from model_registry import ModelRegistry
import json

def run_checklist(state: dict) -> dict:
    parsed = state.get("parsed_data", {})
    if not parsed:
        return {"checklist_result": "❌ No parsed data available"}

    doc_text = json.dumps(parsed, indent=2)
    prompt = TASK_PROMPT_REGISTRY.get("CHECKLIST", "").replace("{doc_text}", doc_text)

    response = query_bedrock_with_multiple_pdfs(
        prompt=prompt,
        files=[],  # No files needed — we already have parsed data
        model_id=ModelRegistry.sonnet_3_5
    )
    parsed = try_parse_json_like(response)
    return {"checklist_result": parsed}
