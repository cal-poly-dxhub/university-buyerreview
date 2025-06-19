from botocore.exceptions import ClientError
import streamlit as st
from Agents.phi_agreement_checker import phi_agreement_checker
import asyncio

def main():
    st.title("UCSD Buyer: Check if the PHI Agreement needs to be signed")
    uploaded_files = st.file_uploader("Upload Relevant Files", accept_multiple_files=True, type="pdf")

    if st.button("Done uploading files"):
        st.divider()

        if not uploaded_files:
            st.warning("No files uploaded.")
            return

        try:
            with st.spinner("Processing all documents in one call…"):
                response = asyncio.run(phi_agreement_checker(uploaded_files))
            output_message = response["output"]["message"]
            st.write("Model response:")
            for block in output_message["content"]:
                if "text" in block:
                    st.write(block["text"])

            token_usage = response["usage"]
            st.caption(
                f"Tokens in: {token_usage['inputTokens']}, "
                f"out: {token_usage['outputTokens']}, "
                f"total: {token_usage['totalTokens']}. "
                f"Stop reason: {response['stopReason']}"
            )

        except ClientError as err:
            st.error(f"A client error occurred: {err.response['Error']['Message']}")

if __name__ == "__main__":
    main()