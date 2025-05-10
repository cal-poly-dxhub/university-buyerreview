from langchain.chat_models import ChatBedrock
from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType
from model_registry import ModelRegistry
from tools import get_prompt_for_doc_type, summarize_document

def create_router_agent():
    llm = ChatBedrock(
        model_id=ModelRegistry.sonnet_3_7,
        region_name="us-west-2",
        temperature=0
    )

    tools = [
        Tool(
            name="get_prompt_for_doc_type",
            func=get_prompt_for_doc_type,
            description="Returns the correct parsing prompt for a document type like SSPR, PO, or INVOICE"
        ),
        Tool(
            name="summarize_document",
            func=summarize_document,
            description="Summarizes the document if no known type matches"
        )
    ]

    agent = initialize_agent(
        tools,
        llm,
        agent_type=AgentType.OPENAI_FUNCTIONS,  # needed for Claude 3-style tool calling
        verbose=True
    )

    return agent
