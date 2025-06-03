import json
import numpy as np
import faiss
import boto3

# Load embeddings from JSONL
def load_embeddings(jsonl_path):
    vectors = []
    texts = []
    with open(jsonl_path, 'r') as f:
        for line in f:
            obj = json.loads(line)
            for vec_str, text in obj.items():
                vector = json.loads(vec_str)  # parse the stringified list
                vectors.append(vector)
                texts.append(text)
    return np.array(vectors).astype('float32'), texts

# Build FAISS index
def build_faiss_index(vectors):
    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)
    return index

# Search FAISS index
def search_faiss(index, query_vector, k=5):
    query_vector = np.array([query_vector]).astype('float32')
    D, I = index.search(query_vector, k)
    return D, I


# Embed the input string using your model (e.g., Titan, OpenAI, etc.)
def embed_input(input_string,c,model_id):
    native_request = {"inputText":input_string}
    request = json.dumps(native_request)
    response = c.invoke_model(modelId=model_id,body=request)
    modelResponse = json.loads(response["body"].read())
    embedding = modelResponse["embedding"]
    return embedding



def vector_search(inputString):
    jsonl_path = 'embeddings.jsonl'
    vectors, texts = load_embeddings(jsonl_path)
    index = build_faiss_index(vectors)
    client2 =  boto3.client("bedrock-runtime",region_name="us-west-2")
    model_id = "amazon.titan-embed-text-v2:0"
    query_vector = embed_input(inputString,client2,model_id)  
    D, I = search_faiss(index, query_vector, k=5)
    results = [(texts[idx], D[0][rank]) for rank, idx in enumerate(I[0])]
    return results

# # Show results
# for rank, idx in enumerate(I[0]):
#     print(f"{rank+1}: {texts[idx]} (Distance: {D[0][rank]})")


