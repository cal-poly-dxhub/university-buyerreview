import boto3
import json
import numpy as np
from opensearchpy import OpenSearch


# Initialize Bedrock runtime client
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

import sys
print("Running Python from:", sys.executable)

# Titan Embeddings model ID (as of 2024)
MODEL_ID = "amazon.titan-embed-text-v1"

def get_normalized_embedding(text):
    body = json.dumps({"inputText": text})
    response = bedrock.invoke_model(
        body=body,
        modelId=MODEL_ID,
        accept="application/json",
        contentType="application/json"
    )
    response_body = json.loads(response["body"].read())
    embedding = np.array(response_body["embedding"])
    return (embedding / np.linalg.norm(embedding)).tolist()

client = OpenSearch(
    hosts=[{"host": "search-service-map-ndxrw2lm2reeycx6ufvlouqaeq.us-west-2.es.amazonaws.com", "port": 443}],
    http_auth=("admuruge", "Bestbro1325!"),  # or use IAM
    use_ssl=True,
    verify_certs=True
)

def search_similar_description(query_text):
    embedding = get_normalized_embedding(query_text)
    
    response = client.search(
        index="services",
        body={
            "size": 1,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": embedding,
                        "k": 1
                    }
                }
            }
        }
    )

    hits = response["hits"]["hits"]
    if hits:
        return hits[0]["_source"]
    return None