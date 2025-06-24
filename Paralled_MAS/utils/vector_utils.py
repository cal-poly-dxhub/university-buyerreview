# import json
# import numpy as np
# import faiss
# import boto3
# import os
# from model_registry import ModelRegistry

# JSONL_PATH = os.path.join("Data", "embeddings.jsonl")
# REGION = "us-west-2"
# # Load embeddings from JSONL
# def load_embeddings(jsonl_path):
#     vectors = []
#     texts = []
#     with open(jsonl_path, 'r') as f:
#         for line in f:
#             obj = json.loads(line)
#             for vec_str, text in obj.items():
#                 vector = json.loads(vec_str)  # parse the stringified list
#                 vectors.append(vector)
#                 texts.append(text)
#     return np.array(vectors).astype('float32'), texts

# # Build FAISS index
# def build_faiss_index(vectors):
#     dim = vectors.shape[1]
#     index = faiss.IndexFlatL2(dim)
#     index.add(vectors)
#     return index

# # Search FAISS index
# def search_faiss(index, query_vector, k=5):
#     query_vector = np.array([query_vector]).astype('float32')
#     D, I = index.search(query_vector, k)
#     return D, I


# # Embed the input string using your model (e.g., Titan, OpenAI, etc.)
# def embed_input(input_string,c,model_id):
#     native_request = {"inputText":input_string}
#     request = json.dumps(native_request)
#     response = c.invoke_model(modelId=model_id,body=request)
#     modelResponse = json.loads(response["body"].read())
#     embedding = modelResponse["embedding"]
#     return embedding



# def vector_search(inputString):
#     vectors, texts = load_embeddings(JSONL_PATH)
#     index = build_faiss_index(vectors)
#     client2 =  boto3.client("bedrock-runtime",region_name=REGION)
#     model_id = ModelRegistry.titan_2
#     query_vector = embed_input(inputString,client2,model_id)  
#     D, I = search_faiss(index, query_vector, k=5)
#     results = [(texts[idx], D[0][rank]) for rank, idx in enumerate(I[0])]
#     return results

# # # Show results
# # for rank, idx in enumerate(I[0]):
# #     print(f"{rank+1}: {texts[idx]} (Distance: {D[0][rank]})")