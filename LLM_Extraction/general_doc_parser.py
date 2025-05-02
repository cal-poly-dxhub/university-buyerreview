from prompts import general_doc_prompt
from utils import try_parse_json_like, query_bedrock_with_multiple_pdfs

MODEL_ID = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"

def parse_documents_together(files):
    result_text = query_bedrock_with_multiple_pdfs(
        general_doc_prompt, files, model_id=MODEL_ID)
    parsed = try_parse_json_like(result_text)
    return parsed if parsed else {"error": "Failed to parse JSON", "raw": result_text}
