import streamlit as st
from utils import try_parse_json_like, query_bedrock_with_multiple_pdfs
from prompts import sspr_prompt


def render_boolean(key, value, use_indicator=True):
    val = str(value).strip().lower()
    if use_indicator and val in {"yes", "true", "agree"}:
        st.success(f"✅ **{key}**: {value}")
    elif use_indicator and val in {"no", "false", "disagree"}:
        st.error(f"❌ **{key}**: {value}")
    elif use_indicator:
        st.info(f"**{key}**: {value}")
    else:
        st.markdown(f"- **{key}**: {value}")


def render_structured_output(data):
    # Render top-level keys
    top_fields = ["SSPR Found", "Funding Source",
                  "Dollar Amount", "Desired Supplier"]
    for field in top_fields:
        value = data.get(field, "N/A")
        render_boolean(field, value)

    # Source Selection
    if "Source Selection" in data:
        st.subheader("📂 Source Selection")
        for k, v in data["Source Selection"].items():
            st.markdown(f"- **{k}**: {v}")

    # Required Sections
    if "Required Sections" in data:
        st.subheader("📄 Required Sections")
        for section in data["Required Sections"]:
            st.markdown(f"- {section}")

    # Section Details
    if "Section Details" in data:
        st.subheader("📘 Section Details")
        for section in data["Section Details"]:
            section_title = f"**{section.get('Section Number', '')}. {section.get('Section Name', '')}**"
            is_complete = section.get("Is Complete", False)
            st.markdown(f"### {section_title}")
            render_boolean("Is Complete", is_complete)

            fields = section.get("Fields", [])
            for field in fields:
                name = field.get("Field Name", "")
                val = field.get("Field Value", "")
                render_boolean(name, val, use_indicator=False)
            st.markdown("---")


# Streamlit App
st.set_page_config(page_title="SSPR Document Analysis")
st.title("SSPR Document Analyzer")

uploaded_files = st.file_uploader("Upload your PDF documents", type=[
                                  "pdf"], accept_multiple_files=True)

if uploaded_files:
    sspr_prompt = st.text_area(
        "Prompt to send with PDFs", value=sspr_prompt, height=400)

    if st.button("Send to Bedrock"):
        with st.spinner("Analyzing documents..."):
            response_text = query_bedrock_with_multiple_pdfs(
                sspr_prompt, uploaded_files)
            st.subheader("Raw Response")
            st.code(response_text)

            parsed_response = try_parse_json_like(response_text)
            if parsed_response:
                st.success("Structured Output")
                render_structured_output(parsed_response)
            else:
                st.error("Failed to parse response as JSON.")
