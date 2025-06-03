import boto3
import csv
import json
import time


toBeEmbedded = []

with open("/home/ec2-user/ucsd/pc_buyer_review_new/PC_Buyer_Assignments - Copy(Buyer Review).csv","r", encoding='windows-1252') as f:
    csvDictReader = csv.DictReader(f)

    for row in csvDictReader:
        cur = f"{row['Purchasing Category']} | {row['Blink Description']}"
        toBeEmbedded.append(cur)




client =  boto3.client("bedrock-runtime",region_name="us-west-2")
model_id = "amazon.titan-embed-text-v2:0"


with open("embeddings.jsonl","w") as out:
    for item in toBeEmbedded:
        native_request = {"inputText":item}
        request = json.dumps(native_request)
        response = client.invoke_model(modelId=model_id,body=request)
        modelResponse = json.loads(response["body"].read())
        embedding = modelResponse["embedding"]
        out.write(json.dumps({json.dumps(embedding):item})+"\n")