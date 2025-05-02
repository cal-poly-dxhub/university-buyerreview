import streamlit as st
import boto3
import json
import re
import os

# AWS setup
session = boto3.Session(region_name="us-west-2")
bedrock = session.client(service_name='bedrock-runtime')
MODEL_ID = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"

sspr_prompt = """
# SSPR Document Analysis Prompt

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


# === Utility ===
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
            start = min([i for i in (text.find('['), text.find('{')) if i != -1])
            end = max([text.rfind(']'), text.rfind('}')]) + 1
            cleaned = text[start:end].strip()
            return json.loads(cleaned)
        except Exception:
            return None

# === SSPR Functions ===


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


def query_bedrock_with_multiple_pdfs(prompt, files):
    messages = create_doc_messages(prompt, files)
    response = bedrock.converse(
        modelId=MODEL_ID,
        messages=messages,
        inferenceConfig={"maxTokens": 10000, "temperature": 0}
    )
    return response['output']['message']['content'][0]['text']


def render_structured_output(data):
    top_fields = ["SSPR Found", "Funding Source",
                  "Dollar Amount", "Desired Supplier"]
    for field in top_fields:
        value = data.get(field, "N/A")
        st.markdown(f"**{field}**: {value}")

    if "Source Selection" in data:
        st.subheader("📂 Source Selection")
        for k, v in data["Source Selection"].items():
            st.markdown(f"- **{k}**: {v}")

    if "Required Sections" in data:
        st.subheader("📄 Required Sections")
        for section in data["Required Sections"]:
            st.markdown(f"- {section}")

    if "Section Details" in data:
        st.subheader("📘 Section Details")
        for section in data["Section Details"]:
            section_title = f"**{section.get('Section Number', '')}. {section.get('Section Name', '')}**"
            st.markdown(f"### {section_title}")
            is_complete = section.get("Is Complete", False)
            st.markdown(f"- Is Complete: {is_complete}")
            for field in section.get("Fields", []):
                st.markdown(
                    f"  - **{field['Field Name']}**: {field['Field Value']}")
            st.markdown("---")

# === Checklist Functions ===
def build_checklist_prompt(doc_text):
    return f"""
You are a compliance assistant. Based on the following extracted document content, evaluate the checklist items and respond in strict JSON format.

Document content:
{doc_text}

Checklist items:

1. **Funding Source**:
   - Is the funding source Federal or Non-Federal?
   - Identify and confirm which one it is based on the document.

2. **Price Reasonableness / SSPR**:
   - Is there documentation of price reasonableness?
   - Look for an SSPR (Source Selection & Price Reasonableness) form or similar justification.

3. **Competitive Bidding (threshold dependent)**:
   - If the total value is less than $100,000, mark this check as automatically passed.
   - If the value is $100,000 or above, check whether competitive bidding was done or a valid exception is documented.

4. **Contract Duration**:
   - If the purchase is for services, check whether the contract exceeds 10 years.
   - If the purchase is for goods, it is considered a one-time purchase and this check automatically passes.

5. **Conflict of Interest**:
   - Has the end user determined that the service provider should not be classified as a UC employee?
   - If no conflict of interest is found or it’s documented clearly, this should pass.

6. **Data Security / Appendix DS**:
   - If the purchase is for software or involves handling UC data, check if Appendix Data Security has been considered or signed.
   - If it's goods or services that clearly don't involve sharing data, this check passes automatically.

Return your answer as a JSON list of objects, each like:
{{
  "check": "...",
  "status": "✅ Passed / ❌ Missing / 🟡 Exception / ❓ Uncertain",
  "note": "...brief justification based on evidence..."
}}
"""


# def build_checklist_prompt(doc_text):
#     return f"""
# You are a compliance assistant. Based on the following extracted document content, evaluate the checklist items and respond in strict JSON format.

# Document content:
# {doc_text}

# Checklist items:
# 1. Competitive Bidding:
#    - Was competitive bidding done?
#    - If not, was an exception documented?

# 2. Use of UC Templates:
#    - Were UC templates used?
#    - If not, did a Policy Exception Authority approve the exception?

# 3. Contract Duration:
#    - Does the total contract duration exceed 10 years?
#    - If so, was an exception approved?
# If this is goods, not services, then it is a one time purchase and it passes this requirement

# Return your answer as a JSON list of objects, each like:
# {{
#   "check": "...",
#   "status": "✅ Passed / ❌ Missing / 🟡 Exception / ❓ Uncertain",
#   "note": "...brief justification based on evidence..."
# }}
# """


def query_bedrock_from_text(prompt):
    messages = [{"role": "user", "content": [{"text": prompt}]}]
    response = bedrock.converse(
        modelId=MODEL_ID,
        messages=messages,
        inferenceConfig={"maxTokens": 4000, "temperature": 0}
    )
    return response['output']['message']['content'][0]['text']


def render_json_checklist(data):
    for item in data:
        status = item.get("status", "❓ Uncertain")
        icon = {
            "✅ Passed": "✅",
            "❌ Missing": "❌",
            "🟡 Exception": "⚠️",
            "❓ Uncertain": "❓"
        }.get(status, "❓")
        with st.expander(f"{icon} {item['check']}"):
            st.markdown(f"**Note:** {item['note']}")


# === Streamlit App ===
st.set_page_config(page_title="SSPR + Checklist Analyzer")
st.title("📄 SSPR + Checklist Validation")

uploaded_files = st.file_uploader("Upload your PDF documents", type=[
                                  "pdf"], accept_multiple_files=True)

sspr_prompt = st.text_area("SSPR Prompt", value=sspr_prompt, height=300)

if uploaded_files:
    if st.button("Run Full Analysis"):
        with st.spinner("Analyzing documents with Bedrock..."):
            sspr_response = query_bedrock_with_multiple_pdfs(
                sspr_prompt, uploaded_files)
            parsed_sspr = try_parse_json_like(sspr_response)

        if parsed_sspr:
            st.subheader("📋 SSPR Extraction")
            render_structured_output(parsed_sspr)

            # Now send entire SSPR JSON string to checklist prompt
            checklist_prompt = build_checklist_prompt(
                json.dumps(parsed_sspr, indent=2))
            with st.spinner("Running Checklist Compliance Check..."):
                checklist_response = query_bedrock_from_text(checklist_prompt)
                parsed_checklist = try_parse_json_like(
                    checklist_response.strip())

            if parsed_checklist:
                st.subheader("✅ Checklist Results")
                render_json_checklist(parsed_checklist)
                st.subheader("📦 Raw Checklist JSON")
                st.code(json.dumps(parsed_checklist, indent=2))
            else:
                st.error("❌ Failed to parse checklist response as JSON")
                st.code(checklist_response)
                st.warning("Try copying this response and checking it in a JSON validator like https://jsonlint.com")
        else:
            st.error("Failed to parse SSPR response")
            st.code(sspr_response)
