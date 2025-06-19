import streamlit as st

st.set_page_config(page_title="🧠 Pipeline Launcher", layout="centered")

st.title("🧭 AI Document Processing Pipelines")

st.markdown("""
Welcome! Use the links below to open and test different pipeline flows and agents.
""")

st.page_link("pages/full_pipeline.py", label="Full Document Pipeline", icon="📂")
st.page_link("pages/test_union_job.py", label="Test Union Job Classifier", icon="🧪")
# Add more as you build more Pages:
# st.page_link("Pages/test_checklist.py", label="✅ Test Checklist Agent", icon="✅")
# st.page_link("Pages/compare_versions.py", label="🧬 Compare Agent Versions", icon="🔁")