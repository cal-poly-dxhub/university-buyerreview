import re 
import os
import json
import boto3

bedrock = boto3.client(service_name='bedrock-runtime')

def clean_file_name(file_name):
    base_name = os.path.basename(file_name)
    name, _ = os.path.splitext(base_name)
    cleaned_name = re.sub(r"[^\w\s\-\(\)\[\]]", "", name)
    cleaned_name = re.sub(r"\s+", " ", cleaned_name).strip()
    return cleaned_name if cleaned_name else "Document"

def try_parse_json_like(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            start = min([i for i in (
                text.find('['), text.find('{')) if i != -1])
            end = max([text.rfind(']'), text.rfind('}')]) + 1
            cleaned = text[start:end].strip()
            return json.loads(cleaned)
        except Exception:
            return None
        
def create_doc_messages(prompt, files):
    content = [{"text": prompt}]
    for i, file in enumerate(files):
        safe_name = clean_file_name(file.name)
        file_bytes = file.read()
        content.insert(i, {
            "document": {
                "name": safe_name,
                "format": "pdf",
                "source": {
                    "bytes": file_bytes
                }
            }
        })
    return [{"role": "user", "content": content}]

def query_bedrock_with_multiple_pdfs(prompt, files, model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0"):
    messages = create_doc_messages(prompt, files)
    response = bedrock.converse(
        modelId=model_id,
        messages=messages,
        inferenceConfig={
            "maxTokens": 100000,
            "temperature": 0
        }
    )
    return response['output']['message']['content'][0]['text']