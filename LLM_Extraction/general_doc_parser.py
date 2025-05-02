from prompts import general_doc_prompt
from utils import try_parse_json_like, query_bedrock_with_multiple_pdfs
from model_registry import ModelRegistry

def parse_documents_together(files):
    result_text = query_bedrock_with_multiple_pdfs(
        general_doc_prompt, files, model_id=ModelRegistry.sonnet_3_7)
    parsed = try_parse_json_like(result_text)
    return parsed if parsed else {"error": "Failed to parse JSON", "raw": result_text}
