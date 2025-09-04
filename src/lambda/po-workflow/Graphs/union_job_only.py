from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from Agents.doc_parser import parse_documents_node
from Agents.union_job_classifier import union_job_check
from state import PipelineState

def build_union_job_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("Parse Documents", RunnableLambda(parse_documents_node))
    graph.add_node("Check if Union Job", RunnableLambda(union_job_check))

    graph.set_entry_point("Parse Documents")
    graph.add_edge("Parse Documents", "Check if Union Job")
    graph.add_edge("Check if Union Job", END)

    return graph.compile()
