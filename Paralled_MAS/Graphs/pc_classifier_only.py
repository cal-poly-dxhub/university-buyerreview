from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from state import PipelineState
from Agents.doc_parser import parse_documents_node
from Agents.pc_llm_mapping import pc_llm_mapping

def build_pc_category_graph():
    g = StateGraph(PipelineState)
    g.add_node("Parse Documents", RunnableLambda(parse_documents_node))
    g.add_node("LLM PC Classifier", RunnableLambda(pc_llm_mapping))

    g.set_entry_point("Parse Documents")
    g.add_edge("Parse Documents", "LLM PC Classifier")
    g.add_edge("LLM PC Classifier", END)
    return g.compile()
