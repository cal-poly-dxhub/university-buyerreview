# pc_classifier_app.py

import streamlit as st
from botocore.exceptions import ClientError
from Agents.pc_llm_mapping import pc_llm_mapping
from Agents.pc_vector_mapping import pc_vector_mapping

def main():
    st.title("UCSD Buyer: Purchasing Category Classification & Mapping")

    uploaded_files = st.file_uploader("Upload Relevant Files", accept_multiple_files=True, type="pdf")

    if st.button("Classify and Map"):
        st.divider()

        if not uploaded_files:
            st.warning("No files uploaded.")
            return

        try:
            with st.spinner("Running LLM Classification..."):
                pc_output = pc_llm_mapping(uploaded_files)

            llm_categories = pc_output["categories"]
            full_text = pc_output["full_text"]
            response = pc_output["response"]
            matched_df = pc_output["matched_df"]

            st.divider()
            st.write("**LLM Response:**")
            st.write(full_text)

            token_usage = response["usage"]
            st.caption(
                f"Tokens in: {token_usage['inputTokens']}, "
                f"out: {token_usage['outputTokens']}, "
                f"total: {token_usage['totalTokens']}. "
                f"Stop reason: {response['stopReason']}"
            )


            if not matched_df.empty:
                st.write("Matching rows:")
                st.dataframe(matched_df)
            else:
                st.write("No exact matches found, running vector similarity search...")
                if llm_categories:
                    with st.spinner("Matching with Buyer Assignments..."):
                        vector_output = pc_vector_mapping(llm_categories)

                    fallback_df = vector_output["fallback_df"]
                    vector_results = vector_output["vector_results"]

                    if not fallback_df.empty:
                        st.write("PC Vector Search Results:")
                        for i, (text, distance) in enumerate(vector_results, 1):
                            st.markdown(f"**{i}.** `{text}`  \nDistance: {distance:.4f}")
                        st.write("CSV rows matching vector search categories:")
                        st.dataframe(fallback_df)
                    else:
                        st.write("No matches found in CSV for vector search categories.")

            
        except ClientError as err:
            st.error(f"A client error occurred: {err.response['Error']['Message']}")

if __name__ == "__main__":
    main()
