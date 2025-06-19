import boto3
import csv
import json


def load_texts_for_embedding(csv_path: str) -> list[str]:
    to_embed = []
    with open(csv_path, "r", encoding="windows-1252") as f:
        reader = csv.DictReader(f)
        for row in reader:
            to_embed.append(
                f"{row['Purchasing Category']} | {row['Blink Description']}")
    return to_embed


def embed_texts_to_jsonl(texts: list[str], output_path: str, model_id: str = "amazon.titan-embed-text-v2:0", region: str = "us-west-2"):
    client = boto3.client("bedrock-runtime", region_name=region)
    with open(output_path, "w") as out:
        for item in texts:
            request = json.dumps({"inputText": item})
            response = client.invoke_model(modelId=model_id, body=request)
            model_response = json.loads(response["body"].read())
            embedding = model_response["embedding"]
            out.write(json.dumps({json.dumps(embedding): item}) + "\n")
