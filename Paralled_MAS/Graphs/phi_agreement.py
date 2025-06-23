from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from state import PipelineState
from Agents.doc_parser import parse_documents_node
from Agents.phi_agreement_checker import phi_agreement_checker

def build_phi_agreement_graph():
    g = StateGraph(PipelineState)
    g.add_node("Parse Documents", RunnableLambda(parse_documents_node))
    g.add_node("PHI Agreement Checker", RunnableLambda(phi_agreement_checker))

    g.set_entry_point("Parse Documents")
    g.add_edge("Parse Documents", "PHI Agreement Checker")
    g.add_edge("PHI Agreement Checker", END)
    return g.compile()
