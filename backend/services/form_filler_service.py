# backend/services/form_filler_service.py

import os
import json
from PyPDFForm import FormWrapper # Correct Import
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Use absolute imports
from backend.services.document_service import get_session_documents_content # Removed cleanup_session_files, app.py handles it

# --- Path Setup ---
_service_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_service_dir)

# Get directories from .env, with defaults
FORM_CONFIGS_DIR_REL = os.getenv("FORM_CONFIGS_DIR", "form_configs")
FILLED_FORM_FOLDER_REL = os.getenv("FILLED_FORM_FOLDER", "filled_forms")

FORM_CONFIGS_DIR_ABS = os.path.join(_backend_dir, FORM_CONFIGS_DIR_REL)
FILLED_FORM_FOLDER_ABS = os.path.join(_backend_dir, FILLED_FORM_FOLDER_REL)

os.makedirs(FILLED_FORM_FOLDER_ABS, exist_ok=True)
os.makedirs(FORM_CONFIGS_DIR_ABS, exist_ok=True) # Ensure form configs dir exists
# --- End Path Setup ---


# --- LLM Initialization ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
try:
    # Consider making model name configurable or part of form_config if different forms need different models
    extraction_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", google_api_key=GOOGLE_API_KEY, temperature=0.0)
    print("Gemini LLM for extraction (gemini-2.0-flash-lite) initialized.")
except Exception as e:
    print(f"Error initializing extraction LLM: {e}")
    extraction_llm = None
# --- End LLM Initialization ---


# --- Prompt Template Definition (Remains Generic) ---
EXTRACTION_PROMPT_TEMPLATE_STR = """
{system_prompt}

Based ONLY on the following document text, extract the information requested for filling the specified form.
Provide the output STRICTLY as a JSON object where keys are the field identifiers and values are the extracted information.
The field identifiers to use are: {field_ids}

Read the specific instructions in the field descriptions below carefully.
Descriptions of the fields:
{field_descriptions}

If information for a specific field cannot be determined according to its description, use the value "NOT_FOUND" or omit the key. Do not make up information.

Document Text:
---
{document_content}
---

Extracted JSON Data:
"""

EXTRACTION_PROMPT = PromptTemplate(
    template=EXTRACTION_PROMPT_TEMPLATE_STR,
    input_variables=["system_prompt", "document_content", "field_ids", "field_descriptions"]
)
# --- End Prompt Template Definition ---

def load_form_config(form_type: str) -> dict:
    """Loads the JSON configuration for a given form_type."""
    config_filename = f"{form_type}.json"
    config_path = os.path.join(FORM_CONFIGS_DIR_ABS, config_filename)
    print(f"Attempting to load form configuration from: {config_path}")

    if not os.path.exists(config_path):
        print(f"Error: Form configuration file not found at {config_path}")
        raise FileNotFoundError(f"Configuration for form type '{form_type}' not found.")
    
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        print(f"Successfully loaded configuration for form '{form_type}'.")
        return config_data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {config_path}: {e}")
        raise ValueError(f"Invalid JSON in configuration for form type '{form_type}'.")
    except Exception as e:
        print(f"Unexpected error loading form configuration {config_path}: {e}")
        raise RuntimeError(f"Could not load configuration for '{form_type}'.")


