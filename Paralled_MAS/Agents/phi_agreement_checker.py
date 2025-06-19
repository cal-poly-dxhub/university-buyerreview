from prompt_loader import TASK_PROMPT_REGISTRY
from utils import build_pdf_based_message
from model_registry import ModelRegistry

def phi_agreement_checker(uploaded_files):
    base_prompt = TASK_PROMPT_REGISTRY.get("PHI_AGREEMENT_CHECK", "")
    response = build_pdf_based_message(ModelRegistry.haiku_3_5, base_prompt, uploaded_files)
    return response
