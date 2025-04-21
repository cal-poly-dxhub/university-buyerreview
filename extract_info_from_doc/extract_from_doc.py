import json
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from pypdf import PdfReader
import pdfplumber
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams



# local imports
# from laserfiche_utils import process_folder_recursively
from bedrock_utils import make_prompt, fits_token_limit
from parsing_utils import parse_document, extract_json_from_response, extract_json_to_text
# from s3_utils import store_json_document_s3_thread

# colored printing

SPEAKER_CARDS = "Speaker Cards"
FILE = "/Users/muru/Documents/AWS_DxHub/meeting_minutes/Statement of work examples/SOW Example #4.pdf"

def extract_text_with_form_fields(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    
    # Extract regular text
    for page in reader.pages:
        text += page.extract_text() + "\n"
    
    # Extract form fields
    if reader.get_fields():
        for field_name, field_value in reader.get_fields().items():
            if field_value:
                text += f"{field_name}: {field_value}\n"
    
    return text

def convert_to_json(template: dict, doc):
    """
    Determine correct S3 parameters for a given file.

    :param bucket_name: Name of the S3 you want to upload your file.
    :param s3_file_name: Name of the file you want to upload to S3.
    :param pages_of_content: List of pages from the document.
    :param document_id: Document id for the document.
    :param template: JSON template for parsing.
    :return: List containing the parsed document, bucket_name, s3_file_name and document_id.
    """

    # # Check for Speaker Cards
    # if SPEAKER_CARDS in s3_file_name:
    #     print("Skipping Speaker Cards")
    #     return []
    



    def extract_text_with_form_fields(pdf_path):
        reader = PdfReader(pdf_path)
        text = ""
        
        # Extract regular text
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        # Extract form fields
        if reader.get_fields():
            for field_name, field_value in reader.get_fields().items():
                if field_value:
                    text += f"{field_name}: {field_value}\n"
        
        return text
    
    contents = extract_text_with_form_fields(doc)

    # Create prompt 
    pre_prompt = "Human: You are an AI assistant adept at parsing documents and extracting key details with meticulous accuracy. Your sole purpose is to populate the provided JSON template completely and precisely, without injecting any of your own interpretations. Behave like an impartial information extraction machine."
    post_prompt = "For each relevant section in the document EXCLUDING DOCTYPE, fill out the corresponding field in the JSON structure. Leave no stone unturned - search thoroughly to identify and accurately record all pertinent details, regardless of how trivial. For each section in the JSON template, if no applicable value exists in the document, use 'null'. Do not remove any sections from the original template, all original fields should be present, mark them with null if not present in the document.Handle ambiguities by listing the most accurate extractions.If you discover additional attributes not matching the template, judiciously append them under 'Misc' only doing so if the attribute cannot be resolved to fit in the template, formatting new entries to maintain machine readability.When finished, return only the fully populated JSON object containing the extracted data from the document. Make sure this JSON object still contains all the original fields from the template even if they are marked as null. Do this multiple times to make sure you extract every relevant entity and relationship with a high level of confidence. Complete multiple epochs and estimate your confidence level [low, medium, high, very high]. Read out your results for each epoch and number each epoch. Place the final, high confidence results in the variable results for downstream ETL consumption and the final json object in <json></json> tags.Demonstrate your technical accuracy through the completeness, precision and formatting of the structured information you provide. It is of utmost importance you complete all key value pairs in the template json with a value; if there is no value found the value should be populated with a null value"

    prompt = [pre_prompt, post_prompt]

    # Check if prompt fits within our token limit
    full_length_prompt = make_prompt(prompt, template, contents)
    if fits_token_limit(full_length_prompt):
        # Parse document into JSON format
        response = parse_document(contents, template, prompt)
        if response:
            # Extract json from LLM response
            json_string_without_path = extract_json_from_response(response)
            
            if json_string_without_path:
                return json_string_without_path
            
            else:
                # JSON parsing failed
                print(f"Parsing failed for doc")
                # Log errored doc id
                with open("failed_documents.txt", "a") as errors:
                    errors.write(f" ")
                return []
        else:
            # No LLM response
            print(f"Empty response with document id: , document name: ")
            # Log errored doc id
            with open("failed_documents.txt", "a") as errors:
                errors.write(f"")
            return []
    else:
        # Document exceeded token limit
        print(f"Document with document_id: and document name: exceeds the token limit for this LLM")
        # Log errored doc id
        with open("failed_documents.txt", "a") as errors:
            errors.write(f" ")
        return []


# def run_threads(document_params: list):
#     """
#     Upload all documents to S3 in parallel.

#     :param document_params: The list of parameters for each document to be passed to the executor.
#     :return: None
#     """

#     # Constants
#     BUCKET_NAME = 0
#     S3_LOCATION = 1
#     PAGES_OF_CONTENT = 3
#     DOC_ID = 4
#     TEMPLATE = 5    

#     completed_docs = 1

#     # Create threads
#     with ThreadPoolExecutor(max_workers=100) as executor:
#         # Start each thread with correct parameters
#         futures = [(executor.submit(store_document_s3, params[BUCKET_NAME], params[S3_LOCATION], 
#                             params[PAGES_OF_CONTENT], params[DOC_ID], params[TEMPLATE])) for params in document_params]
            
#         # Process threads as they are completed
#         for future in as_completed(futures):
#             # return structure of store_document_s3:
#                 #[bucket_name, s3_file_name, parsed_json, document_id, contents]
#             ret_val = future.result()
#             if ret_val != []:
#                 # Extract return values from thread
#                 bucket_name = ret_val[BUCKET_NAME]
#                 s3_file_name = ret_val[S3_LOCATION]
#                 parsed_json = ret_val[2]
#                 document_id = ret_val[3]
#                 original_doc = ret_val[4]

#                 # Upload document
#                 store_json_document_s3_thread(bucket_name, s3_file_name, parsed_json)
#                 print(f"{Fore.BLUE}Processed record #{completed_docs}{Style.RESET_ALL}")

#                 # Store document for evaluation
#                 with open('s3_uploaded.txt', 'a') as evals:
#                     evals.write(f"{original_doc}parsed:{parsed_json}parsed:\n")

#                 completed_docs += 1

#                 # Log document as completed0
#                 with open("finished_jobs.txt", "a") as finished_jobs:
#                     finished_jobs.write(f"{document_id} ") # write all our successful jobs to a file




# def determine_completed() -> set:
#     """
#     Determines which documents have already been completed

#     :return: Set of all completed document ids
#     """
#     try:
#         with open("finished_jobs.txt", "r") as finished_jobs:
#             data = finished_jobs.read()
#             finished_ids = data.strip().split(" ")
#             return set(finished_ids)
#     except IOError:
#         return {}
    

# def parse_folders(config_path):
#     """
#     Parses and uploads all folders to S3 for each entry in the config file.

#     :param config_path: Path of the config file where each entry represents a doctype in laserfiche.
#     :return: None
#     """

#     with open(config_path) as file:
#         try:
#             config_file = json.load(file)
#             # Process each entry in the config file
#             documents = []
#             for template_name, template_entry in config_file['templates'].items():
#                 # Process folder
#                 print(f"Processing {template_name}")
#                 folder_id = template_entry['folder_id']
#                 template_object = template_entry['template']

#                 # Find completed documents
#                 completed = determine_completed()

#                 # Retrive documents
#                 print(f"Adding documents to queue")
#                 documents = process_folder_recursively(folder_id, template_object, documents, completed) 
                        
#                 # Upload all documents
#             print(f"Parsing and uploading documents")
#             run_threads(documents)
#             return

#         except Exception as e:
#             print(e)
#             return None


if __name__ == "__main__":
    # print(convert_to_json(extract_json_to_text("config1.json"), FILE))
    start_time = time.time()
    print(extract_text_with_form_fields(FILE))
    # parse_folders('config.json')
    # print("Uploaded to S3 successfully")
    # end_time = time.time() - start_time
    # print(f"Program took {end_time} seconds to complete")