def _extract_data_with_llm_dynamic(document_content: str, form_config: dict) -> dict:
    """Uses LLM to extract data based on the dynamically loaded form configuration."""
    if not extraction_llm:
        raise ConnectionError("Extraction LLM not initialized.")
    if not document_content:
        print("No document content provided for extraction.")
        return {}

    field_definitions = form_config.get('fields', [])
    if not field_definitions:
        print(f"No field definitions found in configuration for form '{form_config.get('form_id', 'Unknown')}'.")
        return {}

    field_ids = [field['id'] for field in field_definitions]
    field_descriptions = "\n".join([f"- {field['id']}: {field['description_for_llm']}" for field in field_definitions])
    
    system_prompt = form_config.get('description_for_llm_system_prompt', 
                                    "You are an expert at extracting specific information from user-provided text to fill out forms accurately.")

    extraction_chain = LLMChain(llm=extraction_llm, prompt=EXTRACTION_PROMPT)

    print(f"Invoking LLM for data extraction for form '{form_config.get('form_id', 'Unknown')}'...")
    try:
        response = extraction_chain.invoke({
            "system_prompt": system_prompt,
            "document_content": document_content,
            "field_ids": str(field_ids), # Pass as string representation of list
            "field_descriptions": field_descriptions
        })
        llm_output_text = response.get('text', '')
        print(f"LLM extraction response received for form '{form_config.get('form_id', 'Unknown')}'.")

        try:
            # Clean potential markdown code block fences
            json_response_cleaned = llm_output_text.strip().lstrip('```json').lstrip('```').rstrip('```')
            if not json_response_cleaned: # Handle empty string case
                 print("LLM returned an empty string after cleaning.")
                 return {"error": "LLM returned empty parsable output."}
            
            extracted_data_raw = json.loads(json_response_cleaned)
            print(f"Parsed extracted data (raw): {extracted_data_raw}")

            # Filter out "NOT_FOUND" values and ensure keys are expected field_ids
            # LLM is expected to return keys matching field['id']
            final_data = {
                k: v for k, v in extracted_data_raw.items()
                if k in field_ids and (v is not None and str(v).upper() != "NOT_FOUND")
            }
            return final_data

        except json.JSONDecodeError as json_e:
            print(f"Error decoding LLM JSON response: {json_e}")
            print(f"LLM Raw Output was: {llm_output_text}")
            return {"error": "Failed to parse extraction result from LLM"}
        except Exception as parse_e:
            print(f"Unexpected error parsing LLM response: {parse_e}")
            return {"error": f"Unexpected error parsing LLM result: {parse_e}"}

    except Exception as llm_e:
        print(f"Error during LLM data extraction call: {llm_e}")
        if "API key not valid" in str(llm_e): # Be careful with error string matching
            raise ConnectionError("Extraction failed: Invalid Google API Key.")
        raise RuntimeError(f"LLM extraction failed: {llm_e}")


def _map_llm_data_to_pdf_fields(llm_extracted_data: dict, form_config_fields: list) -> dict:
    """Maps data extracted by LLM (keyed by field 'id') to PDF field names."""
    data_for_pdf = {}
    for field_def in form_config_fields:
        field_id = field_def['id']
        pdf_field_name = field_def['pdf_field_name']
        data_type = field_def.get('data_type', 'text')
        
        llm_value = llm_extracted_data.get(field_id)

        if llm_value is None or str(llm_value).upper() == "NOT_FOUND":
            continue # Skip if not found or explicitly marked as not found by LLM

        if data_type == 'boolean_checkbox':
            # Assuming LLM returns "Yes", "True", true, "1" for checked
            # and "No", "False", false, "0" for unchecked.
            # Or simply if the value is affirmative.
            affirmative_responses = ['yes', 'true', '1', True] # Case-insensitive check
            if str(llm_value).lower() in affirmative_responses:
                data_for_pdf[pdf_field_name] = field_def.get('checkbox_true_value_for_pdf', True) # Use True or specific value like "1", "Yes"
            # else: if PyPDFForm needs an explicit 'off' value, handle here. Usually, not adding the key means unchecked.
        elif data_type == 'boolean_radio':
            # Example: "radio_options": { "llm_choice_value": {"pdf_field_name": "ActualRadioField", "value_for_pdf": "ExportValue"} }
            # This part needs more specific logic based on how radio_options is structured in your JSON.
            # For simplicity, assuming llm_value directly maps to a key in radio_options which then gives the target field and value.
            # This is a placeholder for more complex radio button logic.
            # A simpler radio approach: LLM extracts the value that should be selected, e.g., "OptionA".
            # The config then maps "OptionA" to the PDF field name for that radio button and its 'on' value.
            # For now, let's assume direct mapping if llm_value is the export value for a radio button group field.
            # This part might need refinement based on actual PDF structure for radio buttons.
            # A common pattern for radio buttons in PyPDFForm is to set the group field to the chosen option's export value.
            data_for_pdf[pdf_field_name] = str(llm_value) # Simplistic for now
        else: # Default for text, date, number etc.
            data_for_pdf[pdf_field_name] = str(llm_value) # Ensure it's a string for PyPDFForm, or format as needed (e.g. dates)
            
            # Potential post-processing based on data_type (e.g., formatting dates, converting to uppercase)
            if data_type == 'text_uppercase':
                data_for_pdf[pdf_field_name] = str(llm_value).upper()
            # Add more type-specific formatting here if needed

    return data_for_pdf


