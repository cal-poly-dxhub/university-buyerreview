from botocore.exceptions import ClientError
import streamlit as st
import asyncio
from Graphs.phi_agreement import build_phi_agreement_graph
from state import PipelineState


def main():
    st.title("UCSD Buyer: Check if the PHI Agreement needs to be signed")
    uploaded_files = st.file_uploader(
        "Upload Relevant Files", accept_multiple_files=True, type="pdf")

    if st.button("Done uploading files"):
        st.divider()

        if not uploaded_files:
            st.warning("No files uploaded.")
            return

        try:
            with st.spinner("Processing all documents in one call…"):
                pipeline = build_phi_agreement_graph()
                initial_state: PipelineState = {
                    "uploaded_files": uploaded_files}
                final_output = asyncio.run(pipeline.ainvoke(initial_state))
            full_text = final_output["phi_agreement"]["full_text"]
            st.write("Model response:")
            st.write(full_text)
            token_usage = final_output["phi_agreement"]["usage"]
            st.caption(
                f"Tokens in: {token_usage['inputTokens']}, "
                f"out: {token_usage['outputTokens']}, "
                f"total: {token_usage['totalTokens']}. "
                f"Stop reason: {final_output['phi_agreement']['stop_reason']}"
            )
            st.json(final_output)

        except ClientError as err:
            st.error(
                f"A client error occurred: {err.response['Error']['Message']}")


if __name__ == "__main__":
    main()
