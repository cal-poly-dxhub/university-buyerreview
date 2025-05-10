from prompt_loader import PARSER_PROMPT_REGISTRY, TASK_PROMPT_REGISTRY

def get_prompt_for_doc_type(doc_type: str) -> str:
    return PARSER_PROMPT_REGISTRY.get(doc_type.upper(), "")

def summarize_document(doc_text: str) -> str:
    return PARSER_PROMPT_REGISTRY.get("FALLBACK_SUMMARY", f"Summarize the following:\n\n{doc_text}")

def get_task_prompt(task_name: str) -> str:
    return TASK_PROMPT_REGISTRY.get(task_name.upper(), "")

def run_tool_by_name(tool_name: str, input_data: dict) -> dict:
    if tool_name == "get_prompt_for_doc_type":
        doc_type = input_data.get("doc_type", "")
        return {"prompt": get_prompt_for_doc_type(doc_type)}

    elif tool_name == "summarize_document":
        doc_text = input_data.get("doc_text", "")
        return {"summary": summarize_document(doc_text)}

    else:
        raise ValueError(f"Unknown tool name: {tool_name}")

def get_tool_config():
    return {
        "tools": [
            {
                "toolSpec": {
                    "name": "get_prompt_for_doc_type",
                    "description": "Returns the parser prompt for a document type like SSPR or PO.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "doc_type": {
                                    "type": "string"
                                }
                            },
                            "required": ["doc_type"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "summarize_document",
                    "description": "Summarizes the document if no known type matches.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "doc_text": {
                                    "type": "string"
                                }
                            },
                            "required": ["doc_text"]
                        }
                    }
                }
            }
        ]
    }


def build_general_doc_prompt_from_file(template_path="Task_Prompts/Parser.txt"):
    with open(template_path, "r") as f:
        template = f.read()
    
    available_types = [
        t for t in PARSER_PROMPT_REGISTRY.keys() if t != "FALLBACK_SUMMARY"
    ]
    formatted = ", ".join(f'"{doc_type}"' for doc_type in sorted(available_types))
    
    return template.replace("{available_types}", formatted)
