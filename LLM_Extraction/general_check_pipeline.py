import streamlit as st
import json

from general_doc_parser import parse_documents_together
from prompts import checklist_prompt
from utils import try_parse_json_like, query_bedrock_with_multiple_pdfs, render_json_checklist

MODEL_ID = "mistral.mistral-large-2407-v1:0"

st.set_page_config(page_title="Checklist Validator (All Docs)")
st.title("📑 Checklist Validator for All Document Types")

uploaded_files = st.file_uploader("Upload your PDF documents", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    if st.button("Run Full Validation"):
        with st.spinner("Extracting information from uploaded documents..."):
            parsed_data = parse_documents_together(uploaded_files)

        if parsed_data and isinstance(parsed_data, dict) and "error" not in parsed_data:
            st.success("✅ Documents successfully parsed")
            st.subheader("📋 Extracted Information")

            for doc_name, content in parsed_data.items():
                with st.expander(doc_name):
                    st.json(content)

            checklist_input_text = json.dumps(parsed_data, indent=2)

            # Save intermediate extracted data to file before checklist
            with open("intermediate_extracted_data.txt", "w", encoding="utf-8") as f:
                f.write(checklist_input_text)

            full_prompt = checklist_prompt.format(doc_text=checklist_input_text)

            with st.spinner("Running Checklist Evaluation with DeepSeek..."):
                checklist_response = query_bedrock_with_multiple_pdfs(full_prompt, [], MODEL_ID)
                parsed_checklist = try_parse_json_like(checklist_response.strip())

            st.subheader("🧾 Raw Checklist Model Output")
            st.code(checklist_response)

            if parsed_checklist:
                st.subheader("✅ Checklist Results")
                render_json_checklist(parsed_checklist)
                st.subheader("📦 Raw Checklist JSON")
                st.code(json.dumps(parsed_checklist, indent=2))
            else:
                st.error("❌ Failed to parse checklist response as JSON")
        else:
            st.error("❌ Failed to extract data from uploaded documents")
            if isinstance(parsed_data, dict) and "raw" in parsed_data:
                st.code(parsed_data["raw"])
