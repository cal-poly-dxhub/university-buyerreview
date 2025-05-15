
# import boto3
# from botocore.exceptions import ClientError
# import streamlit as st
# import re

# def _sanitize_doc_name(name: str) -> str:                         

#     cleaned = re.sub(r"[^A-Za-z0-9\-\(\)\[\]\s]", "_", name)      
#     cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()             
#     return cleaned or "Document"                                  

# def generate_message(
#         bedrock_client,
#         model_id,
#         input_text,
#         input_files
#     ):

#     content_blocks = [{"text": input_text}]

#     for f in input_files:
#         doc_format = f.name.split(".")[-1]
#         doc_bytes  = f.read()
#         doc_name   = _sanitize_doc_name(f.name)                   

#         content_blocks.append({
#             "document": {
#                 "name": doc_name,                                 
#                 "format": doc_format,
#                 "source": {"bytes": doc_bytes}
#             }
#         })

#     message  = {"role": "user", "content": content_blocks}
#     messages = [message]

#     return bedrock_client.converse(modelId=model_id, messages=messages)

# def main():
#     model_id   = "anthropic.claude-3-5-haiku-20241022-v1:0"
#     input_text = (
#         "The contents of this document should be describing a statement "
#         "of work for a particular service to be carried out. If the service "
#         "seems at all like it would require the use of Personal Health "
#         "Information, say {{PHI}} in this exact format, and give the exact word for word quotes from which you decided that this contains PHI. Otherwise, say {{NOPHI}} with the same reasoning. "
#     )

#     st.title("UCSD Buyer: Check if the PHI Agreement needs to be signed")
#     uploaded_files = st.file_uploader(
#         "Upload Relevant Files", accept_multiple_files=True
#     )

#     if st.button("Done uploading files"):
#         st.divider()

#         if not uploaded_files:
#             st.warning("No files uploaded.")
#             return

#         try:
#             bedrock_client = boto3.client(service_name="bedrock-runtime")

#             with st.spinner("Processing all documents in one call…"):      
#                 response = generate_message(
#                     bedrock_client, model_id, input_text, uploaded_files   
#                 )
#             output_message = response["output"]["message"]
#             st.write("Model response:")
#             for block in output_message["content"]:
#                 if "text" in block:
#                     st.write(block["text"])

#             token_usage = response["usage"]
#             st.caption(
#                 f"Tokens in: {token_usage['inputTokens']}, "
#                 f"out: {token_usage['outputTokens']}, "
#                 f"total: {token_usage['totalTokens']}. "
#                 f"Stop reason: {response['stopReason']}"
#             )

#         except ClientError as err:
#             st.error(f"A client error occurred: {err.response['Error']['Message']}")
#         else:
#             print(f"Finished generating text with model {model_id}.")


# if __name__ == "__main__":
#     main()





## WITH PDF PARSING:

import boto3
from botocore.exceptions import ClientError
import streamlit as st
import re
from PyPDF2 import PdfReader
import io

def _sanitize_doc_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9\-\(\)\[\]\s]", "_", name)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned or "Document"

def parse_pdf_form_fields(file_bytes) -> dict:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        fields = reader.get_fields()
        if not fields:
            return {}
        st.write("Fields successfully parsed.")
        return {name: field.get("/V") for name, field in fields.items()}
    except Exception as e:
        return {"error": str(e)}

def generate_message(bedrock_client, model_id, input_text, input_files):
    content_blocks = [{"text": input_text}]

    for f in input_files:
        doc_format = f.name.split(".")[-1]
        doc_bytes  = f.read()
        doc_name   = _sanitize_doc_name(f.name)

        # Add parsed form fields if available
        parsed_fields = parse_pdf_form_fields(doc_bytes)
        if parsed_fields:
            parsed_output = f"{doc_name} form parsed output, use this for information about the interactive form: {parsed_fields}"
            input_text += "\n\n" + parsed_output

        content_blocks.append({
            "document": {
                "name": doc_name,
                "format": doc_format,
                "source": {"bytes": doc_bytes}
            }
        })

    message  = {"role": "user", "content": content_blocks}
    messages = [message]

    return bedrock_client.converse(modelId=model_id, messages=messages)

def main():
    model_id   = "anthropic.claude-3-5-haiku-20241022-v1:0"
    base_prompt = (
        "The contents of these documents describe the quotes and service details"
        "of a particular requested good or service. If the actual service itself"
        "seems at all like it would require the use of Personal Health "
        "Information, say {{PHI}} in this exact format, and give the exact"
        " word for word quotes from which you decided that this contains PHI."
        " Otherwise, say {{NOPHI}} with the same reasoning."
    )

    st.title("UCSD Buyer: Check if the PHI Agreement needs to be signed")
    uploaded_files = st.file_uploader("Upload Relevant Files", accept_multiple_files=True)

    if st.button("Done uploading files"):
        st.divider()

        if not uploaded_files:
            st.warning("No files uploaded.")
            return

        try:
            bedrock_client = boto3.client(service_name="bedrock-runtime")

            with st.spinner("Processing all documents in one call…"):
                response = generate_message(
                    bedrock_client, model_id, base_prompt, uploaded_files
                )
            output_message = response["output"]["message"]
            st.write("Model response:")
            for block in output_message["content"]:
                if "text" in block:
                    st.write(block["text"])

            token_usage = response["usage"]
            st.caption(
                f"Tokens in: {token_usage['inputTokens']}, "
                f"out: {token_usage['outputTokens']}, "
                f"total: {token_usage['totalTokens']}. "
                f"Stop reason: {response['stopReason']}"
            )

        except ClientError as err:
            st.error(f"A client error occurred: {err.response['Error']['Message']}")
        else:
            print(f"Finished generating text with model {model_id}.")

if __name__ == "__main__":
    main()
