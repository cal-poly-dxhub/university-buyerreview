import streamlit as st
from general_doc_parser import parse_documents_together


st.set_page_config(page_title="General Document Parser")
st.title("📄 Unified Document Parser")

uploaded_files = st.file_uploader("Upload PDF documents", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    if st.button("Run Parser"):
        with st.spinner("Processing documents with Bedrock..."):
            parsed = parse_documents_together(uploaded_files)

        if isinstance(parsed, dict) and "error" not in parsed:
            st.success("✅ Parsed Results")
            for doc_name, content in parsed.items():
                with st.expander(doc_name):
                    st.json(content)
        else:
            st.error("❌ Failed to parse documents. See raw output below.")
            st.code(parsed.get("raw", "No raw text available."))
