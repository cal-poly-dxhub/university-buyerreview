from prompt_loader import TASK_PROMPT_REGISTRY
from utils import create_doc_messages
from model_registry import ModelRegistry
import boto3
from state import PipelineState

bedrock = boto3.client(service_name='bedrock-runtime')


async def phi_agreement_checker(state: PipelineState) -> PipelineState:
    parsed_data = state.get("parsed_data", {})
    if not parsed_data:
        return {
            "phi_agreement": {
                "error": "❌ No parsed data available"
            }
        }
    base_prompt = TASK_PROMPT_REGISTRY.get("PHI_AGREEMENT_CHECK", "")
    final_prompt = base_prompt.replace("{parsed_data}", str(parsed_data))
    messages = create_doc_messages(final_prompt, [])
    response = bedrock.converse(
        modelId=ModelRegistry.haiku_3_5,
        messages=messages,
        inferenceConfig={
            "temperature": 0
        }
    )
    output_message = response["output"]["message"]
    full_text = ""
    for block in output_message["content"]:
        if "text" in block:
            full_text += block["text"]
    return {
        "phi_agreement": {
            "full_text": full_text,
            "stop_reason": response.get('stopReason', None),
            "usage": response.get('usage', None),
        }
    }
