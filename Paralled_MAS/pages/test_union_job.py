import streamlit as st
import asyncio
from Graphs.union_job_only import build_union_job_graph
from state import PipelineState

st.set_page_config(page_title="🧪 Union Job Classifier", layout="centered")
st.title("🧪 Union Job Classifier (Isolated Test)")

uploaded_files = st.file_uploader("Upload one or more PDF files", type="pdf", accept_multiple_files=True)

if uploaded_files and st.button("Run Union Job Classifier"):
    with st.spinner("Running..."):
        graph = build_union_job_graph()
        state: PipelineState = {"uploaded_files": uploaded_files}
        output = asyncio.run(graph.ainvoke(state))

    st.subheader("📝 Union Job Output")
    st.json(output.get("union_job_check"))