def fill_dynamic_form(session_id: str, form_type: str) -> dict:
    """
    Orchestrates document retrieval, dynamic data extraction, and PDF filling.
    Returns a dictionary with 'path' to the filled PDF and 'download_filename'.
    """
    print(f"Starting dynamic form filling process for form '{form_type}', session: '{session_id}'")

    try:
        form_config = load_form_config(form_type)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        # These errors are specific and should be propagated to app.py to return appropriate HTTP status
        print(f"Configuration error for form '{form_type}': {e}")
        raise e 

    # 1. Get aggregated text content
    document_content = get_session_documents_content(session_id)
    llm_extracted_data = {}
    if not document_content:
        print(f"No document content found for session '{session_id}'. Proceeding with potentially empty data for PDF.")
    else:
        # 2. Extract data using LLM
        try:
            llm_extracted_data = _extract_data_with_llm_dynamic(document_content, form_config)
            if "error" in llm_extracted_data: # Check if LLM extraction itself reported an error
                raise ValueError(f"Data extraction failed: {llm_extracted_data['error']}")
        except (ConnectionError, RuntimeError, ValueError) as e:
             print(f"Form filling aborted due to extraction error: {e}")
             raise e # Propagate to app.py

    # 3. Map LLM extracted data to PDF field names and values
    data_for_pdf = _map_llm_data_to_pdf_fields(llm_extracted_data, form_config.get('fields', []))
    print(f"Data prepared for PDF filling: {data_for_pdf}")

    # 4. Fill the PDF form
    template_file_path_rel = form_config.get('template_path')
    if not template_file_path_rel:
        raise ValueError(f"No 'template_path' defined in configuration for form '{form_type}'.")
    
    template_path_abs = os.path.join(_backend_dir, template_file_path_rel)
    print(f"Using PDF template: {template_path_abs}")

    if not os.path.exists(template_path_abs):
        print(f"Error: PDF template not found at {template_path_abs}")
        raise FileNotFoundError(f"PDF template '{template_file_path_rel}' as specified in config for '{form_type}' not found.")

    try:
        # Ensure session-specific output directory exists under the main filled_forms folder
        session_filled_form_dir_abs = os.path.join(FILLED_FORM_FOLDER_ABS, session_id)
        os.makedirs(session_filled_form_dir_abs, exist_ok=True)

        # Sanitize form_type for use in filename if it contains spaces or special chars
        safe_form_type_filename = "".join(c if c.isalnum() else "_" for c in form_type)
        output_pdf_filename = f"{session_id}-filled-{safe_form_type_filename}.pdf"
        output_pdf_path_abs = os.path.join(session_filled_form_dir_abs, output_pdf_filename)

        pdf_wrapper = FormWrapper(template_path_abs)
        pdf_wrapper.fill(
            data_for_pdf,
            # adobe_mode=True # Keep if it was beneficial, PyPDFForm default is usually fine
        )

        with open(output_pdf_path_abs, "wb+") as output_file:
            output_file.write(pdf_wrapper.read())

        print(f"Filled PDF for form '{form_type}' saved to: {output_pdf_path_abs}")
        
        download_filename = f"filled_{safe_form_type_filename}_{session_id}.pdf" # More unique download name
        return {"path": output_pdf_path_abs, "download_filename": download_filename}

    except Exception as pdf_e:
        print(f"Error during PDF processing for {template_path_abs}: {pdf_e}")
        # Consider logging more details about data_for_pdf here for debugging
        raise IOError(f"Failed to fill or save the PDF form '{form_type}': {pdf_e}")