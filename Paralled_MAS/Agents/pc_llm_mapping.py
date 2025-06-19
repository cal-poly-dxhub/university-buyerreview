import re
from prompt_loader import TASK_PROMPT_REGISTRY
from utils import get_unique_purchasing_categories
from model_registry import ModelRegistry
import pandas as pd
import os
from Agents.doc_parser import parse_documents_parallel
from utils import create_doc_messages
import boto3

CSV_PATH = os.path.join("Data", "PC_Buyer_Assignments - Copy(Buyer Review).csv")
COLUMN_TO_SEARCH = "Purchasing Category"

bedrock = boto3.client(service_name='bedrock-runtime')

async def pc_llm_mapping(uploaded_files):
    base_prompt = TASK_PROMPT_REGISTRY.get("PC_CLASSIFICATION", "")
    pc_list = get_unique_purchasing_categories(CSV_PATH)
    formatted_list = ", ".join(f"'{cat}'" for cat in pc_list)
    parsed_data = await parse_documents_parallel(uploaded_files)

    final_prompt = base_prompt.replace("{parsed_data}", str(parsed_data)).replace("{pc_category_list}", formatted_list)
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

    llm_categories = re.findall(r"\{\{(.*?)\}\}", full_text)

    df = pd.read_csv(CSV_PATH)
    # Filter rows where column matches any extracted field (exact match)
    matched_df = df[df[COLUMN_TO_SEARCH].astype(str).isin(llm_categories)]

    return {
        "full_text": full_text,
        "categories": llm_categories,
        "response": response,
        "matched_df": matched_df
    }
