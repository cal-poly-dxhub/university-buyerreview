import re
from prompt_loader import TASK_PROMPT_REGISTRY
from utils import build_pdf_based_message, get_unique_purchasing_categories
from model_registry import ModelRegistry
import pandas as pd
import os

CSV_PATH = os.path.join("Data", "PC_Buyer_Assignments - Copy(Buyer Review).csv")
COLUMN_TO_SEARCH = "Purchasing Category"

def pc_llm_mapping(uploaded_files):
    base_prompt = TASK_PROMPT_REGISTRY.get("PC_CLASSIFICATION", "")
    pc_list = get_unique_purchasing_categories(CSV_PATH)
    formatted_list = ", ".join(f"'{cat}'" for cat in pc_list)
    prompt = base_prompt.replace("{pc_category_list}", formatted_list)

    response = build_pdf_based_message(ModelRegistry.haiku_3_5, prompt, uploaded_files)

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
