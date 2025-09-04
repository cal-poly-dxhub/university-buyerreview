import streamlit as st
import asyncio
from Graphs.data_sec_only import build_data_sec_graph
from state import PipelineState
import json
import os
from datetime import datetime

st.set_page_config(page_title="Data Security Classification", layout="centered")
st.title("Data Security Classification (Isolated Test)")


uploaded_files = st.file_uploader(
    "Upload one or more PDF files", type=["pdf", "png", "jpg", "jpeg", "docx", "txt", "xlsx"], accept_multiple_files=True)

if uploaded_files and st.button("Run"):
    with st.spinner("Processing..."):
        graph = build_data_sec_graph()
        state: PipelineState = {"uploaded_files": uploaded_files}
        output = asyncio.run(graph.ainvoke(state))

    # Remove unserializable keys before showing/saving
    if isinstance(output, dict) and "uploaded_files" in output:
        output.pop("uploaded_files")

    st.subheader("📝 Data Security Result")
    st.json(output)

    # Save each result to its own JSON file in DS_Results directory
    os.makedirs("DS_Results", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"DS_Results/result_{timestamp}.json"

    with open(json_filename, "w") as f:
        json.dump(output, f, indent=2)
