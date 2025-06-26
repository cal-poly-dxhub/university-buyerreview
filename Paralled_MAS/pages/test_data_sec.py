import streamlit as st
import asyncio
from Graphs.data_sec_only import build_data_sec_graph
from state import PipelineState

st.set_page_config(page_title="Data Security Classification", layout="centered")
st.title("Data Security Classification (Isolated Test)")


uploaded_files = st.file_uploader("", type="pdf", accept_multiple_files=True)

if uploaded_files and st.button("Run"):
    with st.spinner("Processing..."):
        graph = build_data_sec_graph()
        state: PipelineState = {"uploaded_files": uploaded_files}
        output = asyncio.run(graph.ainvoke(state))
    
    # Return only the JSON response
    data_sec_output = output["data_security"]
    st.json(data_sec_output)
