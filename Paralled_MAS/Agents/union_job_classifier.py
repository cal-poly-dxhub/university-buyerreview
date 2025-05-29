from utils import query_bedrock_with_multiple_pdfs, try_parse_json_like
from prompt_loader import TASK_PROMPT_REGISTRY
from model_registry import ModelRegistry
import json
from state import PipelineState

def union_job_check(state: PipelineState) -> PipelineState:
    parsed = state.get("parsed_data", {})
    if not parsed:
        return {"union_job_check": "❌ No parsed data available"}

    doc_text = json.dumps(parsed, indent=2)
    prompt = TASK_PROMPT_REGISTRY.get("UNION_JOB_CLASSIFICATION", "").replace("{doc_text}", doc_text)

    response = query_bedrock_with_multiple_pdfs(
        prompt=prompt,
        files=[],  
        model_id=ModelRegistry.haiku_3_5
    )
    parsed = try_parse_json_like(response)

    return {"union_job_check": parsed}
