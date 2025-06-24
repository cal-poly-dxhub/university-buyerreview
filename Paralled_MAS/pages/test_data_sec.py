import streamlit as st
import asyncio
from Graphs.data_sec_only import build_data_sec_graph
from state import PipelineState
import pandas as pd

st.set_page_config(page_title="🧪 Union Job Classifier", layout="centered")
st.title("🧪 Union Job Classifier (Isolated Test)")

uploaded_files = st.file_uploader(
    "Upload one or more PDF files", type="pdf", accept_multiple_files=True)

if uploaded_files and st.button("Run Data Security Flagger"):
    with st.spinner("Running..."):
        graph = build_data_sec_graph()
        state: PipelineState = {"uploaded_files": uploaded_files}
        output = asyncio.run(graph.ainvoke(state))

    st.subheader("📝 Union Job Output")
    st.json(output.get("run_data_sec_classification"))
    
    # Show matched row if available
