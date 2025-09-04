# import os
# import asyncio
# from urllib.parse import urlparse

# from tools import build_general_doc_prompt_from_file, get_tool_config
# from utils import (
#     try_parse_json_like,
#     query_bedrock_with_multiple_files_with_tools,
#     # compress_file_if_needed,  # only for file-like inputs
#     # get_file_size_mb,
#     # MAX_CHUNK_SIZE_MB
# )
# from model_registry import ModelRegistry
# from state import PipelineState


# def is_s3_uri(x) -> bool:
#     return isinstance(x, str) and x.startswith("s3://")


# def s3_uri_to_name(s3_uri: str) -> str:
#     # e.g., s3://bucket/path/to/My Doc.v2.pdf -> "My Doc.v2"
#     base = os.path.basename(urlparse(s3_uri).path)
#     name, _ = os.path.splitext(base)
#     return name or base or "file"


# def get_display_name(file_or_uri) -> str:
#     if hasattr(file_or_uri, "name") and isinstance(file_or_uri.name, str):
#         # file-like (e.g., Streamlit UploadedFile, BytesIO with .name)
#         base = os.path.basename(file_or_uri.name)
#         name, _ = os.path.splitext(base)
#         return name or base or "file"
#     if is_s3_uri(file_or_uri):
#         return s3_uri_to_name(file_or_uri)
#     # Fallback
#     return "file"

# def normalize_for_bedrock(file_or_uri):
#     """
#     Return a value suitable for `files=` in query_bedrock_with_multiple_files_with_tools.
#     Adjust this if your wrapper expects a different schema for S3 inputs.
#     """
#     if is_s3_uri(file_or_uri):
#         # Option A: if your wrapper accepts raw S3 URIs:
#         # return file_or_uri

#         # Option B (common): explicit source dict
#         return {"source": {"type": "s3", "uri": file_or_uri}}

#     # File-like objects pass through as-is
#     return file_or_uri


# # --- Synchronous single document processor ---
# def route_and_parse_document(file_or_uri, prompt_path="Task_Prompts/Parser.txt"):
#     prompt = build_general_doc_prompt_from_file(prompt_path)

#     payload = normalize_for_bedrock(file_or_uri)

#     response = query_bedrock_with_multiple_files_with_tools(
#         prompt=prompt,
#         files=[payload],
#         model_id=ModelRegistry.sonnet_3,
#         tool_config=get_tool_config([
#             "get_prompt_for_doc_type",
#             "summarize_document"
#         ])
#     )

#     parsed = try_parse_json_like(response)
#     if parsed:
#         return {"result": parsed}
#     else:
#         return {
#             "result": None,
#             "error": "❌ Failed to parse document.",
#             "raw": response
#         }


# async def async_parse_document(file_or_uri):
#     # If you later re-enable compression/size checks, guard them so they only run on file-like inputs.
#     return await asyncio.to_thread(route_and_parse_document, file_or_uri)


# # --- Parse all uploaded documents in parallel ---
# async def parse_documents_parallel(files_or_uris):
#     tasks = [async_parse_document(x) for x in files_or_uris]
#     results = await asyncio.gather(*tasks)
#     keys = [get_display_name(x) for x in files_or_uris]
#     return dict(zip(keys, results))


# async def parse_documents_node(state: PipelineState) -> PipelineState:
#     parsed = await parse_documents_parallel(state["uploaded_files"])
#     return {"parsed_data": parsed}


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
# from config.processing_limits import (
#     MAX_DOCUMENTS_PER_BATCH, 
#     BATCH_DELAY_SECONDS,
#     MAX_RETRIES,
#     RETRY_DELAY_SECONDS,
#     ENABLE_PROGRESS_LOGGING
# )

# --- Synchronous single document processor ---
def route_and_parse_document(file, prompt_path="Task_Prompts/Parser.txt"):
    prompt = build_general_doc_prompt_from_file(prompt_path)

    response = query_bedrock_with_multiple_files_with_tools(
        prompt=prompt,
        files=[file],
        model_id=ModelRegistry.sonnet_3,
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
    # compressed_file = compress_file_if_needed(file, file.name)
    # compressed_file.name = file.name
    # size_mb = get_file_size_mb(compressed_file)

    # if size_mb > MAX_CHUNK_SIZE_MB:
    #     return {
    #         "result": None,
    #         "error": f"❌ Even after compression, file '{file.name}' is still over 4.5MB.",
    #     }

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, route_and_parse_document, file)

# --- Parse all uploaded documents in parallel ---
async def parse_documents_parallel(files):
    tasks = [async_parse_document(file) for file in files]
    results = await asyncio.gather(*tasks)
    
    return dict(zip([file.name for file in files], results))

