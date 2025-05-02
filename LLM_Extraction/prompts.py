data_validation_prompt = """Data Validation Prompt
Your task is to validate the consistency of information in a Purchase Order (PO) document against other related documents like invoices, quotes, SOWs, or SSPRs.

Output Format
Provide your response as pure JSON.
If no PO document is present in the provided documents, respond with: {{"status": "No PO document to be validated"}}
If a PO is present, validate properties from the PO against other documents.
Only include properties that appear in both the PO and at least one other document.
For each property, indicate whether values match across documents with one of these values only: "Yes", "No", or "Mostly Yes".
Examine Supplier Address and Delivery Address thoroughly, as they are critical for compliance.

JSON Structure
For cases with no PO document:
{{
"status": "No PO document to be validated"
}}

For cases with a PO document:
{{
"Property 1": {{
"match": "Yes|No|Mostly Yes",
"PO": "Value from PO",
"Source 1": "Value 1",
"Source 2": "Value 2"
}},
"Property 2": {{
"match": "Yes|No|Mostly Yes",
"PO": "Value from PO",
"Source 1": "Value 1"
}}
}}

Rules
The PO document is the primary reference document - all validations must include the PO value.
If a property isn't mentioned in a document, don't include that document as a source.
Only validate data that is explicitly mentioned.
Omit any property that only appears in the PO but not in any other document.
The "match" value must be one of: "Yes", "No", or "Mostly Yes".
Focus on verifying that information in the PO is correct and aligned with other documents, not vice versa.

Documents:
{doc_text}
"""

PO_prompt = """Extract the following information from the purchase order document:
PO Number
Supplier Name
Supplier Address
Purchase Order Date
Payment Terms
Delivery Address
Line Item Description
Total Amount
Contact Person for Order Confirmation
Present the extracted information in a structured format with clear labels for each field."""

sspr_prompt = """SSPR Document Analysis Prompt
Task
Analyze the provided documents to check for an SSPR (Source Selection & Price Reasonableness) and extract specific information.

Output Format
Return your response in a structured JSON format with the following fields:

```json
{
  "SSPR Found": "Yes/No",
  "Funding Source": "Federal Funds/Non-Federal Funds",
  "Dollar Amount": "$X",
  "Desired Supplier": "Company Name",
  "Source Selection": {
    "Funding Source": "",
    "Type": ""
  },
  "Sections Always Required": [
    "I - SOURCE SELECTION",
    "VII - CONFLICT OF INTEREST STATEMENT",
    "VIII - REPRESENTATION"
  ],
  "Sections Required for this Type": [
    "List additional required sections based on the selected funding source and type"
  ],
  "Section Details": [
    {
      "Section Number": "I",
      "Section Name": "SOURCE SELECTION (I)",
      "Is Complete": true/false,
      "Fields": [
        {
          "Field Name": "Field Label",
          "Field Value": "Extracted Value"
        }
      ]
    }
  ]
}
```

Analysis Rules

Always Required Sections
Sections I, VII, and VIII are always required regardless of funding source or type.

Additional Required Sections by Funding Type
Based on which checkbox is selected in Section I:

1. **Federal Funds**:
   - New or Existing Formal Competitive Bid/Contract#: No additional sections
   - Competitive Proposals of < $100K: Section II
   - Sole Source: Sections III, IV
   - Certified Small Business (Only <$250K): Section III

2. **Non-Federal Funds**:
   - New or Existing Formal Competitive Bid/Contract#: No additional sections
   - Certified Small Business or DVBE (Only <$250K): Section III
   - Sole Source: Sections III, IV
   - Professional/Personal Services: Sections III, V
   - Unusual & Compelling Urgency: Section VI

Section Information
For each required section, indicate:
- Section Number and Name (formatted with proper title case)
- Whether it's complete (true/false)
- List of fields with their corresponding values (with proper labels)

# YOU HAVE TO INCLUDE Always Required Sections & Additional Required Sections by Funding Type
⚠️ **IMPORTANT**: Return only valid JSON. Do NOT include any explanation or notes before or after the JSON. No markdown. No commentary.
"""

invoice_prompt = """Extract the following key information from the invoice or quotes document:
Invoice Number
Invoice Date
Due Date
Total Amount Due
Payment Terms
Vendor/Company Name
Vendor Address
Bill To Information
Line Item Details (dates, descriptions, quantities, rates, amounts)
Any reference numbers
Present the extracted information in an organized format with appropriate sections and clear labels."""

sow_prompt = """Extract the following key information from this Statement of Work document:
SOW ID/Number (if available)
Current Term Start Date
Current Term End Date
Total Contract Duration/Period (if different from current term)
Client/University Name
Vendor/Supplier/Contractor Name
Project Scope/Services Description (brief summary)
Deliverables (if specified)
Total Cost/Budget (both for current term and total if specified)
Payment Terms and Schedule
Project Manager/Lead contacts for both parties
Location of Services
If any information isn't explicitly stated in the document, indicate 'Not specified' for that field. Present the extracted information in a clear, structured format with labeled fields."""

