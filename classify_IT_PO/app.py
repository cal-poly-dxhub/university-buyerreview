from datetime import datetime
import streamlit as st
import json
from bedrock_utils import (
    extract_text_with_form_fields,
    make_prompt,
    invoke_until_completion,
    try_parse_json_like
)

def full_model_invocation(doc):
    """Processes a document through the LLM for classification analysis."""
    contents = extract_text_with_form_fields(doc)
    
    pre_prompt = "Human: You are a document classification specialist for the University of California. Your task is to analyze a Purchase Order (PO) document and its attachments, and determine the appropriate Protection Level (P1-P4) and Availability Level (A1-A4) according to the UC Institutional Information and IT Resource Classification Standard."
    post_prompt = """Assistant: I will provide you with:

The complete text of a Purchase Order document and any attachments
The UC Institutional Information and IT Resource Classification Standard
Please analyze all provided documents carefully, focusing on:

The types of information contained in the PO (financial data, vendor information, personal information, etc.)
The sensitivity of this information and potential harm if compromised
The importance of this information to business operations
Any regulatory or compliance requirements that may apply
The need for confidentiality, integrity, and availability
Apply the following classification guidelines from the UC Institutional Information and IT Resource Classification Standard:

Protection Levels:

P4 (High): Information whose unauthorized disclosure could result in significant fines, penalties, regulatory action, or civil/criminal violations; could cause significant harm to UC stakeholders; or could impact essential services
P3 (Moderate): Information whose unauthorized disclosure could result in small to moderate fines or penalties; could cause moderate damage to UC or its stakeholders; or could have moderate impact on privacy
P2 (Low): Information not specifically protected by statute but not intended for public use; unauthorized disclosure could result in minor damage or small financial loss
P1 (Minimal): Public information where integrity is the primary concern
Availability Levels:

A4 (High): Loss of availability would result in major impairment to overall operations, essential services, or significant financial losses
A3 (Moderate): Loss of availability would result in moderate financial losses and/or reduced customer service
A2 (Low): Loss of availability may cause minor losses or inefficiencies
A1 (Minimal): Loss of availability poses minimal impact or financial loss
Then provide your analysis as a JSON object with the following structure:

{ "classification": { "protection_level": { "code": "P1/P2/P3/P4", "description": "Minimal/Low/Moderate/High", "protection_reasoning": "explanation for protection level assignment" }, "availability_level": { "code": "A1/A2/A3/A4", "description": "Minimal/Low/Moderate/High", "availability_reasoning": "explanation for availability level assignment" } }, "sensitive_information": [ { "type": "information type (e.g., PII, financial, etc.)", "description": "specific details found", "concern": "potential harm if compromised" } ], "regulatory_concerns": "description of applicable regulations if any", "handling_recommendations": [ "recommendation 1", "recommendation 2" ], "special_considerations": "any ambiguities or additional notes worth mentioning" }"""

    prompt = make_prompt(pre_prompt + post_prompt, contents)
    response = invoke_until_completion(prompt)
    return response

def display_classification_results(data):
    """Displays the classification results in a structured format."""
    st.header("📊 Classification Analysis")
    
    # Classification Section
    st.subheader("Classification Summary")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Protection Level")
        st.metric(
            label=f"{data['classification']['protection_level']['code']}",
            value=f"{data['classification']['protection_level']['description']}"
        )
        st.info(data['classification']['protection_level']['protection_reasoning'])
        
    with col2:
        st.markdown("##### Availability Level")
        st.metric(
            label=f"{data['classification']['availability_level']['code']}",
            value=f"{data['classification']['availability_level']['description']}"
        )
        st.info(data['classification']['availability_level']['availability_reasoning'])
    
    # Sensitive Information Section
    st.subheader("Sensitive Information Identified")
    if len(data['sensitive_information']) > 0:
        for i, info in enumerate(data['sensitive_information']):
            with st.expander(f"{info['type']}", expanded=True if i == 0 else False):
                st.write(f"**Description:** {info['description']}")
                st.write(f"**Concern:** {info['concern']}")
    else:
        st.write("No sensitive information identified.")
    
    # Regulatory Concerns
    st.subheader("Regulatory Concerns")
    st.write(data['regulatory_concerns'] if data['regulatory_concerns'] else "No regulatory concerns identified.")
    
    # Handling Recommendations
    st.subheader("Handling Recommendations")
    for i, rec in enumerate(data['handling_recommendations']):
        st.write(f"{i+1}. {rec}")
    
    # Special Considerations
    if data['special_considerations']:
        st.subheader("Special Considerations")
        st.warning(data['special_considerations'])

# Streamlit UI
st.set_page_config(page_title="Document Analyzer", layout="wide")
st.title("📄 Document Classification Analyzer")

uploaded_file = st.file_uploader("Upload your document", type=["pdf", "docx", "txt"])

if uploaded_file is not None:
    st.success(f"Uploaded: {uploaded_file.name}")

    with st.spinner("Processing document and analyzing classification..."):
        result = try_parse_json_like(full_model_invocation(uploaded_file))
        
        try:
            classification_data = result if isinstance(result, dict) else json.loads(result)
            display_classification_results(classification_data)
            
            # Download option
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Document_Classification_{timestamp}.json"
            st.download_button(
                label="⬇️ Download Full Analysis (JSON)",
                data=json.dumps(classification_data, indent=2),
                file_name=filename,
                mime="application/json"
            )
            
        except json.JSONDecodeError:
            st.subheader("📃 Analysis Output")
            st.text_area("Raw Output", result, height=300)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"LLM_Output_{timestamp}.txt"
            st.download_button(
                label="⬇️ Download Output as .txt",
                data=result,
                file_name=filename,
                mime="text/plain"
            )