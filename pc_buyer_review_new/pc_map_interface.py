
## WITH PDF PARSING:

import boto3
from botocore.exceptions import ClientError
import streamlit as st
import re
from PyPDF2 import PdfReader
import io
import pandas as pd
import vectorSearch

def _sanitize_doc_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9\-\(\)\[\]\s]", "_", name)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned or "Document"

def parse_pdf_form_fields(file_bytes) -> dict:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        fields = reader.get_fields()
        if not fields:
            return {}
        st.write("Fields successfully parsed.")
        return {name: field.get("/V") for name, field in fields.items()}
    except Exception as e:
        return {"error": str(e)}

def generate_message(bedrock_client, model_id, input_text, input_files):
    content_blocks = [{"text": input_text}]

    for f in input_files:
        doc_format = f.name.split(".")[-1]
        doc_bytes  = f.read()
        doc_name   = _sanitize_doc_name(f.name)

        # Add parsed form fields if available
        parsed_fields = parse_pdf_form_fields(doc_bytes)
        if parsed_fields:
            parsed_output = f"{doc_name} form parsed output, use this for information about the interactive form: {parsed_fields}"
            input_text += "\n\n" + parsed_output

        content_blocks.append({
            "document": {
                "name": doc_name,
                "format": doc_format,
                "source": {"bytes": doc_bytes}
            }
        })

    message  = {"role": "user", "content": content_blocks}
    messages = [message]

    return bedrock_client.converse(modelId=model_id, messages=messages)

