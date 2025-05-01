# Python Built-Ins:
import os
from typing import Optional, Tuple
import sys
import json
import time

# External Dependencies:
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from botocore.exceptions import ReadTimeoutError
import botocore
from pypdf import PdfReader

bedrock_runtime = None

# If you'd like to try your own prompt, edit this parameter!
# prompt_data = """Human: Command: Write a paragraph why Generative AI is an important technology to understand.
# Assistant:
# """


def get_bedrock_client(
    runtime: Optional[bool] = True,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None
):
    service_name = 'bedrock-runtime' if runtime else 'bedrock'
    return boto3.client(
        service_name=service_name,
        region_name="us-west-2",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token
    )

bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-west-2")

def invoke_model(prompt: str) -> Tuple[str, str]:
    """Invokes Amazon Bedrock model with the given prompt."""
    messages = [{"role": "user", "content": prompt}]
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": messages
    }
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    
    try:
        response = bedrock_runtime.invoke_model(
            body=json.dumps(body),
            modelId=model_id,
            accept="application/json",
            contentType="application/json"
        )
        response_body = json.loads(response.get("body").read())
        output = response_body.get("content")[0].get("text")
        stop_reason = response_body.get("stop_reason", "")
        return output, stop_reason
    except Exception as e:
        print(f"Error invoking model: {str(e)}")
        return "", ""

def invoke_until_completion(prompt: str) -> str:
    """Invokes model repeatedly until completion if max tokens reached."""
    response, stop_reason = invoke_model(prompt)
    while stop_reason == "max_tokens":
        response, stop_reason = invoke_model(f"{prompt}\n Continue from: {response}\n ")
    return response

def make_prompt(prompt_text: str, document: str) -> str:
    """Creates the full prompt to be passed to the LLM."""
    return f"{prompt_text}\n\n{document}"

def extract_text_with_form_fields(doc) -> str:
    """Extracts text and form fields from a PDF document."""
    reader = PdfReader(doc)
    text = ""
    
    # Extract regular text
    for page in reader.pages:
        text += page.extract_text() + "\n"
    
    # Extract form fields
    if reader.get_fields():
        for field_name, field_value in reader.get_fields().items():
            if field_value:
                text += f"{field_name}: {field_value}\n"
    
    return text

def try_parse_json_like(text: str) -> dict:
    """Attempts to parse JSON from text, handling various formats."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            cleaned_text = text[start:end]
            return json.loads(cleaned_text)
        except Exception:
            return None

# # Concatenate pages together with page number between pages
# reader = PdfReader('Statement of work examples/SOWExample6.pdf')
# contents = ''
# for page in reader.pages:
#     contents += page.extract_text()

# # Create prompt 
# pre_prompt = "Human: You are an AI assistant adept at parsing documents and extracting key details with meticulous accuracy. Your sole purpose is to populate the provided JSON template completely and precisely, without injecting any of your own interpretations. Behave like an impartial information extraction machine."
# post_prompt = "For each relevant section in the document EXCLUDING DOCTYPE, fill out the corresponding field in the JSON structure. Leave no stone unturned - search thoroughly to identify and accurately record all pertinent details, regardless of how trivial. For each section in the JSON template, if no applicable value exists in the document, use 'null'. Do not remove any sections from the original template, all original fields should be present, mark them with null if not present in the document.Handle ambiguities by listing the most accurate extractions.If you discover additional attributes not matching the template, judiciously append them under 'Misc' only doing so if the attribute cannot be resolved to fit in the template, formatting new entries to maintain machine readability.When finished, return only the fully populated JSON object containing the extracted data from the document. Make sure this JSON object still contains all the original fields from the template even if they are marked as null. Do this multiple times to make sure you extract every relevant entity and relationship with a high level of confidence. Complete multiple epochs and estimate your confidence level [low, medium, high, very high]. Read out your results for each epoch and number each epoch. Place the final, high confidence results in the variable results for downstream ETL consumption and the final json object in <json></json> tags.Demonstrate your technical accuracy through the completeness, precision and formatting of the structured information you provide."

# prompt = [pre_prompt, post_prompt]

# # Check if prompt fits within our token limit
# full_length_prompt = make_prompt(prompt, contents)