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
    type=["pdf"],
    accept_multiple_files=True
)

# ---- ENTRY POINT ----
if uploaded_files and st.button("Run Full Pipeline"):
    with st.spinner("Running full document pipeline..."):
        pipeline = build_full_pipeline_graph()
        final_state = asyncio.run(run_json_pipeline_with_stream(uploaded_files, pipeline))

        pdf_bytes = final_state.get("pdf_summary")

        if pdf_bytes:
            st.success("✅ Summary PDF generated.")
            st.download_button(
                label="📄 Download Summary PDF",
                data=pdf_bytes,
                file_name="summary.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("⚠️ No summary PDF found in pipeline output.")
