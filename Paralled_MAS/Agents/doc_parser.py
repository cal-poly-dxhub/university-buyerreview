import asyncio
from tools import build_general_doc_prompt_from_file
from utils import (
    try_parse_json_like,
    query_bedrock_with_multiple_files_with_tools,
    compress_file_if_needed,
    get_file_size_mb,
    MAX_CHUNK_SIZE_MB
)
from model_registry import ModelRegistry
from tools import get_tool_config
from state import PipelineState


# --- Synchronous single document processor ---
def route_and_parse_document(file, prompt_path="Task_Prompts/Parser.txt"):
    prompt = build_general_doc_prompt_from_file(prompt_path)

    response = query_bedrock_with_multiple_files_with_tools(
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


async def async_parse_document(file):
    compressed_file = compress_file_if_needed(file, file.name)
    compressed_file.name = file.name
    size_mb = get_file_size_mb(compressed_file)

    if size_mb > MAX_CHUNK_SIZE_MB:
        return {
            "result": None,
            "error": f"❌ Even after compression, file '{file.name}' is still over 4.5MB.",
        }

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, route_and_parse_document, compressed_file)


# --- Parse all uploaded documents in parallel ---
async def parse_documents_parallel(files):
    tasks = [async_parse_document(file) for file in files]
    results = await asyncio.gather(*tasks)
    return dict(zip([file.name for file in files], results))


async def parse_documents_node(state: PipelineState) -> PipelineState:
    parsed = await parse_documents_parallel(state["uploaded_files"])
    return {"parsed_data": parsed}
