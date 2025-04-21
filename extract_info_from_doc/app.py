from datetime import datetime
import streamlit as st
import json
from extract_from_doc import convert_to_json, extract_json_to_text

# Streamlit UI
st.set_page_config(page_title="Document Analyzer", layout="centered")
st.title("📄 Drag and Drop Document Analyzer")

uploaded_file = st.file_uploader("Upload your document", type=["pdf", "docx", "txt"])

if uploaded_file is not None:
    st.success(f"Uploaded: {uploaded_file.name}")

    with st.spinner("Processing with LLM..."):
        output_json = convert_to_json(extract_json_to_text("config1.json"), uploaded_file)
        readable_text = output_json

    st.subheader("📃 LLM Output")
    st.text_area("Readable Summary", readable_text, height=300)

    # Create downloadable .txt file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"LLM_Output_{timestamp}.txt"
    st.download_button(
        label="⬇️ Download Output as .txt",
        data=readable_text,
        file_name=filename,
        mime="text/plain"
    )