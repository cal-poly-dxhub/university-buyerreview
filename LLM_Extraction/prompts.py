data_validation_prompt = """Data Validation Prompt
Your task is to compare properties mentioned in multiple documents, including a PO file, and validate their consistency.
Output Format
Provide your response as pure JSON.
Only include properties that appear in at least two documents.
For each property, indicate whether values match across documents with one of these values only: "Yes", "No", or "Mostly Yes".
Only list documents as sources if they explicitly mention the property value.

JSON Structure
json{
  "Property 1": {
    "match": "Yes|No|Mostly Yes",
    "Source 1": "Value 1",
    "Source 2": "Value 2",
    "Source 3": "Value 3"
  },
  "Property 2": {
    "match": "Yes|No|Mostly Yes",
    "Source 1": "Value 1",
    "Source 2": "Value 2"
  }
}
Rules
If a property isn't mentioned in a document, don't include that document as a source.
Only validate data that is explicitly mentioned.
Omit any property that appears in only one document.
The "match" value must be one of: "Yes", "No", or "Mostly Yes".
Focus only on data about the company being contracted with, not other companies' proposals."""

PO_prompt = """Extract the following information from the purchase order document:
PO Number
Supplier Name
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