def main():
    model_id   = "anthropic.claude-3-5-haiku-20241022-v1:0"
    base_prompt = (
        """The contents of these documents describe the quotes and service details"
        of a particular requested good or service. Deduce the purchasing category
        of the requested good or service. Here are purchasing categories you can
        choose from:
        
        {'Facility Tools under 5K', 'Public Transit', 'Kitchen Equipment under 5K', 'Marine/Ship Equipment under 5K', 'Other IT Hardware under 5K', 'Printer/Copier Rental', 'Installation - Non-Taxable', 'Vehicle Lease', 'Fire Alarm/Fire Equipment Supplies', 'Hazardous Waste Disposal', 'IT Peripherals/Accessories under 5K', 'Facility Equipment over 5K (Inventorial)', 'Lab Equipment under 5K', 'Parking/Transportation Supplies', 'Construction Materials', 'Automotive Fuel', 'Network Hardware under 5K', 'Other IT Hardware over 5K (Inventorial)', 'Packaging Materials', 'Facility Equipment Maintenance/Repair Service', 'Pool/Spa Supplies', 'Vehicle Purchase over 5K (Inventorial)', 'Lab Animals Supplies', 'HVAC/Refrigeration Supplies under 5K', 'DNA/RNA/Oligos/Antibodies', 'Services - Advisory', 'Vehicle Maintenance And Repair Services', 'Telecom Audio Visual Equip over 5K (Inventorial)', 'Locks and Security Equipment under 5K', 'Furniture under 5K', 'Services - Translation/Interpreter', 'Lab Animals', 'Landscape Maintenance Supplies', 'Kitchen Equipment over 5K (Inventorial)', 'Printed/Copied Materials', 'Parking/Valet Services', 'Utilities - Cable TV', 'Chartered Vessel', 'Carpet and Flooring Supplies', 'Food/Beverage', 'Desktop/Laptop/Workstations over 5K (Inventorial)', 'Lab Animals Services', 'Telecom Voice Equipment under 5K', 'Recharge - UCSD Fleet Services Vehicle Rentals', 'Fire Alarm Equip/Fire Equip over 5K (Inventorial)', 'Facility Tools over 5K (Inventorial)', 'Painting and Decorating Supplies', 'Lab Testing Kits/Assays', 'IT Technical Services', 'Lab Equipment Capital Lease', 'DNA/RNA/Oligo Sequencing Services', 'Facility Equipment under 5K', 'Telecom Contractor Provided Materials', 'Telecom Voice Equipment over 5K (Inventorial)', 'Services - Marketing', 'Facility Electrical Services', 'Cloud Computing Services', 'Utilities - Water/Sewage', 'Security Services', 'Office Supplies', 'Services - Moving/Relocation', 'Vehicle Repair Parts/Materials', 'Shipping', 'Books', 'Installation - Taxable', 'Marine/Ship Services', 'Marine/Ship Repair', 'Software - Download', 'Material Handling Equipment over 5K (Inventorial)', 'Rideshare/Limo/Taxi Services', 'Construction Labor', 'Promotional Items/Merchandise', 'Fire Alarm Equipment/Fire Equipment under 5K', 'Services - Medical Coding/Billing', 'Servers under 5K', 'Facility Equipment Lease/Rental', 'Marine/Ship Equipment over 5K (Inventorial)', 'Office Equipment over 5K (Inventorial)', 'Firearms/Ammunition under 5K', 'Recharge - UCSD Transportation Parking Permits', 'Facility Electrical Supplies', 'IT Peripherals/Accessories over 5K (Inventorial)', 'Services - Financial', 'Facility Signage', 'Vehicle Rental', 'Services - Engineering/Design', 'Other Voice/Data', 'Services - Humanitarian', 'Lab Equipment Maintenance/Repair Parts', 'HVAC/Refrigeration Equipment over 5K (Inventorial)', 'Carpet and Flooring Services', 'Events Services (Nontaxable)', 'Services - Temporary Employment', 'Locks and Security System Maintenance Services', 'Services - Instructional/Training/Development', 'Medical/Surgical Supplies', 'Services - Editorial & Publication Support', 'Laundry/Uniform/Linen Supplies', 'Laundry/Uniform/Linen Services \n(this one may have been discontinued)', 'Furniture over 5K (Inventorial)', 'Vehicle Purchase under 5K', 'Services - Audit', 'Local/Long Distance Telephone', 'Facility Testing/Diagnostic Services', 'Clinical Trials Supplies', 'Events Services (Taxable)', 'Servers over 5K (Inventorial)', 'Mail/Postage/Messenger', 'Storage Hardware under 5K', 'Network Hardware over 5K (Inventorial)', 'Services - Field Research', 'Printer/Copier Maintenance', 'Lab Supplies', 'Firearms/Ammunition over 5K (Inventorial)', 'IT Programming Services', 'Elevator Maintenance Services', 'HVAC/Refrigeration Supplies over 5K (Inventorial)', 'Handling', 'Non-Hazardous Waste Disposal', 'Office Equipment under 5K', 'Services - Advertising/Public Relations/Promotions', 'Facility Repair Parts and Materials', 'Locks and Security Equip over 5K (Inventorial)', 'Utilities - Electricity', 'Services - Recruiting', 'Fire Alarm/Equipment Maintenance Services', 'Kitchen Supplies over 5K (Inventorial)', 'Plumbing Supplies', 'Lab Equipment over 5K (Inventorial)', 'Services - Clinical', 'Other Building Repair/Maintenance', 'Security Services - Crowd Control', 'IT/Telecom Hardware Maintenance or Support', 'Personal Protective Equipment Supplies', 'Services - Media/Digital', 'Sports/Fitness/Rec Equip over 5K (Inventorial)', 'Data Circuits/Internet', 'Pest Control Services', 'Drugs/Pharmaceutical Products', 'HVAC Equipment Maintenance Services', 'Facility Chemicals and Lubricants', 'Clinical Trial Digital Gift Cards', 'Lab Gases', 'Recharge - UCSD STORE Water Cooler Rental', 'Software - SaaS/Cloud', 'Lab Equipment Maintenance/Repair Services', 'Services - Legal', 'Facility Electrical Equipment', 'Trade Shows/Exhibits', 'Services - Transcription', 'Lab Testing/Diagnostic Services', 'Lab Equipment Rental/Operating Lease', 'Storage Hardware over 5K (Inventorial)', 'Clinical Trials Services', 'Landscape Maintenance Services', 'Janitorial Supplies', 'Chartered Bus/Rail', 'Marine/Ship Supplies', 'Telecom Audio Visual Equipment under 5K', 'Pool/Spa Maintenance', 'HVAC/Refrigeration Equipment under 5K', 'Uniform/Linen Rental Services', 'Janitorial Equipment over 5K (Inventorial)', 'Laundry Services - University Property', 'Lab Chemicals/Reagents', 'Desktop/Laptop/Workstations under 5K', 'Cell Phone Services', 'Janitorial Equipment under 5K', 'Kitchen Supplies under 5K', 'Plumbing Services', 'Marine/Ship Fuel', 'Janitorial Services', 'Kitchen Equipment Maintenance', 'Services - Medical', 'Material Handling Equipment under 5K', 'Services - Real Estate', 'Sports/Fitness/Recreation Equipment under 5K', 'Document Storage/Shredding', 'Controlled Substances/Narcotics'}
        based on the content within the attached documents, select ONE purchasing category that the service
        lines up best with, and say the purchasing category in this exact format:
        {{SELECTED_PURCHASING_CATEGORY_HERE}}
        Then, give your reasoning for deciding this with evidence that goes
        back to the original document.
        """
    )

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
                response = generate_message(
                    bedrock_client, model_id, base_prompt, uploaded_files
                )
            output_message = response["output"]["message"]
            fullText = ""
            for block in output_message["content"]:
                if "text" in block:
                    fullText += block["text"]
            
            llm_pc = re.findall(r"\{\{(.*?)\}\}", fullText)


            df = pd.read_csv("/home/ec2-user/ucsd/pc_buyer_review_new/PC_Buyer_Assignments - Copy(Buyer Review).csv")

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
                    res = vectorSearch.vector_search(searchString)
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
