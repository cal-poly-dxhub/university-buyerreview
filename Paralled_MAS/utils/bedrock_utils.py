from model_registry import ModelRegistry
from utils import clean_file_name
import boto3
from utils import parse_pdf_form_fields, sanitize_doc_name

bedrock = boto3.client(service_name='bedrock-runtime')


def create_doc_messages(prompt, files):
    content = [{"text": prompt}]

    def get_file_format(filename):
        """Determine the file format based on file extension"""
        ext = filename.lower().split('.')[-1]
        format_mapping = {
            'pdf': 'pdf',
            'png': 'png',
            'jpg': 'jpeg',
            'jpeg': 'jpeg',
            'docx': 'docx',
            'txt': 'txt',
            'xlsx': 'xlsx'
        }
        return format_mapping.get(ext, 'pdf')  # default to pdf if unknown

    def is_image_format(format_type):
        """Check if the format is an image type"""
        return format_type in ['png', 'jpeg']

    for i, file in enumerate(files):
        safe_name = clean_file_name(file.name)
        file_bytes = file.read()
        file_format = get_file_format(file.name)

        if is_image_format(file_format):
            # For images, use the image block format
            content.insert(i, {
                "image": {
                    "format": file_format,
                    "source": {
                        "bytes": file_bytes
                    }
                }
            })
        else:
            # For documents (PDF, DOCX, TXT, XLSX), use the document block format
            content.insert(i, {
                "document": {
                    "name": safe_name,
                    "format": file_format,
                    "source": {
                        "bytes": file_bytes
                    }
                }
            })

    return [{"role": "user", "content": content}]


def query_bedrock_with_multiple_files(prompt, files, model_id=ModelRegistry.sonnet_4):
    messages = create_doc_messages(prompt, files)
    response = bedrock.converse(
        modelId=model_id,
        messages=messages,
        inferenceConfig={
            "temperature": 0,
            "top_p": 0,
            "top_k": 1
        }
    )
    content = response['output']['message']['content']
    return "".join([c['text'] for c in content if 'text' in c])


def query_bedrock_with_multiple_files_with_tools(prompt, files, model_id, tool_config):
    messages = create_doc_messages(prompt, files)

    # Step 1: Send the initial message
    response = bedrock.converse(
        modelId=model_id,
        messages=messages,
        inferenceConfig={"temperature": 0},
        toolConfig=tool_config,
    )
    bedrock_message = response["output"]["message"]
    messages.append(bedrock_message)

    content = bedrock_message["content"]
    tool_use = next((c["toolUse"] for c in content if "toolUse" in c), None)

    if not tool_use:
        return "".join([c["text"] for c in content if "text" in c])

    return handle_bedrock_tool_use(messages, tool_use, model_id, tool_config)


def handle_bedrock_tool_use(messages, tool_use, model_id, tool_config):
    # Step 2: Run the tool locally
    from tools import run_tool_by_name
    result_data = run_tool_by_name(tool_use["name"], tool_use["input"])

    # Decide if result is text or json
    if isinstance(result_data, str):
        content_block = [{"text": result_data}]
    elif isinstance(result_data, dict):
        content_block = [{"json": result_data}]
    else:
        raise TypeError("Tool output must be a str or dict")

    # Step 3: Respond with toolResult
    tool_result_message = {
        "role": "user",
        "content": [{
            "toolResult": {
                "toolUseId": tool_use["toolUseId"],
                "content": content_block,
                "status": "success"
            }
        }]
    }

    messages.append(tool_result_message)

    # Step 4: Send the updated full message thread
    followup = bedrock.converse(
        modelId=model_id,
        messages=messages,
        inferenceConfig={"temperature": 0},
        toolConfig=tool_config
    )

    return followup["output"]["message"]["content"][0].get("text", "<no text>")


def build_pdf_based_message(model_id, input_text, input_files):
    content_blocks = [{"text": input_text}]

    for f in input_files:
        doc_format = f.name.split(".")[-1]
        doc_bytes = f.read()
        doc_name = sanitize_doc_name(f.name)

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

    message = {"role": "user", "content": content_blocks}
    messages = [message]

    return bedrock.converse(modelId=model_id, messages=messages)
