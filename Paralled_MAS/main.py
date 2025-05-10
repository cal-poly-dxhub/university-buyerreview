import asyncio
import streamlit as st
from typing import TypedDict, List, Dict, Any
from streamlit.runtime.uploaded_file_manager import UploadedFile
from pandas import DataFrame
import json

from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda

from doc_parser import parse_documents_parallel
from validation import validate_data
from checklist import run_checklist


# --- Pipeline State Definition ---
class PipelineState(TypedDict, total=False):
    uploaded_files: List[UploadedFile]
    parsed_data: Dict[str, Any]
    checklist_result: Any
    validation_result: Any


# --- Router: only run validate_data if PO document is present ---
def should_run_validation(state: PipelineState) -> str:
    parsed = state.get("parsed_data", {})
    for doc in parsed.values():
        if doc.get("doc_type", "").upper() == "PO":
            return "validate"
    return "skip"


# --- Node: Parse uploaded documents ---

async def parse_documents_node(state: PipelineState) -> PipelineState:
    parsed = await parse_documents_parallel(state["uploaded_files"])
    return {"parsed_data": parsed}


# --- LangGraph builder ---
def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("parse_documents", RunnableLambda(parse_documents_node))
    graph.add_node("checklist", RunnableLambda(run_checklist))
    graph.add_node("validate_data", RunnableLambda(validate_data))
    graph.add_node("skip", RunnableLambda(lambda state: {
        "parsed_data": state["parsed_data"]
    }))

    graph.set_entry_point("parse_documents")

    # Always run checklist
    graph.add_edge("parse_documents", "checklist")

    # Conditionally run validation
    graph.add_conditional_edges("parse_documents", should_run_validation, {
        "validate": "validate_data",
        "skip": "skip"
    })

    # Terminal edges
    graph.add_edge("checklist", END)
    graph.add_edge("validate_data", END)
    graph.add_edge("skip", END)

    return graph.compile()


# --- Streamlit UI ---
if __name__ == "__main__":
    st.set_page_config(page_title="📄 Document Pipeline", layout="centered")
    st.title("📄 Document Parser with Checklist + Conditional Validation")

    uploaded_files = st.file_uploader(
        "Upload one or more PDF files",
        type="pdf",
        accept_multiple_files=True
    )

    if uploaded_files:
        with st.spinner("Running document pipeline..."):
            pipeline = build_graph()
            initial_state: PipelineState = {"uploaded_files": uploaded_files}
            final_output = asyncio.run(pipeline.ainvoke(initial_state))

        st.subheader("✅ Final Output")
        st.json({
            "parsed_data": final_output.get("parsed_data"),
            "validation_result": final_output.get("validation_result"),
            "checklist_result": final_output.get("checklist_result")
        })

        # st.subheader("✅ Parsed Documents")
        # parsed_docs = final_output.get("parsed_data", {})

        # if parsed_docs:
        #     tab_names = list(parsed_docs.keys())
        #     tabs = st.tabs(tab_names)

        #     for tab, doc_name in zip(tabs, tab_names):
        #         with tab:
        #             doc = parsed_docs[doc_name]
        #             st.markdown(f"**Document Type**: `{doc.get('doc_type', 'Unknown')}`")
        #             data = doc.get("parsed_data", {})

        #             if "line_items" in data:
        #                 st.markdown("### Line Items")
        #                 st.dataframe(DataFrame(data["line_items"]))
                    
        #             for key, value in data.items():
        #                 if key != "line_items":
        #                     st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")

        # # --- Checklist Results ---
        # checklist = final_output.get("checklist_result")
        # if checklist:
        #     st.markdown("### ✅ Compliance Checklist")
        #     if isinstance(checklist, str):
        #         try:
        #             checklist = json.loads(checklist)
        #         except:
        #             pass

        #     for item in checklist:
        #         st.markdown(f"- **{item['check']}** — {item['status']}: {item['note']}")

        # # --- Validation Results ---
        # validation = final_output.get("validation_result")
        # if validation:
        #     st.markdown("### 🧪 Validation Result")
        #     if isinstance(validation, str):
        #         try:
        #             validation = json.loads(validation)
        #         except:
        #             pass

        #     for key, val in validation.items():
        #         match = val.get("match", "❓")
        #         st.markdown(f"**{key}** — Match: `{match}`")
        #         st.code(json.dumps(val, indent=2))

