import json
import re
from bedrock_utils import invoke_model, make_prompt
from laserfiche_utils import extract_document_path


REPO_NAME = "CityClerk"
CITY_URL = "opengov.slocity.org"


def parse_document(document: str, template: dict, prompt_text: list[str]) -> str:
    """
    Invokes LLM with a specified prompt and document.

    :param document: Document you want to pass to LLM.
    :param template: One-shot JSON template to pass to LLM.
    :param prompt_text: Prompt to be passed to LLM before and after the document.
    :return: LLM's response to prompt
    """

    prompt = make_prompt(prompt_text, template, document)
    print(prompt)
    response, max_token = invoke_model(prompt)
    return response

def extract_json_from_response(response: str) -> str:
    """
    Extracts JSON from LLM response containing JSON and other text.

    :param response: The response you want to parse.
    :return: JSON string from response.
    """

    # Find the first curly brace
    start_json = response.find('{')
    # Find the last curly brace
    end_json = response.rfind('}') + 2
    # Check for failure of find and rfind
    if (start_json != -1 and end_json != -1): 
        # Return response between those indices
        return response[start_json:end_json]


def extract_json_from_tags(response):
    # make the llm return the score in <score> </score> tags.  
    # return the repsonse between those tages
    
    pattern = r'<json>(.*?)process_folder_recursively</json>'
    match = re.search(pattern, response, re.DOTALL)

    if match:
        json = match.group(1)
        return json
    else:
        raise ValueError
    

def extract_json_to_text(json_filepath, output_filepath=None):
    """
    Extracts data from a JSON file and returns it as a formatted text string.

    Args:
        json_filepath (str): The path to the JSON file.
        output_filepath (str, optional): The path to save the output text file. 
                                       If None, the text will be printed to the console.

    Returns:
        str: A string representation of the extracted JSON data.
    """
    try:
        with open(json_filepath, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
         return f"Error: File not found: {json_filepath}"
    except json.JSONDecodeError:
        return f"Error: Invalid JSON format in {json_filepath}"

    return data


def add_path_to_json(json_string: str, document_id: int, original_prompt: str) -> json:
    """
    Add a URL referencing the original document to a JSON object

    :param json_string: JSON string to add URL to.
    :param document_id: ID of the document represented by the JSON object.
    :param original_prompt: Prompt used to create JSON object.
    :return: JSON object with URL.
    """

    try:
        # Convert JSON to dict
        parsed_dict = json.loads(json_string)

        # Create and add URL
        url = f"{CITY_URL}/WebLink/DocView.aspx?id={document_id}&dbid=0&repo={REPO_NAME}"
        parsed_dict['URL'] = url

        print(f"Added url to {extract_document_path(document_id)}")

        # Return JSON object in proper format
        return json.dumps(parsed_dict, indent=4, separators=(',',': '))
    
    except ValueError as e:
        # Converting to JSON failed
        print("Not Valid JSON, attempting to reformat")
        with open("json_errors.txt", "a") as file:
            file.write(f"{e}\n{json_string}\n")
        
        # Reformat JSON
        parsed_dict = format_json(json_string, original_prompt, e)

        if parsed_dict:
            # Create and add URL
            url = f"{CITY_URL}/WebLink/DocView.aspx?id={document_id}&dbid=0&repo={REPO_NAME}"
            parsed_dict['URL'] = url

            print(f"Added url to {extract_document_path(document_id)}")

            # Return JSON object in proper format
            return json.dumps(parsed_dict, indent=4, separators=(',',': '))
        
        # Reformatting failed
        else:
            # Log error
            with open("failed_documents.txt", "a") as errors:
                errors.write(f"{document_id} ")   


def format_json(misformatted_json: str, prompt: str, error) -> json:
    """
    Reformats a misformatted JSON string by invoking an LLM

    :param misformatted_json: The misformatted JSON string.
    :param prompt: The original prompt used to create that string.
    :param error: The error associated with attempting to convert that string into JSON
    :return: None on Failure, JSON object on success
    """

    prompt = f"Human: This is my original prompt. {prompt}\n{misformatted_json}\nThis is the error: {error}\n. Make sure to close all brackets and all closing braces at the end of the object. Fix all formatting issues and return the new json object\n\nAssistant:"
    
    response = invoke_until_completion(prompt)

    if response:
        try:
            # Convert response into JSON
            parsed_response = extract_json_from_response(response)
            parsed_dict = json.loads(parsed_response)
            return parsed_dict
        except ValueError as e: 
            # Parsing failed, error handled in parent
            return None
    else:
        # Bad LLM response
        return None
    

