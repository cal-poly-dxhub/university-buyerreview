import streamlit as st
import json
from utils import try_parse_json_like, query_bedrock_with_multiple_pdfs, render_json_checklist
from prompts import checklist_prompt
from model_registry import ModelRegistry



# Streamlit UI

st.set_page_config(page_title="UC Procurement Checklist Parser")
st.title("🧾 LLM-Based UC Procurement Compliance Check")

file = st.file_uploader("Upload extracted .txt file", type=["txt"])

if file:
    text = file.read().decode("utf-8")
    st.text_area("Extracted Text Preview", text[:1500], height=200)

    if st.button("Send to Bedrock"):
        with st.spinner("Calling Claude..."):
            prompt = checklist_prompt.format(doc_text=text)
            response_text = query_bedrock_with_multiple_pdfs(
                prompt, [], ModelRegistry.mistral_large)
            parsed = try_parse_json_like(response_text)

        if parsed:
            st.success("Checklist Evaluation Complete ✅")
            render_json_checklist(parsed)
            st.subheader("📦 Raw JSON Output")
            st.code(json.dumps(parsed, indent=2))
        else:
            st.error("❌ Model did not return valid JSON.")
            st.code(response_text)
