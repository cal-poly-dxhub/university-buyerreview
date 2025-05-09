import streamlit as st
import json
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda

from general_doc_parser import parse_documents_together
from utils import (
    query_bedrock_with_multiple_pdfs,
    try_parse_json_like,
    render_json_output,
    render_json_checklist,
    render_parsed_documents,
)
from prompts import checklist_and_validation_prompt
from model_registry import ModelRegistry
from dotenv import load_dotenv

load_dotenv()
from langsmith import traceable

class PipelineState(TypedDict):
    uploaded_files: List[Any]
    parsed_data: Dict[str, Any]
    model_output: Dict[str, Any]
    raw_output: str

def parse_documents(state):
    uploaded_files = state["uploaded_files"]
    return {"parsed_data": parse_documents_together(uploaded_files)}
    # parsed = {}
    # for file in uploaded_files:
    #     name = file.name
    #     file_parsed = parse_documents_together([file])
    #     parsed[name] = file_parsed.get(name, file_parsed)  # handles single-file or dict cases
    # return {"parsed_data": parsed}

def validate_and_check(state):
    parsed = state["parsed_data"]
    doc_text = json.dumps(parsed, indent=2)
    prompt = checklist_and_validation_prompt.format(doc_text=doc_text)
    response_text = query_bedrock_with_multiple_pdfs(prompt, [], model_id=ModelRegistry.sonnet_3_5)
    parsed_response = try_parse_json_like(response_text)
    return {"model_output": parsed_response, "raw_output": response_text}

def display_results(state):
    parsed_data = state.get("parsed_data", {})
    if parsed_data:
        st.success("✅ Documents parsed successfully")
        st.subheader("📋 Extracted Data")
        render_parsed_documents(parsed_data)

    st.subheader("🦾 Raw Combined Model Output")
    st.code(state.get("raw_output", "<no output>"))

    parsed = state.get("model_output", {})
    if not parsed:
        st.error("❌ Failed to parse model output as JSON")
        return {}

    if "data_validation" in parsed:
        st.subheader("✅ Data Validation Results")
        render_json_output(parsed["data_validation"])

    if "compliance_checklist" in parsed:
        st.subheader("✅ Checklist Results")
        render_json_checklist(parsed["compliance_checklist"])

    return {}

# LangGraph definition
graph = StateGraph(PipelineState)
graph.add_node("parse_documents", RunnableLambda(parse_documents))
graph.add_node("validate_and_check", RunnableLambda(validate_and_check))
graph.add_node("display_results", RunnableLambda(display_results))

graph.set_entry_point("parse_documents")
graph.add_edge("parse_documents", "validate_and_check")
graph.add_edge("validate_and_check", "display_results")
graph.add_edge("display_results", END)

app = graph.compile()

# Streamlit integration
@traceable(name="main_langgraph_pipeline")
def main():
    st.set_page_config(page_title="LangGraph - Checklist + Validator")
    st.title("📁 LangGraph Procurement Validator")

    uploaded_files = st.file_uploader("Upload your PDF documents", type=["pdf"], accept_multiple_files=True)

    if uploaded_files and st.button("Run LangGraph Validation"):
        app.invoke({"uploaded_files": uploaded_files})

if __name__ == "__main__":
    main()
