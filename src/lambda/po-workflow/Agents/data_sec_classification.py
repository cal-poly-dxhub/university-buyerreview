from utils import query_bedrock_with_multiple_files, try_parse_json_like
from prompt_loader import TASK_PROMPT_REGISTRY
from model_registry import ModelRegistry
from utils import create_doc_messages
from utils.embedding_utils_opensearch import search_similar_description
import json
import boto3
from state import PipelineState
import numpy as np


bedrock = boto3.client(service_name='bedrock-runtime')

def goods_services_classification(parsed_data) -> str:   
    base_prompt = TASK_PROMPT_REGISTRY.get("GOODS_SERVICES", "")
    final_prompt = base_prompt.replace("{parsed_data}", str(parsed_data))
    messages = create_doc_messages(final_prompt, [])

    print(messages)

    response = bedrock.converse(
        modelId=ModelRegistry.sonnet_3_7,
        messages=messages,
        inferenceConfig={
            "temperature": 0.3
        }
    )

    output_message = response["output"]["message"]
    full_text = ""
    for block in output_message["content"]:
        if "text" in block:
            full_text += block["text"]

    return full_text

async def run_data_sec_classification(state: PipelineState) -> PipelineState:
    parsed_data = state.get("parsed_data", {})
    if not parsed_data:
        return {
            "Data Security": {
                "error": "❌ No parsed data available"
            }
        }

    try:
        gs_result = goods_services_classification(parsed_data)
        print(gs_result)
        # Continue to data security classification regardless of goods/services
    except:
        print("error")


    base_prompt = TASK_PROMPT_REGISTRY.get("SECURITY_CLASSIFICATION", "")
    final_prompt = base_prompt.replace("{parsed_data}", str(parsed_data))
    messages = create_doc_messages(final_prompt, [])

    print(messages)

    response = bedrock.converse(
        modelId=ModelRegistry.sonnet_3_7,
        messages=messages,
        inferenceConfig={
            "temperature": 0.5
        }
    )

    output_message = response["output"]["message"]
    full_text = ""
    for block in output_message["content"]:
        if "text" in block:
            full_text += block["text"]

    parsed = try_parse_json_like(full_text)
    if not parsed:
        return {"data_security": "❌ Error in parsing response"}
    
    # print()
    # print(parsed["information_exchanged"])

    # similarity_search_classification = (search_similar_description(parsed["information_exchanged"])["institutional information type"], search_similar_description(parsed["information_exchanged"])["institutional information type"])
    # parsed["similarity_search_classification"] = similarity_search_classification

    return {"data_security": parsed}




