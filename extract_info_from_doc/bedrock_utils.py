# Python Built-Ins:
import os
from typing import Optional
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
    if runtime:
        service_name = 'bedrock-runtime'
    else:
        service_name = 'bedrock'

    bedrock_runtime = boto3.client(
        service_name=service_name,
        region_name="us-west-2",  # Change to your preferred region
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token  # Optional
    )

    print("boto3 Bedrock client successfully created!")
    print(bedrock_runtime._endpoint)
    return bedrock_runtime

bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-west-2")

def invoke_model(prompt):
    """
    Invokes Amazon bedrock model to run an inference
    using the input provided in the request body.
    
    Args:
        body (dict): The invokation body to send to bedrock
        model_id (str): the model to query
        accept (str): input accept type
        content_type (str): content type
    Returns:
        Inference response from the model.
    """
    MESSAGES = [{"role": "user", "content": prompt}] 

    BODY={
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": MESSAGES
        }

    MODELID = "anthropic.claude-3-5-sonnet-20240620-v1:0"  # change this to use a different version from the model provider
    ACCEPT = "application/json"
    CONTENTTYPE = "application/json"

    try:
        start_time = time.time()
        response = bedrock_runtime.invoke_model(
            body=json.dumps(BODY), 
            modelId=MODELID, 
            accept=ACCEPT, 
            contentType=CONTENTTYPE
        )
        elapsed_time = time.time() - start_time    
#        print(f"Model invocation took {elapsed_time:.3f} seconds.")  #Uncomment for model invocation time

        response_body = json.loads(response.get("body").read())
        output = response_body.get("content")[0].get("text")
        stop_reason = response_body.get("stop_reason", "") 
        

        return output, stop_reason

    # Handle errors
    except ClientError as err:
        print(f"{err.response['Error']['Code']}: {err.response['Error']['Message']}")
        return "", ""
    except ValueError as err:
        print(err)
        return "", ""
    except ReadTimeoutError as err:
        print(err)
        return "", ""


    except Exception as e:
        print(f"Couldn't invoke {MODELID}")
        raise e

def invoke_until_completion(prompt: str):
    response, stop_reason = invoke_model(prompt)
    while stop_reason == "max_tokens":
        response, stop_reason = invoke_model(f"{prompt}\n Continue from: {response}\n ")
    return response

def make_prompt(prompt_list, template, document) -> str:
    """
    Creates the full prompt to be passed to the LLM.
    
    :param prompt_list: List of the prompts to be passed before and after the template,
    :param template: One-shot JSON template for the LLM to use as a format.
    :param document: Document you would like to parse.
    :return: Prompt containing all relevant information in the correct format.
    """

    # Tags needed to invoke Claude
    human_tag = "Human: "
    assistant_tag = "Assistant:"

    # Format prompt
    pre_prompt, post_prompt = prompt_list
    prompt = f"{document}\n\n{human_tag}{pre_prompt}\n\n{template}\n\n{post_prompt}\n\n{assistant_tag}"

    return prompt

def extract_json_to_text(json_filepath, output_filepath=None):
    """
    Extracts data from a JSON file and returns it as a formatted text string.

    Args:
        json_filepath (str): The path to the JSON file.
        output_filepath (str, optional): The path to save the output text file. 
                                       If None, the text will be printed to the console.

    Returns:
        str: A string representation of the extracted JSON data.
    """
    try:
        with open(json_filepath, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
         return f"Error: File not found: {json_filepath}"
    except json.JSONDecodeError:
        return f"Error: Invalid JSON format in {json_filepath}"

    return data

# Concatenate pages together with page number between pages
reader = PdfReader('Statement of work examples/SOWExample6.pdf')
contents = ''
for page in reader.pages:
    contents += page.extract_text()

# Create prompt 
pre_prompt = "Human: You are an AI assistant adept at parsing documents and extracting key details with meticulous accuracy. Your sole purpose is to populate the provided JSON template completely and precisely, without injecting any of your own interpretations. Behave like an impartial information extraction machine."
post_prompt = "For each relevant section in the document EXCLUDING DOCTYPE, fill out the corresponding field in the JSON structure. Leave no stone unturned - search thoroughly to identify and accurately record all pertinent details, regardless of how trivial. For each section in the JSON template, if no applicable value exists in the document, use 'null'. Do not remove any sections from the original template, all original fields should be present, mark them with null if not present in the document.Handle ambiguities by listing the most accurate extractions.If you discover additional attributes not matching the template, judiciously append them under 'Misc' only doing so if the attribute cannot be resolved to fit in the template, formatting new entries to maintain machine readability.When finished, return only the fully populated JSON object containing the extracted data from the document. Make sure this JSON object still contains all the original fields from the template even if they are marked as null. Do this multiple times to make sure you extract every relevant entity and relationship with a high level of confidence. Complete multiple epochs and estimate your confidence level [low, medium, high, very high]. Read out your results for each epoch and number each epoch. Place the final, high confidence results in the variable results for downstream ETL consumption and the final json object in <json></json> tags.Demonstrate your technical accuracy through the completeness, precision and formatting of the structured information you provide."

prompt = [pre_prompt, post_prompt]

# Check if prompt fits within our token limit
full_length_prompt = make_prompt(prompt, extract_json_to_text("config1.json"), contents)