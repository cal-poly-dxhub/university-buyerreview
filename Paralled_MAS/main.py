import asyncio
import streamlit as st
from doc_parser import parse_documents_parallel

# --- Streamlit UI ---
if __name__ == "__main__":
    st.set_page_config(page_title="Document Parser", layout="centered")
    st.title("📄 Parallel Document Parser")

    uploaded_files = st.file_uploader(
        "Upload one or more PDF files",
        type="pdf",
        accept_multiple_files=True
    )

    if uploaded_files:
        with st.spinner("Parsing documents..."):
            parsed_output = asyncio.run(parse_documents_parallel(uploaded_files))

        st.subheader("✅ Parsed Output")
        st.json(parsed_output)
