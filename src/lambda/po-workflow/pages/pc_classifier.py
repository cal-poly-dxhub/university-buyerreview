# pc_classifier_app.py

import streamlit as st
from botocore.exceptions import ClientError
# from Agents.pc_vector_mapping import pc_vector_mapping
import asyncio
from Graphs.pc_classifier_only import build_pc_category_graph
from state import PipelineState
import pandas as pd


def main():
    st.title("UCSD Buyer: Purchasing Category Classification & Mapping")

    uploaded_files = st.file_uploader("Upload Relevant Files", accept_multiple_files=True, type=["pdf", "png", "jpg", "jpeg", "docx", "txt", "xlsx"])

    if st.button("Classify and Map"):
        st.divider()

        if not uploaded_files:
            st.warning("No files uploaded.")
            return

        try:
            with st.spinner("Running LLM Classification..."):
                pipeline = build_pc_category_graph()
                initial_state: PipelineState = {
                    "uploaded_files": uploaded_files}
                final_output = asyncio.run(pipeline.ainvoke(initial_state))

            llm_categories = final_output["pc_mapping"]["categories"]
            full_text = final_output["pc_mapping"]["full_text"]
            matched_df = final_output["pc_mapping"]["matched_df"]

            st.write("**LLM Response:**")
            st.write(full_text)
            st.divider()

            token_usage = final_output["pc_mapping"]["usage"]
            st.caption(
                f"Tokens in: {token_usage['inputTokens']}, "
                f"out: {token_usage['outputTokens']}, "
                f"total: {token_usage['totalTokens']}. "
                f"Stop reason: {final_output['pc_mapping']['stop_reason']}"
            )


            if matched_df:
                st.write("Matching rows:")
                df = pd.DataFrame(matched_df)
                st.dataframe(df)
                st.json(final_output)
            # else:
            #     st.write("No exact matches found, running vector similarity search...")
            #     if llm_categories:
            #         with st.spinner("Matching with Buyer Assignments..."):
            #             vector_output = pc_vector_mapping(llm_categories)

            #         fallback_df = vector_output["pc_mapping"]["matched_df"]
            #         vector_results = vector_output["pc_mapping"]["vector_results"]

            #         if not fallback_df.empty:
            #             st.write("PC Vector Search Results:")
            #             for i, (text, distance) in enumerate(vector_results, 1):
            #                 st.markdown(f"**{i}.** `{text}`  \nDistance: {distance:.4f}")
            #             st.write("CSV rows matching vector search categories:")
            #             st.dataframe(fallback_df)
            #         else:
            #             st.write("No matches found in CSV for vector search categories.")

            
        except ClientError as err:
            st.error(f"A client error occurred: {err.response['Error']['Message']}")

if __name__ == "__main__":
    main()
