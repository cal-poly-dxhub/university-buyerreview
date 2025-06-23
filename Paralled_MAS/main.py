import streamlit as st

st.set_page_config(page_title="🧠 Pipeline Launcher", layout="centered")

st.title("🧭 AI Document Processing Pipelines")

st.markdown("""
Welcome! Use the links below to open and test different pipeline flows and agents.
""")

st.page_link("pages/full_pipeline.py", label="Full Document Pipeline", icon="📂")
st.page_link("pages/test_union_job.py", label="Test Union Job Classifier", icon="🧪")
st.page_link("pages/pc_classifier.py", label="PC Classifier & Vector Mapping", icon="📊")
st.page_link("pages/phi_agreement_check.py", label="PHI Agreement Check", icon="🔍")
