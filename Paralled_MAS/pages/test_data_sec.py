import streamlit as st
import asyncio
from Graphs.data_sec_only import build_data_sec_graph
from state import PipelineState

st.set_page_config(page_title="Data Security Classification", layout="centered")
st.title("Data Security Classification (Isolated Test)")


uploaded_files = st.file_uploader(
    "Upload one or more PDF files", type=["pdf", "png", "jpg", "jpeg", "docx", "txt", "xlsx"], accept_multiple_files=True)

if uploaded_files and st.button("Run"):
    with st.spinner("Processing..."):
        graph = build_data_sec_graph()
        state: PipelineState = {"uploaded_files": uploaded_files}
        output = asyncio.run(graph.ainvoke(state))

    st.subheader("📝 Union Job Output")
    st.json(output.get("run_data_sec_classification"))

    # Show matched row if available
