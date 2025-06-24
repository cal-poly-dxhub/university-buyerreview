from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from Agents.doc_parser import parse_documents_parallel
from Agents.data_sec_classification import run_data_sec_classification
from state import PipelineState

async def parse_documents_node(state: PipelineState) -> PipelineState:
    parsed = await parse_documents_parallel(state["uploaded_files"])
    return {"parsed_data": parsed}

def build_data_sec_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("Parse Documents", RunnableLambda(parse_documents_node))
    graph.add_node("Run Data Decurity Classification", RunnableLambda(run_data_sec_classification))

    graph.set_entry_point("Parse Documents")
    graph.add_edge("Parse Documents", "Run Data Decurity Classification")
    graph.add_edge("Run Data Decurity Classification", END)

    return graph.compile()
