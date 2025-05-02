import streamlit as st
import json

from general_doc_parser import parse_documents_together
from prompts import checklist_and_validation_prompt
from utils import (
    try_parse_json_like,
    query_bedrock_with_multiple_pdfs,
    render_json_checklist,
    render_json_output,
    render_parsed_documents
)
from model_registry import ModelRegistry


def run_combined_validation(uploaded_files):
    with st.spinner("Extracting information from uploaded documents..."):
        parsed_data = parse_documents_together(uploaded_files)

    if parsed_data and isinstance(parsed_data, dict) and "error" not in parsed_data:
        render_parsed_documents(parsed_data)

        input_text = json.dumps(parsed_data, indent=2)
        full_prompt = checklist_and_validation_prompt.format(
            doc_text=input_text)

        with st.spinner("Running Checklist + Validation with Claude..."):
            response_text = query_bedrock_with_multiple_pdfs(
                full_prompt, [], model_id=ModelRegistry.sonnet_3_5
            )
            parsed_response = try_parse_json_like(response_text)

        st.subheader("🦾 Raw Combined Model Output")
        st.code(response_text)

        if parsed_response:
            if "data_validation" in parsed_response:
                st.subheader("✅ Data Validation Results")
                render_json_output(parsed_response["data_validation"])
            if "compliance_checklist" in parsed_response:
                st.subheader("✅ Checklist Results")
                render_json_checklist(parsed_response["compliance_checklist"])
        else:
            st.error("❌ Failed to parse model output as JSON")
    else:
        st.error("❌ Failed to extract data from uploaded documents")
        if isinstance(parsed_data, dict) and "raw" in parsed_data:
            st.code(parsed_data["raw"])

def main():
    st.set_page_config(page_title="Combined Checklist + Validation")
    st.title("📁 Combined Checklist + Data Validator")

    uploaded_files = st.file_uploader("Upload your PDF documents", type=[
                                      "pdf"], accept_multiple_files=True)

    if uploaded_files:
        if st.button("Run Combined Validation"):
            run_combined_validation(uploaded_files)

if __name__ == "__main__":
    main()