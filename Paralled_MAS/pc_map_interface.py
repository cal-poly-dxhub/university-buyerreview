
## WITH PDF PARSING:

import boto3
from botocore.exceptions import ClientError
import streamlit as st
import re
import pandas as pd
from prompt_loader import TASK_PROMPT_REGISTRY
from utils import vector_search, build_pdf_based_message
from model_registry import ModelRegistry


def main():
    model_id   = ModelRegistry.haiku_3_5
    base_prompt = TASK_PROMPT_REGISTRY.get("PC_CATEGORY_CLASSIFICATION", "")

    st.title("UCSD Buyer: Find the Purchasing Category and map to the assigned Buyer")
    uploaded_files = st.file_uploader("Upload Relevant Files", accept_multiple_files=True)

    if st.button("Done uploading files"):
        st.divider()

        if not uploaded_files:
            st.warning("No files uploaded.")
            return

        try:
            bedrock_client = boto3.client(service_name="bedrock-runtime")

            with st.spinner("Processing all documents in one call…"):
                response = build_pdf_based_message(
                    bedrock_client, model_id, base_prompt, uploaded_files
                )
            output_message = response["output"]["message"]
            fullText = ""
            for block in output_message["content"]:
                if "text" in block:
                    fullText += block["text"]
            
            llm_pc = re.findall(r"\{\{(.*?)\}\}", fullText)


            df = pd.read_csv("Data/PC_Buyer_Assignments - Copy(Buyer Review).csv")

            column_to_search = "Purchasing Category"

            # Filter rows where column matches any extracted field (exact match)
            matched_df = df[df[column_to_search].astype(str).isin(llm_pc)]

            if not matched_df.empty:
                st.write("Matching rows:")
                st.dataframe(matched_df)
            else:
                st.write("No exact matches found, running vector similarity search...")
                if llm_pc:
                    searchString = llm_pc[0]
                    res = vector_search(searchString)
                    st.write("PC Vector Search Results: ")
                    for i, (text, distance) in enumerate(res, 1):
                        st.markdown(f"**{i}.** `{text}`  \nDistance: {distance:.4f}")
                    search_keys = [text.split('|')[0].strip() for text, _ in res]
                    secondary_matches = df[df[column_to_search].astype(str).isin(search_keys)]
                    if not secondary_matches.empty:
                        st.write("CSV rows matching vector search categories:")
                        st.dataframe(secondary_matches)
                    else:
                        st.write("No matches found in CSV for vector search categories.")


            st.divider()
            st.write(f"LLM Response: {fullText}")



            token_usage = response["usage"]
            st.caption(
                f"Tokens in: {token_usage['inputTokens']}, "
                f"out: {token_usage['outputTokens']}, "
                f"total: {token_usage['totalTokens']}. "
                f"Stop reason: {response['stopReason']}"
            )

        except ClientError as err:
            st.error(f"A client error occurred: {err.response['Error']['Message']}")
        else:
            print(f"Finished generating text with model {model_id}.")

if __name__ == "__main__":
    main()
