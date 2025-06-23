import pandas as pd
from utils import vector_search
import os
import streamlit as st

CSV_PATH = os.path.join("Data", "PC_Buyer_Assignments - Copy(Buyer Review).csv")
COLUMN_TO_SEARCH = "Purchasing Category"

def pc_vector_mapping(llm_categories):
    df = pd.read_csv(CSV_PATH)

    fallback_df = pd.DataFrame()
    vector_results = []

    if llm_categories:
        search_string = llm_categories[0]
        vector_results = vector_search(search_string)
        search_keys = [text.split('|')[0].strip() for text, _ in vector_results]
        fallback_df = df[df[COLUMN_TO_SEARCH].astype(str).isin(search_keys)]

    return {
        "pc_mapping": {
            "matched_df": fallback_df,
            "vector_results": vector_results
        }
    }
