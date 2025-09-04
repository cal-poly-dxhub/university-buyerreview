from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from Agents.doc_parser import parse_documents_node
from Agents.data_sec_classification import run_data_sec_classification
from state import PipelineState

def build_data_sec_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("Parse Documents", RunnableLambda(parse_documents_node))
    graph.add_node("Run Data Security Classification", RunnableLambda(run_data_sec_classification))

    graph.set_entry_point("Parse Documents")
    graph.add_edge("Parse Documents", "Run Data Security Classification")
    graph.add_edge("Run Data Security Classification", END)

    return graph.compile()
