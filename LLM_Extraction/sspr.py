import streamlit as st
import boto3
import json
import re
import os

# Create Bedrock client
session = boto3.Session(region_name="us-west-2")
bedrock = session.client(service_name='bedrock-runtime')

def clean_file_name(file_name):
    base_name = os.path.basename(file_name)
    name, _ = os.path.splitext(base_name)
    cleaned_name = re.sub(r"[^\w\s\-\(\)\[\]]", "", name)
    cleaned_name = re.sub(r"\s+", " ", cleaned_name).strip()
    return cleaned_name if cleaned_name else "Document"

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
            "maxTokens": 10000,
            "temperature": 0
        }
    )
    return response['output']['message']['content'][0]['text']

def try_parse_json_like(text):
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

def render_boolean(key, value, use_indicator=True):
    val = str(value).strip().lower()
    if use_indicator and val in {"yes", "true", "agree"}:
        st.success(f"✅ **{key}**: {value}")
    elif use_indicator and val in {"no", "false", "disagree"}:
        st.error(f"❌ **{key}**: {value}")
    elif use_indicator:
        st.info(f"**{key}**: {value}")
    else:
        st.markdown(f"- **{key}**: {value}")

def render_structured_output(data):
    # Render top-level keys
    top_fields = ["SSPR Found", "Funding Source", "Dollar Amount", "Desired Supplier"]
    for field in top_fields:
        value = data.get(field, "N/A")
        render_boolean(field, value)

    # Source Selection
    if "Source Selection" in data:
        st.subheader("📂 Source Selection")
        for k, v in data["Source Selection"].items():
            st.markdown(f"- **{k}**: {v}")

    # Required Sections
    if "Required Sections" in data:
        st.subheader("📄 Required Sections")
        for section in data["Required Sections"]:
            st.markdown(f"- {section}")

    # Section Details
    if "Section Details" in data:
        st.subheader("📘 Section Details")
        for section in data["Section Details"]:
            section_title = f"**{section.get('Section Number', '')}. {section.get('Section Name', '')}**"
            is_complete = section.get("Is Complete", False)
            st.markdown(f"### {section_title}")
            render_boolean("Is Complete", is_complete)

            fields = section.get("Fields", [])
            for field in fields:
                name = field.get("Field Name", "")
                val = field.get("Field Value", "")
                render_boolean(name, val, use_indicator=False)
            st.markdown("---")

# Streamlit App
st.set_page_config(page_title="SSPR Document Analysis")
st.title("SSPR Document Analyzer")

uploaded_files = st.file_uploader("Upload your PDF documents", type=["pdf"], accept_multiple_files=True)

prompt = """# SSPR Document Analysis Prompt

## Task
Analyze the provided documents to check for an SSPR (Source Selection & Price Reasonableness) and extract specific information.

## Output Format
Return your response in a structured JSON format with the following fields:

```json
{
  "SSPR Found": "Yes/No",
  "Funding Source": "Federal Funds/Non-Federal Funds",
  "Dollar Amount": "$X",
  "Desired Supplier": "Company Name",
  "Source Selection": {
    "Funding Source": "",
    "Type": ""
  },
  "Sections Always Required": [
    "I - SOURCE SELECTION",
    "VII - PRICING",
    "VIII - APPROVALS"
  ],
  "Sections Required for this Type": [
    "List additional required sections based on the selected funding source and type"
  ],
  "Section Details": [
    {
      "Section Number": "I",
      "Section Name": "SOURCE SELECTION (I)",
      "Is Complete": true/false,
      "Fields": [
        {
          "Field Name": "Field Label",
          "Field Value": "Extracted Value"
        }
      ]
    }
  ]
}
```

## Analysis Rules

### Always Required Sections
Sections I, VII, and VIII are always required regardless of funding source or type.

### Additional Required Sections by Funding Type
Based on which checkbox is selected in Section I:

1. **Federal Funds**:
   - New or Existing Formal Competitive Bid/Contract#: No additional sections
   - Competitive Proposals of < $100K: Section II
   - Sole Source: Sections III, IV
   - Certified Small Business (Only <$250K): Section III

2. **Non-Federal Funds**:
   - New or Existing Formal Competitive Bid/Contract#: No additional sections
   - Certified Small Business or DVBE (Only <$250K): Section III
   - Sole Source: Sections III, IV
   - Professional/Personal Services: Sections III, V
   - Unusual & Compelling Urgency: Section VI

### Section Information
For each required section, indicate:
- Section Number and Name (formatted with proper title case)
- Whether it's complete (true/false)
- List of fields with their corresponding values (with proper labels)

# YOU HAVE TO INCLUDE Always Required Sections & Additional Required Sections by Funding Type
⚠️ **IMPORTANT**: Return only valid JSON. Do NOT include any explanation or notes before or after the JSON. No markdown. No commentary.
"""

if uploaded_files:
    prompt = st.text_area("Prompt to send with PDFs", value=prompt, height=400)

    if st.button("Send to Bedrock"):
        with st.spinner("Analyzing documents..."):
            response_text = query_bedrock_with_multiple_pdfs(prompt, uploaded_files)
            st.subheader("Raw Response")
            st.code(response_text)

            parsed_response = try_parse_json_like(response_text)
            if parsed_response:
                st.success("Structured Output")
                render_structured_output(parsed_response)
            else:
                st.error("Failed to parse response as JSON.")
