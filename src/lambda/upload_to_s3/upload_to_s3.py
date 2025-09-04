# Single file Upload handler code

# import json, base64, boto3, string, random, os
# s3 = boto3.client("s3")
# BUCKET = "dxhub-buyer-review"

# def lambda_handler(event, context):
#     # API GW REST + binary = base64 in event["body"], with a flag
#     b64 = event.get("body") or ""
#     if event.get("isBase64Encoded", False):
#         data = base64.b64decode(b64)
#     else:
#         # Fallback (shouldn't happen for binary types)
#         data = b64.encode("utf-8")

#     key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)) + ".pdf"
#     s3.put_object(Bucket=BUCKET, Key=key, Body=data, ContentType="application/pdf")
#     return {"statusCode": 200, "body": json.dumps({"ok": True, "key": key})}

# Multi-part data

import json, base64, boto3, os, re, uuid
from requests_toolbelt.multipart import decoder

s3 = boto3.client("s3")
BUCKET = "077938161517-us-west-2-dxhub-ub-bkt"

def _get_header(headers, key):
    return (headers.get(key) or headers.get(key.lower()) or headers.get(key.title()))

def _ensure_boundary(content_type: str, raw: bytes) -> str:
    # If boundary missing, try to infer from body start: b"--<boundary>\r\n"
    if "multipart/form-data" in content_type and "boundary=" not in content_type:
        if raw.startswith(b"--"):
            first_line = raw.split(b"\r\n", 1)[0]  # b"--<boundary>"
            boundary = first_line[2:]  # strip leading "--"
            if boundary:
                return f'multipart/form-data; boundary={boundary.decode("utf-8", "ignore")}'
    return content_type

def lambda_handler(event, context):
    body_b64 = event.get("body") or ""
    raw = base64.b64decode(body_b64) if event.get("isBase64Encoded") else body_b64.encode("utf-8")
    headers = event.get("headers", {}) or {}
    content_type = _get_header(headers, "Content-Type") or "application/octet-stream"
    content_type = _ensure_boundary(content_type, raw)

    uploaded = []
    try:
        if content_type.startswith("multipart/form-data"):
            if "boundary=" not in content_type:
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"ok": False, "error": "Missing multipart boundary in Content-Type"})
                }

            mp = decoder.MultipartDecoder(raw, content_type)
            for part in mp.parts:
                disp = (part.headers.get(b"Content-Disposition") or b"").decode("utf-8", "ignore")
                m = re.search(r'filename="([^"]+)"', disp)
                if not m:
                    continue  # skip text fields
                filename = os.path.basename(m.group(1)) or "upload.bin"
                p_ct = (part.headers.get(b"Content-Type") or b"application/octet-stream").decode("utf-8", "ignore")
                key = f"{uuid.uuid4().hex}_{filename}"
                s3.put_object(Bucket=BUCKET, Key=key, Body=part.content, ContentType=p_ct)
                uploaded.append({"filename": filename, "key": key, "contentType": p_ct})
        else:
            key = f"{uuid.uuid4().hex}.bin"
            s3.put_object(Bucket=BUCKET, Key=key, Body=raw, ContentType=content_type)
            uploaded.append({"filename": key, "key": key, "contentType": content_type})
    except Exception as e:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": False, "error": f"multipart parse failed: {type(e).__name__}: {str(e)}"})
        }

    return {"statusCode": 200, "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": True, "files": uploaded})}
