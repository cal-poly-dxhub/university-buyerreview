import asyncio
import streamlit as st
from tools import build_general_doc_prompt_from_file
from utils import query_bedrock_with_multiple_pdfs, try_parse_json_like, query_bedrock_with_multiple_pdfs_with_tools
from model_registry import ModelRegistry
from tools import get_tool_config

# --- Synchronous single document processor ---
def route_and_parse_document(file, prompt_path="Task_Prompts/Parser.txt"):
    prompt = build_general_doc_prompt_from_file(prompt_path)
    response = query_bedrock_with_multiple_pdfs_with_tools(
        prompt=prompt,
        files=[file],
        model_id=ModelRegistry.sonnet_3_7,
        tool_config=get_tool_config()
    )
    parsed = try_parse_json_like(response)
    return parsed if parsed else {"error": "Failed to parse", "raw": response}

# --- Async wrapper for single document ---
async def async_parse_document(file):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, route_and_parse_document, file)

# --- Parse all uploaded documents in parallel ---
async def parse_documents_parallel(files):
    tasks = [async_parse_document(file) for file in files]
    results = await asyncio.gather(*tasks)
    return dict(zip([file.name for file in files], results))

# --- Streamlit UI ---
if __name__ == "__main__":
    st.set_page_config(page_title="Document Parser", layout="centered")
    st.title("📄 Parallel Document Parser")

    uploaded_files = st.file_uploader(
        "Upload one or more PDF files",
        type="pdf",
        accept_multiple_files=True
    )

    if uploaded_files:
        with st.spinner("Parsing documents..."):
            parsed_output = asyncio.run(parse_documents_parallel(uploaded_files))

        st.subheader("✅ Parsed Output")
        st.json(parsed_output)
