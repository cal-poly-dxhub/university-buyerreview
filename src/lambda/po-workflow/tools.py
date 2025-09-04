from prompt_loader import PARSER_PROMPT_REGISTRY, TASK_PROMPT_REGISTRY
import json
from typing import List
import os
from utils import get_uc_cost

TOOL_CONFIG_DIR = "Tools_Config"
TOOL_REGISTRY = {
    "summarize_document": lambda d: {"summary": summarize_document(d["doc_text"])},
    "get_prompt_for_doc_type": lambda d: {"prompt": get_prompt_for_doc_type(d["doc_type"])},
    "get_UC_cost": lambda d: {"uc_cost": get_uc_cost(d["job_title"])}
}


def get_prompt_for_doc_type(doc_type: str) -> str:
    return PARSER_PROMPT_REGISTRY.get(doc_type.upper(), "")


def summarize_document(doc_text: str) -> str:
    return PARSER_PROMPT_REGISTRY.get("FALLBACK_SUMMARY", f"Summarize the following:\n\n{doc_text}")


def get_task_prompt(task_name: str) -> str:
    return TASK_PROMPT_REGISTRY.get(task_name.upper(), "")




def run_tool_by_name(tool_name: str, input_data: dict) -> dict:
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {tool_name}")
    return TOOL_REGISTRY[tool_name](input_data)


def get_tool_config(selected_tool_names: List[str]) -> dict:
    tools = []

    for name in selected_tool_names:
        path = os.path.join(TOOL_CONFIG_DIR, f"{name}.json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Tool config not found: {path}")
        with open(path) as f:
            spec = json.load(f)
            tools.append({"toolSpec": spec})

    return {
        "tools": tools
    }


def build_general_doc_prompt_from_file(template_path="Task_Prompts/Parser.txt"):
    with open(template_path, "r") as f:
        template = f.read()

    available_types = [
        t for t in PARSER_PROMPT_REGISTRY.keys() if t != "FALLBACK_SUMMARY"
    ]
    formatted = ", ".join(
        f'"{doc_type}"' for doc_type in sorted(available_types))

    return template.replace("{available_types}", formatted)
