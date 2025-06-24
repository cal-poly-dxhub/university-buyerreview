from utils import query_bedrock_with_multiple_files, try_parse_json_like
from prompt_loader import TASK_PROMPT_REGISTRY
from model_registry import ModelRegistry
import json


def run_data_sec_classification(state: dict) -> dict:
    parsed_data = state.get("parsed_data", {})
    if not parsed_data:
        return {"checklist_result": "❌ No parsed data available"}

    doc_text = json.dumps(parsed_data, indent=2)
    prompt = TASK_PROMPT_REGISTRY.get(
        "SECURITY_CLASSIFICATION", "").replace("{doc_text}", doc_text)

    response = query_bedrock_with_multiple_files(
        prompt=prompt,
        files=[],  # No files needed — we already have parsed data
        model_id=ModelRegistry.sonnet_3_5
    )

    parsed = try_parse_json_like(response)
    if not parsed:
        return {"checklist_result": "❌ Error in parsing response"}

    return {"service_info": service_info}


def goods_services_classification(service_info: dict) -> str:
    doc_text = json.dumps(service_info, indent=2)
    prompt = TASK_PROMPT_REGISTRY.get(
        "GOODS_SERVICES", "").replace("{doc_text}", doc_text)

    response = query_bedrock_with_multiple_files(
        prompt=prompt,
        files=[],
        model_id=ModelRegistry.sonnet_3_5
    )

    return response