# async def process_batch_with_retry(batch, batch_num, total_batches):
#     """
#     Process a batch of documents with retry logic for throttling exceptions.
#     """
#     for attempt in range(MAX_RETRIES + 1):
#         try:
#             if ENABLE_PROGRESS_LOGGING:
#                 print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} documents) - Attempt {attempt + 1}")
            
#             tasks = [async_parse_document(file) for file in batch]
#             batch_results = await asyncio.gather(*tasks)
            
#             if ENABLE_PROGRESS_LOGGING:
#                 print(f"✅ Batch {batch_num}/{total_batches} completed successfully")
            
#             return batch_results
            
#         except Exception as e:
#             error_msg = str(e).lower()
#             if "throttling" in error_msg or "rate limit" in error_msg or "too many requests" in error_msg:
#                 if attempt < MAX_RETRIES:
#                     wait_time = RETRY_DELAY_SECONDS * (2 ** attempt)  # Exponential backoff
#                     if ENABLE_PROGRESS_LOGGING:
#                         print(f"⚠️  Throttling detected in batch {batch_num}. Retrying in {wait_time}s... (Attempt {attempt + 1}/{MAX_RETRIES + 1})")
#                     await asyncio.sleep(wait_time)
#                     continue
#                 else:
#                     if ENABLE_PROGRESS_LOGGING:
#                         print(f"❌ Batch {batch_num} failed after {MAX_RETRIES + 1} attempts due to throttling")
#                     raise
#             else:
#                 # Non-throttling error, don't retry
#                 if ENABLE_PROGRESS_LOGGING:
#                     print(f"❌ Batch {batch_num} failed with non-throttling error: {str(e)}")
#                 raise
    
#     # This should never be reached, but just in case
#     raise Exception(f"Batch {batch_num} failed after all retry attempts")


# # --- Parse documents in batches to avoid throttling ---
# async def parse_documents_parallel(files):
#     if not files:
#         return {}
    
#     total_files = len(files)
#     if ENABLE_PROGRESS_LOGGING:
#         print(f"Processing {total_files} documents in batches of {MAX_DOCUMENTS_PER_BATCH}")
    
#     # Check if we exceed the maximum limit
#     if total_files > MAX_DOCUMENTS_PER_BATCH:
#         if ENABLE_PROGRESS_LOGGING:
#             print(f"⚠️  Warning: {total_files} documents exceed recommended limit of {MAX_DOCUMENTS_PER_BATCH}")
#             print(f"   Processing in batches with {BATCH_DELAY_SECONDS}s delays to avoid throttling")
    
#     all_results = {}
    
#     # Process files in batches
#     for i in range(0, total_files, MAX_DOCUMENTS_PER_BATCH):
#         batch = files[i:i + MAX_DOCUMENTS_PER_BATCH]
#         batch_num = (i // MAX_DOCUMENTS_PER_BATCH) + 1
#         total_batches = (total_files + MAX_DOCUMENTS_PER_BATCH - 1) // MAX_DOCUMENTS_PER_BATCH
        
#         # Process current batch with retry logic
#         try:
#             batch_results = await process_batch_with_retry(batch, batch_num, total_batches)
            
#             # Store results
#             for file, result in zip(batch, batch_results):
#                 all_results[file.name] = result
                
#         except Exception as e:
#             if ENABLE_PROGRESS_LOGGING:
#                 print(f"❌ Failed to process batch {batch_num}: {str(e)}")
#             # Continue with next batch instead of failing completely
#             for file in batch:
#                 all_results[file.name] = {
#                     "result": None,
#                     "error": f"❌ Batch processing failed: {str(e)}"
#                 }
        
#         # Add delay between batches to avoid throttling (except for the last batch)
#         if i + MAX_DOCUMENTS_PER_BATCH < total_files:
#             if ENABLE_PROGRESS_LOGGING:
#                 print(f"Waiting {BATCH_DELAY_SECONDS}s before next batch...")
#             await asyncio.sleep(BATCH_DELAY_SECONDS)
    # if ENABLE_PROGRESS_LOGGING:
    #     print(f"✅ Completed processing {total_files} documents")
    # return all_results


async def parse_documents_node(state: PipelineState) -> PipelineState:
    parsed = await parse_documents_parallel(state["uploaded_files"])
    # uploaded_files = state.get("uploaded_files", [])
    
    # # Check document limit before processing
    # if len(uploaded_files) > MAX_DOCUMENTS_PER_BATCH:
    #     if ENABLE_PROGRESS_LOGGING:
    #         print(f"⚠️  Processing {len(uploaded_files)} documents (exceeds recommended limit of {MAX_DOCUMENTS_PER_BATCH})")
    #         print(f"   This may take longer due to throttling protection")
    
    # parsed = await parse_documents_parallel(uploaded_files)
    return {"parsed_data": parsed}