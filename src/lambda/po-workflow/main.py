import os, pathlib

# Fontconfig picks cache from XDG_CACHE_HOME/fontconfig, or HOME/.cache/fontconfig, or /var/cache/fontconfig
os.environ.setdefault("XDG_CACHE_HOME", "/tmp")
os.environ.setdefault("HOME", "/tmp")
os.environ.setdefault("FONTCONFIG_PATH", "/etc/fonts")             # where fonts.conf lives
os.environ.setdefault("FONTCONFIG_FILE", "/etc/fonts/fonts.conf")  # be explicit

# Ensure /tmp/fontconfig exists before any WeasyPrint/Pango import happens
pathlib.Path("/tmp/fontconfig").mkdir(parents=True, exist_ok=True)

# (optional) quick sanity log to confirm writability
try:
    test_path = "/tmp/fontconfig/.writable-test"
    open(test_path, "wb").write(b"ok")
    os.remove(test_path)
except Exception as e:
    print("Fontconfig cache NOT writable:", e)

import re
import json
import time
import uuid
import base64
import boto3
import asyncio
import urllib.parse
from io import BytesIO
from pathlib import Path

from Graphs.full_pipeline import build_full_pipeline_graph
from utils import run_json_pipeline_with_stream

# ------------------------------------------------------------------------------
# Environment (WeasyPrint / Fontconfig)
# ------------------------------------------------------------------------------
import os, pathlib
os.environ.setdefault("XDG_CACHE_HOME", "/tmp")
os.environ.setdefault("HOME", "/tmp")                 # good fallback
os.environ.setdefault("FONTCONFIG_PATH", "/etc/fonts")
os.environ.setdefault("FONTCONFIG_FILE", "/etc/fonts/fonts.conf")
pathlib.Path("/tmp/fontconfig").mkdir(parents=True, exist_ok=True)

s3 = boto3.client("s3")

# Prefer envs provided by CDK
DOCUMENTS_BUCKET = os.environ.get("DOCUMENTS_BUCKET", "077938161517-us-west-2-dxhub-ub-bkt")
RESULTS_BUCKET    = os.environ.get("RESULTS_BUCKET",   "077938161517-us-west-2-dxhub-results-bkt")
REQUESTS_PREFIX   = os.environ.get("REQUESTS_PREFIX",  "jobs/")  # where job JSONs are dropped

class NamedBytesIO(BytesIO):
    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name = name  # give it a filename for libs that call .name

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
_S3_URI_RE = re.compile(r"^s3://([^/]+)/(.+)$")

def _to_s3_uri(bucket, key):
    return f"s3://{bucket}/{urllib.parse.unquote_plus(key)}"

def _extract_s3_uris_from_event(event):
    uris = []
    for rec in event.get("Records", []):
        if rec.get("eventSource") == "aws:s3":
            b = rec["s3"]["bucket"]["name"]
            k = urllib.parse.unquote_plus(rec["s3"]["object"]["key"])
            uris.append(_to_s3_uri(b, k))
    return uris

def _parse_s3_uri(uri: str):
    m = _S3_URI_RE.match(uri)
    if not m:
        raise ValueError(f"Bad S3 URI: {uri}")
    bucket, key = m.group(1), urllib.parse.unquote_plus(m.group(2))
    return bucket, key

def _guess_media_type(key: str):
    k = key.lower()
    if k.endswith(".pdf"):  return "application/pdf"
    if k.endswith(".png"):  return "image/png"
    if k.endswith(".jpg") or k.endswith(".jpeg"): return "image/jpeg"
    if k.endswith(".txt"):  return "text/plain"
    if k.endswith(".html") or k.endswith(".htm"): return "text/html"
    if k.endswith(".docx"): return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if k.endswith(".pptx"): return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    if k.endswith(".csv"):  return "text/csv"
    return "application/octet-stream"

