from prompt_loader import TASK_PROMPT_REGISTRY
from utils import create_doc_messages
from model_registry import ModelRegistry
from Agents.doc_parser import parse_documents_parallel
import streamlit as st
import boto3

bedrock = boto3.client(service_name='bedrock-runtime')

def phi_agreement_checker(uploaded_files):
    base_prompt = TASK_PROMPT_REGISTRY.get("PHI_AGREEMENT_CHECK", "")
    parsed_data = parse_documents_parallel(uploaded_files)
    final_prompt = base_prompt.replace("{parsed_data}", str(parsed_data))
    messages = create_doc_messages(final_prompt, uploaded_files)
    response = bedrock.converse(
        modelId=ModelRegistry.haiku_3_5,
        messages=messages,
        inferenceConfig={
            "temperature": 0
        }
    )
    return response