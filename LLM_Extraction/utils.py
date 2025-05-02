import re
import os
import json
import boto3
import streamlit as st
from model_registry import ModelRegistry

bedrock = boto3.client(service_name='bedrock-runtime')


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


def create_doc_messages(prompt, files):
    content = [{"text": prompt}]
    for i, file in enumerate(files):
        safe_name = clean_file_name(file.name)
        file_bytes = file.read()
        content.insert(i, {
            "document": {
                "name": safe_name,
                "format": "pdf",
                "source": {
                    "bytes": file_bytes
                }
            }
        })
    return [{"role": "user", "content": content}]


def query_bedrock_with_multiple_pdfs(prompt, files, model_id=ModelRegistry.sonnet_3_7):
    messages = create_doc_messages(prompt, files)
    response = bedrock.converse(
        modelId=model_id,
        messages=messages,
        inferenceConfig={
            "temperature": 0
        }
    )
    return response['output']['message']['content'][0]['text']


def render_json_checklist(data):
    for item in data:
        status = item.get("status", "❓ Uncertain")
        icon = {
            "✅ Passed": "✅",
            "❌ Missing": "❌",
            "🟡 Exception": "⚠️",
            "❓ Uncertain": "❓"
        }.get(status, "❓")
        with st.expander(f"{icon} {item['check']}"):
            st.markdown(f"**Note:** {item['note']}")

def render_json_output(data):
    for property_name, property_info in data.items():
        match = property_info.get("match", "")
        if match == "Yes":
            st.success(f"\u2705 {property_name}")
        elif match == "No":
            st.error(f"\u274C {property_name}")
        elif match == "Mostly Yes":
            st.warning(f"\u26A0\uFE0F {property_name}")
        else:
            st.info(property_name)

        sources = {k: v for k, v in property_info.items() if k != "match"}
        for source_name, value in sources.items():
            st.markdown(f"- **{source_name}**: {value}")
        st.markdown("---")


def render_key_fields(key_fields):
    for k, v in key_fields.items():
        if isinstance(v, list):
            st.markdown(f"**{k}**:")
            for i, item in enumerate(v, 1):
                st.markdown(f"- **Item {i}:**")
                for sub_k, sub_v in item.items():
                    st.markdown(f"  - {sub_k}: {sub_v}")
        else:
            st.markdown(f"- **{k}**: {v}")

def render_parsed_documents(parsed_data: dict):
    st.success("✅ Documents parsed successfully")
    st.subheader("📋 Extracted Data")
    for doc_name, content in parsed_data.items():
        with st.expander(doc_name):
            if isinstance(content, dict) and "Key Fields" in content:
                st.markdown(f"**Document Type:** {content.get('Document Type', 'Unknown')}")
                st.markdown(f"**Summary:** {content.get('Summary', '')}")
                render_key_fields(content.get("Key Fields", {}))
            else:
                st.json(content)