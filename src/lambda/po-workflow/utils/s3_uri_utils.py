from urllib.parse import urlparse, unquote
import io
import boto3
import tempfile
import json
import os
import mimetypes
import re

s3 = boto3.client("s3")

def filelike_from_s3_uri(s3_uri: str) -> io.BytesIO:
    """
    Takes s3://bucket/key.pdf and returns a file-like object
    with .name and .read() for use in your existing functions.
    """
    parsed = urlparse(s3_uri)
    if parsed.scheme != "s3":
        raise ValueError(f"Not a valid S3 URI: {s3_uri}")
    bucket = parsed.netloc
    key = unquote(parsed.path.lstrip("/"))
    filename = key.split("/")[-1] or "document.pdf"

    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj["Body"].read()  # bytes

    buf = io.BytesIO(data)
    buf.name = filename  # your helper uses file.name
    buf.seek(0)
    return buf

def files_from_s3_uris(s3_uris):
    return [filelike_from_s3_uri(uri) for uri in s3_uris]

def upload_json_to_s3(data: dict, bucket: str, key: str):
    """
    Upload a JSON dict as a file to S3.

    :param data: Python dict (will be converted to JSON)
    :param bucket: S3 bucket name
    :param key: S3 object key (path/filename.json)
    """
    # Convert dict to JSON string
    json_str = json.dumps(data, indent=2)

    # Write to a temporary file
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as tmp_file:
        tmp_file.write(json_str)
        tmp_file.flush()
        tmp_file_name = tmp_file.name

    # Upload to S3
    s3_client = boto3.client("s3")
    s3_client.upload_file(tmp_file_name, bucket, key)

    print(f"Uploaded JSON to s3://{bucket}/{key}")

def get_doc_type_from_s3_uri(s3_uri: str) -> str:
    """
    Extracts the document type from an S3 URI based on file extension.

    :param s3_uri: e.g. 's3://my-bucket/path/to/file.pdf'
    :return: document type string (pdf, txt, html, json, docx, etc.)
    """
    # Validate format of S3 URI
    if not s3_uri.startswith("s3://"):
        raise ValueError(f"Invalid S3 URI: {s3_uri}")

    # Extract the filename from the key
    filename = os.path.basename(s3_uri)

    # Guess extension
    ext = os.path.splitext(filename)[1].lower().lstrip(".")

    # Map extension to document type (customize as needed)
    known_map = {
        "pdf": "pdf",
        "txt": "txt",
        "html": "html",
        "htm": "html",
        "json": "json",
        "csv": "csv",
        "docx": "docx",
        "xlsx": "xlsx",
        "pptx": "pptx",
        "md": "md",
        'png': 'png',
        'jpg': 'jpeg',
        'jpeg': 'jpeg',
    }

    if ext in known_map:
        return known_map[ext]

    # Fall back to mimetypes
    ctype, _ = mimetypes.guess_type(filename)
    if ctype:
        # Use last part of MIME type as doc type
        return ctype.split("/")[-1]

    return "pdf"  # safe fallback

def get_file_name_from_s3_uri(s3_uri: str) -> str:
    """
    Extracts the base file name (without extension) from an S3 URI.
    
    Example:
    s3://my-bucket/path/to/file.pdf -> file
    """
    # Get the last part after "/"
    file_with_ext = os.path.basename(s3_uri)
    
    # Remove the extension
    file_name, _ = os.path.splitext(file_with_ext)
    
    return file_name

def strip_filename_from_s3_uri(s3_uri: str) -> str:
    """Return the base filename without extension from an S3 URI."""
    path = urlparse(s3_uri).path  # /Sample Attachments/.../filename.pdf
    filename = os.path.basename(path)  # filename.pdf
    name, _ = os.path.splitext(filename)  # filename
    return name

def create_doc_messages_s3_uri(prompt, uri_list):
    content = [{"text": prompt}]

    def is_image_format(format_type):
        """Check if the format is an image type"""
        return format_type in ['png', 'jpeg']
        
    for i, uri in enumerate(uri_list):
        uri = uri["source"]["uri"]

        print(uri)

        file_format = get_doc_type_from_s3_uri(uri)
        safe_name = get_file_name_from_s3_uri(uri)

        if is_image_format(file_format):
            # For images, use the image block format
            content.insert(i, {
                "image": {
                    "format": file_format,
                    "source": {
                        's3Location': {
                            'uri': uri,
                            'bucketOwner': "077938161517"
                        }
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
                        's3Location': {
                            'uri': uri,
                            'bucketOwner': '077938161517'
                        }
                    }
                }
            })
    return [{"role": "user", "content": content}]