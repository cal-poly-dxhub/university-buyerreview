import streamlit as st
import asyncio
from Graphs.full_pipeline import build_full_pipeline_graph
from state import PipelineState

st.set_page_config(page_title="📄 Full Document Pipeline", layout="centered")
st.title("📄 Document Parser with Checklist + PO Validation")

st.subheader("📂 Upload Documents")
uploaded_files = st.file_uploader(
    "Upload one or more PDF files",
    type="pdf",
    accept_multiple_files=True
)

if uploaded_files and st.button("Run Full Pipeline"):
    with st.spinner("Running full document pipeline..."):
        pipeline = build_full_pipeline_graph()
        initial_state: PipelineState = {"uploaded_files": uploaded_files}
        final_output = asyncio.run(pipeline.ainvoke(initial_state))

    st.subheader("✅ Final Output")
    st.json(final_output)
