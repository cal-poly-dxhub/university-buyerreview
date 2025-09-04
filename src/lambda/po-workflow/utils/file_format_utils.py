import re
import os
import json
import re
import os
import io
from PyPDF2 import PdfReader
import streamlit as st

def sanitize_doc_name(name: str) -> str:
    cleaned_name = re.sub(r"[^\w\s\-\(\)\[\]]", "", os.path.splitext(name)[0])
    return re.sub(r"\s+", " ", cleaned_name).strip() or "Document"

def parse_pdf_form_fields(file_bytes: bytes) -> dict:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        fields = reader.get_fields()
        if not fields:
            return {}
        st.write("Fields successfully parsed.")
        return {name: field.get("/V") for name, field in fields.items()}
    except Exception as e:
        return {"error": str(e)}


def clean_file_name(file_name):
    base_name = os.path.basename(file_name)
    name, _ = os.path.splitext(base_name)
    cleaned_name = re.sub(r"[^\w\s\-\(\)\[\]]", "", name)
    cleaned_name = re.sub(r"\s+", " ", cleaned_name).strip()
    return cleaned_name if cleaned_name else "Document"


def try_parse_json_like(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            start = min([i for i in (
                text.find('['), text.find('{')) if i != -1])
            end = max([text.rfind(']'), text.rfind('}')]) + 1
            cleaned = text[start:end].strip()
            return json.loads(cleaned)
        except Exception:
            return None
