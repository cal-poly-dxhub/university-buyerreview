import boto3
import csv
import json
from model_registry import ModelRegistry

REGION = "us-west-2"
ENCODING_METHOD = "windows-1252"
PC_COLUMN = "Purchasing Category"
Blink_DESCRIPTION_COLUMN = "Blink Description"

def load_texts_for_embedding(csv_path: str) -> list[str]:
    to_embed = []
    with open(csv_path, "r", encoding=ENCODING_METHOD) as f:
        reader = csv.DictReader(f)
        for row in reader:
            to_embed.append(
                f"{row[PC_COLUMN]} | {row[Blink_DESCRIPTION_COLUMN]}")
    return to_embed


def embed_texts_to_jsonl(texts: list[str], output_path: str, model_id: str = ModelRegistry.titan_2, region: str = REGION):
    client = boto3.client("bedrock-runtime", region_name=region)
    with open(output_path, "w") as out:
        for item in texts:
            request = json.dumps({"inputText": item})
            response = client.invoke_model(modelId=model_id, body=request)
            model_response = json.loads(response["body"].read())
            embedding = model_response["embedding"]
            out.write(json.dumps({json.dumps(embedding): item}) + "\n")