general_doc_prompt = f"""
You are an AI assistant tasked with extracting structured information from a variety of procurement and vendor-related documents.

Here are examples of the types of documents and what should be extracted:

---
SSPR:
{sspr_prompt}
---
Invoice:
{invoice_prompt}
---
Statement of Work (SOW):
{sow_prompt}
---
Purchase Order (PO):
{PO_prompt}
---

For each uploaded document, return a structured JSON object with the document name as the key. Each document entry should contain:
- A guessed Document Type
- A brief Summary of its purpose
- Key Fields extracted (as a dictionary)

⚠️ IMPORTANT: Return a single JSON object with each document name as a key. Do NOT include explanations or commentary outside the JSON.
"""

checklist_prompt = """
You are a compliance assistant. Based on the following extracted document content, evaluate the checklist items and respond in strict JSON format.

Document content:
{doc_text}

Checklist items:

1. **Funding Source**:
   - Is the funding source Federal or Non-Federal?
   - Identify and confirm which one it is based on the document.

2. **Price Reasonableness / SSPR**:
   - Is there documentation of price reasonableness?
   - Look for an SSPR (Source Selection & Price Reasonableness) form or similar justification.

3. **Competitive Bidding (threshold dependent)**:
   - If the total value is less than $100,000, mark this check as automatically passed.
   - If the value is $100,000 or above, check whether competitive bidding was done or a valid exception is documented.

4. **Contract Duration**:
   - If the purchase is for services, check whether the contract exceeds 10 years.
   - If the purchase is for goods, it is considered a one-time purchase and this check automatically passes.

5. **Conflict of Interest**:
   - Has the end user determined that the service provider should not be classified as a UC employee?
   - If no conflict of interest is found or it’s documented clearly, this should pass.

6. **Data Security / Appendix DS**:
   - If the purchase is for software or involves handling UC data, check if Appendix Data Security has been considered or signed.
   - If it's goods or services that clearly don't involve sharing data, this check passes automatically.

Return your answer as a JSON list of objects, each like:
{{
  "check": "...",
  "status": "✅ Passed / ❌ Missing / 🟡 Exception / ❓ Uncertain",
  "note": "...brief justification based on evidence..."
}}
"""

checklist_and_validation_prompt = """You are a procurement and compliance assistant. Your task is to validate Purchase Order (PO) documents against related documents and evaluate compliance requirements. Based on the provided documents, perform TWO distinct analyses:

PART 1: DATA VALIDATION
Validate the consistency of information in a Purchase Order (PO) document against other related documents like invoices, quotes, SOWs, or SSPRs.

Output Format for Part 1:
Provide your response as pure JSON.
- If no PO document is present, respond with: {{"status": "No PO document to be validated"}}
- If a PO is present, validate properties from the PO against other documents.
- Only include properties that appear in both the PO and at least one other document.
- For each property, indicate whether values match across documents with one of these values only: "Yes", "No", or "Mostly Yes".
- Examine Supplier Address and Delivery Address thoroughly, as they are critical for compliance.

JSON Structure for Part 1:
For cases with no PO document:
{{
  "status": "No PO document to be validated"
}}

For cases with a PO document:
{{
  "Property 1": {{
    "match": "Yes|No|Mostly Yes",
    "PO": "Value from PO",
    "Source 1": "Value 1",
    "Source 2": "Value 2"
  }},
  "Property 2": {{
    "match": "Yes|No|Mostly Yes",
    "PO": "Value from PO",
    "Source 1": "Value 1"
  }}
}}

Rules for Part 1:
- The PO document is the primary reference document - all validations must include the PO value.
- If a property isn't mentioned in a document, don't include that document as a source.
- Only validate data that is explicitly mentioned.
- Omit any property that only appears in the PO but not in any other document.
- The "match" value must be one of: "Yes", "No", or "Mostly Yes".
- Focus on verifying that information in the PO is correct and aligned with other documents, not vice versa.

PART 2: COMPLIANCE CHECKLIST
Based on the document content, evaluate the following compliance checklist items.

Output Format for Part 2:
Return your answer as a JSON list of objects, each like:
{{
  "check": "...",
  "status": "✅ Passed / ❌ Missing / 🟡 Exception / ❓ Uncertain",
  "note": "...brief justification based on evidence..."
}}

Checklist items:
1. **Funding Source**:
   - Is the funding source Federal or Non-Federal?
   - Identify and confirm which one it is based on the document.

2. **Price Reasonableness / SSPR**:
   - Is there documentation of price reasonableness?
   - Look for an SSPR (Source Selection & Price Reasonableness) form or similar justification.

3. **Competitive Bidding (threshold dependent)**:
   - If the total value is less than $100,000, mark this check as automatically passed.
   - If the value is $100,000 or above, check whether competitive bidding was done or a valid exception is documented.

4. **Contract Duration**:
   - If the purchase is for services, check whether the contract exceeds 10 years.
   - If the purchase is for goods, it is considered a one-time purchase and this check automatically passes.

5. **Conflict of Interest**:
   - Has the end user determined that the service provider should not be classified as a UC employee?
   - If no conflict of interest is found or it's documented clearly, this should pass.

6. **Data Security / Appendix DS**:
   - If the purchase is for software or involves handling UC data, check if Appendix Data Security has been considered or signed.
   - If it's goods or services that clearly don't involve sharing data, this check passes automatically.

FINAL OUTPUT:
Provide your response as a structured JSON with two main sections:
{{
  "data_validation": {{
    // Part 1 results here
  }},
  "compliance_checklist": [
    // Part 2 results here as an array
  ]
}}

Documents:
{doc_text}
"""