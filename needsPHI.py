

# #https://docs.aws.amazon.com/bedrock/latest/userguide/inference-invoke.html

# #https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-examples.html

# # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# # SPDX-License-Identifier: Apache-2.0

# import boto3

# import time

# from botocore.exceptions import ClientError

# import streamlit as st

# def generate_message(bedrock_client,
#                      model_id,
#                      input_text,
#                      inputFile):


#     # Get format from path and read the path
#     input_document_format = inputFile.name.split(".")[-1]
#     input_document = inputFile.read()

#     # Message to send.
#     message = {
#         "role": "user",
#         "content": [
#             {
#                 "document": {
#                     "name": "MyDocument",
#                     "format": input_document_format,
#                     "source": {
#                         "bytes": input_document
#                     }
#                 }
#             },
#             {
#                 "text": input_text
#             }
#         ]
#     }

#     messages = [message]

#     # Send the message.
#     response = bedrock_client.converse(
#         modelId=model_id,
#         messages=messages
#     )

#     return response


# def main():

#     model_id = "anthropic.claude-3-5-haiku-20241022-v1:0"
#     input_text = """The contents of this document should be describing a statement of work for a
#       particular service to be carried out. If the service seems at all like it would require
#       the use of Personal Health Information, say {{PHI}}, in this exact format. Otherwise, say {{NOPHI}}."""
    

#     st.title("UCSD Buyer: Check if the PHI Agreement needs to be signed")
#     uploaded_files = st.file_uploader(
#     "Upload Relevant Files", accept_multiple_files=True
#     )
    


#     if st.button("Done uploading files"):
#         st.divider()
        
#         for file in uploaded_files:
#             try:

#                 bedrock_client = boto3.client(service_name="bedrock-runtime")

#                 with st.spinner("Processing..."):
#                     response = generate_message(bedrock_client, model_id, input_text, file)

#                 output_message = response['output']['message']

#                 print(f"Role: {output_message['role']}")

#                 st.write(f"For input file: {file.name}")
#                 for content in output_message['content']:
#                     st.write(f"LLM Output: {content['text']}")
#                 st.divider()

#                 token_usage = response['usage']
#                 print(f"Input tokens:  {token_usage['inputTokens']}")
#                 print(f"Output tokens:  {token_usage['outputTokens']}")
#                 print(f"Total tokens:  {token_usage['totalTokens']}")
#                 print(f"Stop reason: {response['stopReason']}")
#                 time.sleep(2)

#             except ClientError as err:
#                 message = err.response['Error']['Message']
#                 print(f"A client error occured: {message}")

#             else:
#                 print(f"Finished generating text with model {model_id}.")


# if __name__ == "__main__":
#     main()

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import boto3
from botocore.exceptions import ClientError
import streamlit as st
import re

def _sanitize_doc_name(name: str) -> str:                         

    cleaned = re.sub(r"[^A-Za-z0-9\-\(\)\[\]\s]", "_", name)      
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()             
    return cleaned or "Document"                                  

def generate_message(
        bedrock_client,
        model_id,
        input_text,
        input_files
    ):

    content_blocks = [{"text": input_text}]

    for f in input_files:
        doc_format = f.name.split(".")[-1]
        doc_bytes  = f.read()
        doc_name   = _sanitize_doc_name(f.name)                   

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
    model_id   = "us.amazon.nova-premier-v1:0"
    input_text = (
        "The contents of this document should be describing a statement "
        "of work for a particular service to be carried out. If the service "
        "seems at all like it would require the use of Personal Health "
        "Information, say {{PHI}} in this exact format, and give the exact word for word quotes from which you decided that this contains PHI. Otherwise, say {{NOPHI}} with the same reasoning. "
    )

    st.title("UCSD Buyer: Check if the PHI Agreement needs to be signed")
    uploaded_files = st.file_uploader(
        "Upload Relevant Files", accept_multiple_files=True
    )

    if st.button("Done uploading files"):
        st.divider()

        if not uploaded_files:
            st.warning("No files uploaded.")
            return

        try:
            bedrock_client = boto3.client(service_name="bedrock-runtime")

            with st.spinner("Processing all documents in one call…"):      
                response = generate_message(
                    bedrock_client, model_id, input_text, uploaded_files   
                )

            output_message = response["output"]["message"]
            st.write("Model response:")
            for block in output_message["content"]:
                if "text" in block:
                    st.write(block["text"])

            token_usage = response["usage"]
            st.caption(
                f"Tokens – in: {token_usage['inputTokens']}, "
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
