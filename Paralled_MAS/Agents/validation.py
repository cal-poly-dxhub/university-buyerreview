from utils import query_bedrock_with_multiple_pdfs, try_parse_json_like
from prompt_loader import TASK_PROMPT_REGISTRY
from model_registry import ModelRegistry
import json
from state import PipelineState


def validate_data(state: PipelineState) -> PipelineState:
    parsed = state.get("parsed_data", {})
    if not parsed:
        return {
            "validation_result": {
                "error": "❌ No parsed data available",
                "result": None,
                "raw": None
            }
        }

    try:
        doc_text = json.dumps(parsed, indent=2)
        prompt = TASK_PROMPT_REGISTRY.get(
            "DATA_VALIDATION", "").replace("{doc_text}", doc_text)

        response = query_bedrock_with_multiple_pdfs(
            prompt=prompt,
            files=[],
            model_id=ModelRegistry.sonnet_3_5
        )

        parsed_result = try_parse_json_like(response)

        return {
            "validation_result": {
                "error": None if parsed_result else "❌ Failed to parse validation response",
                "result": parsed_result,
                "raw": response
            }
        }

    except Exception as e:
        return {
            "validation_result": {
                "error": f"❌ Exception: {str(e)}",
                "result": None,
                "raw": None
            }
        }
