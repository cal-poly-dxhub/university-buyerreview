# import json
# import time
# from concurrent.futures import ThreadPoolExecutor
# from concurrent.futures import as_completed
# from pypdf import PdfReader
# import boto3 
# from botocore.exceptions import ClientError
# from botocore.exceptions import ReadTimeoutError
# from botocore.config import Config
# from botocore.exceptions import EventStreamError

# import uuid


# FILE = 'Statement of work examples/SOWExample6.pdf'
# TEMPLATE = 'config1.json'

# def pdf_to_text(file):
#     reader = PdfReader(file)
#     contents = ''
#     for page in reader.pages:
#         contents += page.extract_text()
#     return contents

# DOC_TEMPLATE = f"Document: {pdf_to_text(FILE)}\n\nTemplate: {TEMPLATE}"

# def invokeflow(input1):
#     config = Config(read_timeout=1000,
#                    connect_timeout=100,
#                    retries={"max_attempts": 2})

#     client = boto3.client("bedrock-agent-runtime", config=config, region_name="us-west-2")

#     response = client.invoke_flow(
#         flowIdentifier='TMILSXKNST',
#         flowAliasIdentifier='FILM0D9D66',
#         inputs=[
#             {
#                 'content': {
#                     "document": str(input1)
#                 },
#             'nodeName': 'FlowInputNode',
#             'nodeOutputName': 'document'
#             }
#         ]
#     )
#     stream = response['responseStream']
#     full_response = ''
#     for event in stream:
#         print(event)
#     return full_response



# if __name__ == "__main__":
#     print(invokeflow(DOC_TEMPLATE))