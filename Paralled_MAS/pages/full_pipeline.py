import streamlit as st
import asyncio
from Graphs.full_pipeline import build_full_pipeline_graph
from utils import run_json_pipeline_with_stream

# ---- CONFIG ----
st.set_page_config(page_title="📄 Full Document Pipeline", layout="wide")
st.title("📄 Document Parser with Checklist + PO Validation")

st.subheader("📂 Upload Documents")
uploaded_files = st.file_uploader(
    "Upload one or more PDF files",
    type="pdf",
    accept_multiple_files=True
)

# ---- ENTRY POINT ----
if uploaded_files and st.button("Run Full Pipeline"):
    with st.spinner("Running full document pipeline..."):
        pipeline = build_full_pipeline_graph()
        asyncio.run(run_json_pipeline_with_stream(uploaded_files, pipeline))
