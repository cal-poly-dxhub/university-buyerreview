import streamlit as st
import asyncio
from Graphs.union_job_only import build_union_job_graph
from state import PipelineState
import pandas as pd
from Graphs.union_job_only import build_union_job_graph
from utils import run_json_pipeline_with_stream

st.set_page_config(page_title="🧪 Union Job Classifier", layout="centered")
st.title("🧪 Union Job Classifier (Isolated Test)")

uploaded_files = st.file_uploader(
    "Upload one or more PDF files", type=["pdf"], accept_multiple_files=True)

# ---- ENTRY POINT ----
if uploaded_files and st.button("Run Union Job Classifier"):
    with st.spinner("Running Union Job pipeline..."):
        pipeline = build_union_job_graph()
        output = asyncio.run(run_json_pipeline_with_stream(uploaded_files, pipeline))
    
    # Show matched row if available
    matched_row = output.get("union_job_check", {}).get("matched_row")

    if isinstance(matched_row, dict):
        st.subheader("📋 Matched Job Row")
        df = pd.DataFrame([matched_row])
        st.dataframe(df.style.set_properties(**{
            'border-color': 'black',
            'border-style': 'solid',
            'border-width': '1px',
        }))

