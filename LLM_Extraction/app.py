import streamlit as st
from utils import (
    try_parse_json_like,
    query_bedrock_with_multiple_pdfs,
    render_json_output,
    render_parsed_documents
)
from prompts import data_validation_prompt
from general_doc_parser import parse_documents_together
from model_registry import ModelRegistry


st.set_page_config(page_title="Data Validation From Parsed Docs")
st.title("📊 Data Validator (from Parsed Document Agent)")

uploaded_files = st.file_uploader("Upload PDF documents", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    if st.button("Run Data Validator"):
        with st.spinner("Parsing and validating document data..."):
            parsed_data = parse_documents_together(uploaded_files)

        if parsed_data and isinstance(parsed_data, dict) and "error" not in parsed_data:
            render_parsed_documents(parsed_data)

            try:
                prompt_input = data_validation_prompt.format(
                    doc_text=parsed_data
                )
            except KeyError as e:
                st.error(f"Prompt formatting error: missing key {e}")
                st.stop()

            with st.spinner("Running validation with model..."):
                validation_response = query_bedrock_with_multiple_pdfs(
                    prompt_input, [], model_id=ModelRegistry.sonnet_3_5
                )
                parsed_output = try_parse_json_like(validation_response)

            st.subheader("𞷾 Raw Model Output")
            st.code(validation_response)

            if parsed_output:
                st.subheader("✅ Validation Results")
                render_json_output(parsed_output)
            else:
                st.error("❌ Failed to parse model output as JSON.")
        else:
            st.error("❌ Failed to parse documents.")
            if isinstance(parsed_data, dict) and "raw" in parsed_data:
                st.code(parsed_data["raw"])
