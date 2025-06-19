import asyncio
from tools import build_general_doc_prompt_from_file
from utils import try_parse_json_like, query_bedrock_with_multiple_pdfs_with_tools
from model_registry import ModelRegistry
from tools import get_tool_config

# --- Synchronous single document processor ---


def route_and_parse_document(file, prompt_path="Task_Prompts/Parser.txt"):
    prompt = build_general_doc_prompt_from_file(prompt_path)

    response = query_bedrock_with_multiple_pdfs_with_tools(
        prompt=prompt,
        files=[file],
        model_id=ModelRegistry.sonnet_3_7,
        tool_config=get_tool_config([
            "get_prompt_for_doc_type",
            "summarize_document"
        ])
    )

    parsed = try_parse_json_like(response)

    if parsed:
        return {
            "result": parsed
        }
    else:
        return {
            "result": None,
            "error": "❌ Failed to parse document.",
            "raw": response
        }


# --- Async wrapper for single document ---
async def async_parse_document(file):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, route_and_parse_document, file)

# --- Parse all uploaded documents in parallel ---


async def parse_documents_parallel(files):
    tasks = [async_parse_document(file) for file in files]
    results = await asyncio.gather(*tasks)
    return dict(zip([file.name for file in files], results))
