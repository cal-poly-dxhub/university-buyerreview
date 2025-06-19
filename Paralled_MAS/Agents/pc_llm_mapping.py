import re
from prompt_loader import TASK_PROMPT_REGISTRY
from utils import build_pdf_based_message
from model_registry import ModelRegistry


def pc_llm_mapping(uploaded_files):
    base_prompt = TASK_PROMPT_REGISTRY.get("PC_CATEGORY_CLASSIFICATION", "")

    response = build_pdf_based_message(ModelRegistry.haiku_3_5, base_prompt, uploaded_files)

    output_message = response["output"]["message"]
    full_text = ""
    for block in output_message["content"]:
        if "text" in block:
            full_text += block["text"]

    llm_categories = re.findall(r"\{\{(.*?)\}\}", full_text)

    return {
        "full_text": full_text,
        "categories": llm_categories,
        "response": response
    }
