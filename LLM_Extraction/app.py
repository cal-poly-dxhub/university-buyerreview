import streamlit as st
import boto3
import json
import re

# Create the Bedrock client
session = boto3.Session(region_name="us-west-2")
bedrock = session.client(service_name='bedrock-runtime')

def clean_file_name(file_name):
    # Replace all non-allowed characters and compress whitespace
    cleaned = re.sub(r"[^\w\s\-\(\)\[\]]", "", file_name)  # remove unsupported characters
    cleaned = re.sub(r"\s+", " ", cleaned).strip()  # compress whitespace
    return cleaned if cleaned else "Document"

def create_doc_messages(prompt, files):
    content = [{ "text": prompt }]
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
    return [{ "role": "user", "content": content }]

def query_bedrock_with_multiple_pdfs(prompt, files, model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0"):
    messages = create_doc_messages(prompt, files)
    response = bedrock.converse(
        modelId=model_id,
        messages=messages,
        inferenceConfig={
            "maxTokens": 10000,
            "temperature": 0
        }
    )
    return response['output']['message']['content'][0]['text']

# Streamlit App
st.set_page_config(page_title="Direct PDF Upload with Claude")
st.title("Upload PDFs (Raw Bytes) for LLM Processing")

uploaded_files = st.file_uploader("Upload your PDF documents", type=["pdf"], accept_multiple_files=True)

prompt = """Data Validation Prompt
Your task is to compare properties mentioned in multiple documents, including a PO file, and validate their consistency.
Output Format

Provide your response as pure JSON.
Only include properties that appear in at least two documents.
For each property, indicate whether values match across documents with one of these values only: "Yes", "No", or "Mostly Yes".
Only list documents as sources if they explicitly mention the property value.

JSON Structure
json{
  "Property 1": {
    "match": "Yes|No|Mostly Yes",
    "Source 1": "Value 1",
    "Source 2": "Value 2",
    "Source 3": "Value 3"
  },
  "Property 2": {
    "match": "Yes|No|Mostly Yes",
    "Source 1": "Value 1",
    "Source 2": "Value 2"
  }
}
Rules

If a property isn't mentioned in a document, don't include that document as a source.
Only validate data that is explicitly mentioned.
Omit any property that appears in only one document.
The "match" value must be one of: "Yes", "No", or "Mostly Yes".
Focus only on data about the company being contracted with, not other companies' proposals.
"""
if uploaded_files:
    prompt = st.text_area("Prompt to send with PDFs", value=prompt)

    if st.button("Send to Bedrock"):
        with st.spinner("Processing multiple PDFs together..."):
            response_text = query_bedrock_with_multiple_pdfs(prompt, uploaded_files)
            st.subheader("Response for All Files")
            st.write(response_text)
