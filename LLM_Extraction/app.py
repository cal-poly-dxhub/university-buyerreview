import streamlit as st
from utils import try_parse_json_like, query_bedrock_with_multiple_pdfs
from prompts import data_validation_prompt


def render_json_output(data):
    for property_name, property_info in data.items():
        match = property_info.get("match", "")
        if match == "Yes":
            st.success(f"\u2705 {property_name}")
        elif match == "No":
            st.error(f"\u274C {property_name}")
        elif match == "Mostly Yes":
            st.warning(f"\u26A0\uFE0F {property_name}")
        else:
            st.info(property_name)

        sources = {k: v for k, v in property_info.items() if k != "match"}
        for source_name, value in sources.items():
            st.markdown(f"- **{source_name}**: {value}")
        st.markdown("---")


# Streamlit App
st.set_page_config(page_title="Direct PDF Upload with Claude")
st.title("Upload PDFs (Raw Bytes) for LLM Processing")

uploaded_files = st.file_uploader("Upload your PDF documents", type=[
                                  "pdf"], accept_multiple_files=True)

if uploaded_files:
    data_validation_prompt = st.text_area("Prompt to send with PDFs", value=data_validation_prompt)

    if st.button("Send to Bedrock"):
        with st.spinner("Processing multiple PDFs together..."):
            response_text = query_bedrock_with_multiple_pdfs(
                data_validation_prompt, uploaded_files)
            st.subheader("Response for All Files")
            parsed_response = try_parse_json_like(response_text)
            if parsed_response:
                render_json_output(parsed_response)
            else:
                st.error("Failed to parse response as JSON.")
                st.code(response_text)
