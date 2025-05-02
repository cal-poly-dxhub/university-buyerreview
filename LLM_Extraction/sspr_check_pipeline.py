import streamlit as st
import json
from utils import try_parse_json_like, query_bedrock_with_multiple_pdfs, render_json_checklist
from prompts import sspr_prompt, checklist_prompt
from model_registry import ModelRegistry


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
            checklist_prompt = checklist_prompt.format(
                doc_text=json.dumps(parsed_sspr, indent=2))
            with st.spinner("Running Checklist Compliance Check..."):
                checklist_response = query_bedrock_with_multiple_pdfs(
                    checklist_prompt, [], ModelRegistry.sonnet_3_7)
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
                st.warning(
                    "Try copying this response and checking it in a JSON validator like https://jsonlint.com")
        else:
            st.error("Failed to parse SSPR response")
            st.code(sspr_response)
