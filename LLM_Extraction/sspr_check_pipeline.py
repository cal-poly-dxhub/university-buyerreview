import streamlit as st
import re
import json
from utils import try_parse_json_like, query_bedrock_with_multiple_pdfs
from prompts import sspr_prompt

MODEL_ID = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"

# === SSPR Functions ===

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
                checklist_response = query_bedrock_with_multiple_pdfs(checklist_prompt,[], MODEL_ID)
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
