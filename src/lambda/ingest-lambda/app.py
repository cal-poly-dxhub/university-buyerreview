import os
import json
import uuid
import time
import base64
import boto3

s3 = boto3.client("s3")
REQUESTS_BUCKET = os.environ["REQUESTS_BUCKET"]
REQUESTS_PREFIX = os.environ.get("REQUESTS_PREFIX", "jobs/")

def _parse_body(event):
    body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")
    return json.loads(body)

def handler(event, context):
    try:
        payload = _parse_body(event)
        s3_uris = payload.get("s3_uris", [])
        metadata = payload.get("metadata", {})

        if not isinstance(s3_uris, list) or not s3_uris:
            return {"statusCode": 400, "body": json.dumps({"error": "Provide s3_uris: []"})}

        job_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
        key = f"{REQUESTS_PREFIX}{job_id}.json"

        job = {"job_id": job_id, "s3_uris": s3_uris, "metadata": metadata}
        s3.put_object(
            Bucket=REQUESTS_BUCKET,
            Key=key,
            Body=json.dumps(job).encode("utf-8"),
            ContentType="application/json",
        )

        # Immediately return; the processor will be invoked by the S3 event
        return {
            "statusCode": 202,
            "body": json.dumps({
                "message": "Accepted",
                "job_id": job_id,
                "request_bucket": REQUESTS_BUCKET,
                "request_key": key
            })
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