def _s3_uri_to_attachment(uri: str):
    """Load S3 object and return a Bedrock 'attachment' with base64 'bytes'."""
    bucket, key = _parse_s3_uri(uri)
    obj = s3.get_object(Bucket=bucket, Key=key)
    raw = obj["Body"].read()
    return NamedBytesIO(raw, Path(key).name)
    # return {
    #     "name": uri,
    #     "mediaType": _guess_media_type(key),
    #     "source": {"bytes": b64},  # base64 BYTES
    # }

def _unique_result_key(job_id: str | None, prefix="summaries/", suffix=".pdf"):
    ts = time.strftime("%Y%m%d-%H%M%S")
    jid = job_id or uuid.uuid4().hex[:8]
    return f"{prefix}{ts}-{jid}{suffix}"

def _load_job_from_event(event):
    """
    If this is an S3:ObjectCreated for a job JSON at REQUESTS_PREFIX, load and return:
    (s3_uris, metadata, job_id, job_bucket, job_key). Else return (None, None, None, None, None).
    """
    for rec in event.get("Records", []):
        if rec.get("eventSource") == "aws:s3":
            b = rec["s3"]["bucket"]["name"]
            k = urllib.parse.unquote_plus(rec["s3"]["object"]["key"])
            if k.startswith(REQUESTS_PREFIX) and k.endswith(".json"):
                obj = s3.get_object(Bucket=b, Key=k)
                data = json.loads(obj["Body"].read())
                return data.get("s3_uris"), data.get("metadata", {}), data.get("job_id"), b, k
    return None, None, None, None, None

# ------------------------------------------------------------------------------
# Lambda handler
# ------------------------------------------------------------------------------
def handler(event, context):
    # 0) Prefer job-file trigger: S3:ObjectCreated on jobs/*.json
    s3_uris, metadata, job_id, job_bucket, job_key = _load_job_from_event(event)

    # 1) Back-compat: direct invoke or S3 event of documents
    if not s3_uris:
        # Direct list in event
        if isinstance(event.get("s3_uris"), list):
            s3_uris = event["s3_uris"]
        # Or raw S3 object create (documents)
        if not s3_uris:
            s3_uris = _extract_s3_uris_from_event(event)

    if not s3_uris:
        return {"statusCode": 400, "body": json.dumps({"error": "No S3 URIs found."})}

    # 2) Build pipeline
    pipeline = build_full_pipeline_graph()

    # 3) Build Bedrock-friendly attachments
    try:
        attachments = [_s3_uri_to_attachment(u) for u in s3_uris]
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": f"Failed to load S3 objects: {str(e)}"})}

    # 4) Run pipeline (prefer attachments signature; fall back to s3_uris)
    # try:
    # try:
    final_state = asyncio.run(
        run_json_pipeline_with_stream(attachments, pipeline)
    )
    # except TypeError:
    #     final_state = asyncio.run(
    #         run_json_pipeline_with_stream(s3_uris, pipeline)
    #     )
    # except Exception as e:
    #     return {"statusCode": 500, "body": json.dumps({"error": f"Pipeline failed: {str(e)}"})}

    # 5) Persist the PDF
    pdf_bytes = (final_state or {}).get("pdf_summary")
    if not pdf_bytes:
        return {"statusCode": 500, "body": json.dumps({"error": "Pipeline returned no 'pdf_summary' bytes."})}

    out_key = _unique_result_key(job_id)
    try:
        s3.put_object(
            Bucket=RESULTS_BUCKET,
            Key=out_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": f"Failed to write PDF to S3: {str(e)}"})}

    # 6) (Optional) clean up job file after success
    if job_bucket and job_key:
        try:
            s3.delete_object(Bucket=job_bucket, Key=job_key)
        except Exception:
            # Non-fatal if cleanup fails
            pass

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "OK",
            "result_bucket": RESULTS_BUCKET,
            "result_key": out_key,
            "job_id": job_id,
        })
    }
