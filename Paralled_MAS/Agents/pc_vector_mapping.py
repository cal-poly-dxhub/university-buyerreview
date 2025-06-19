import pandas as pd
from utils import vector_search
import os

CSV_PATH = os.path.join("Data", "PC_Buyer_Assignments - Copy(Buyer Review).csv")
COLUMN_TO_SEARCH = "Purchasing Category"

def pc_vector_mapping(llm_categories):
    df = pd.read_csv(CSV_PATH)

    matched_df = df[df[COLUMN_TO_SEARCH].astype(str).isin(llm_categories)]
    fallback_df = pd.DataFrame()
    vector_results = []

    if matched_df.empty and llm_categories:
        search_string = llm_categories[0]
        vector_results = vector_search(search_string)
        search_keys = [text.split('|')[0].strip() for text, _ in vector_results]
        fallback_df = df[df[COLUMN_TO_SEARCH].astype(str).isin(search_keys)]

    return {
        "matched_df": matched_df,
        "fallback_df": fallback_df,
        "vector_results": vector_results
    }
