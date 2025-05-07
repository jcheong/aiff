# backend/services/form_filler_service.py

import os
import json
from PyPDFForm import FormWrapper # Correct Import
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Use absolute imports
from backend.services.document_service import get_session_documents_content, cleanup_session_files

# --- Path Setup ---
_service_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_service_dir)

PDF_TEMPLATE_DIR_REL = os.getenv("PDF_TEMPLATE_DIR", "templates")
PDF_TEMPLATE_NAME = os.getenv("PDF_TEMPLATE_NAME", "i-765.pdf")
FILLED_FORM_FOLDER_REL = os.getenv("FILLED_FORM_FOLDER", "filled_forms")

PDF_TEMPLATE_DIR_ABS = os.path.join(_backend_dir, PDF_TEMPLATE_DIR_REL)
FILLED_FORM_FOLDER_ABS = os.path.join(_backend_dir, FILLED_FORM_FOLDER_REL)

os.makedirs(FILLED_FORM_FOLDER_ABS, exist_ok=True)
# --- End Path Setup ---


# --- LLM Initialization ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
try:
    extraction_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", google_api_key=GOOGLE_API_KEY, temperature=0.0)
    print("Gemini LLM for extraction (gemini-2.0-flash-lite) initialized.")
except Exception as e:
    print(f"Error initializing extraction LLM: {e}")
    extraction_llm = None
# --- End LLM Initialization ---


# --- Target Fields Definition ---
# Define PDF keys directly, with descriptions instructing LLM on 1/0 logic.
# CRITICAL: Verify these keys EXACTLY match your PDF inspection results.
I765_TARGET_FIELDS = {
    # PDF Keys mapped to descriptions for LLM
    "Line1a_FamilyName[0]": "Your Full Name: Family Name (Last Name)",
    "Line1b_GivenName[0]": "Your Full Name: Given Name (First Name). The first word is the Given Name, and the rest of the words are the Middle Name",
    "Line1c_MiddleName[0]": "Your Full Name: Middle Name. The first word is the Given Name, and the rest of the words are the Middle Name",

    "Line9_Checkbox[1]": "Gender - Male Option: Respond with 1 if text indicates Male. Respond with 0 if text indicates Female. Otherwise respond 0. Value has to be a numerical",
    "Line9_Checkbox[0]": "Gender - Female Option: Respond with 1 if text indicates Female. Respond with 0 if text indicates Male. Otherwise respond 0. Value has to be a numerical",

    "Line17a_CountryOfBirth[0]": "Your Country or Countries of Citizenship or Nationality. Always determine the country name",

    "Line18a_CityTownOfBirth[0]": "Your City of Birth",
    "Line18b_CityTownOfBirth[0]": "Your State or Province of Birth. In the absence of a State or Province of Birth, use the Your City and Country of Birth to find it",
    "Line18c_CountryOfBirth[0]": "Your Country of Birth. Always determine the country name",
    "Line19_DOB[0]": "Your Date of Birth. Format MM/DD/YYYY",

    "Line20b_Passport[0]": "Your Passport Number",
    "Line20d_CountryOfIssuance[0]": "The Country That Issued Your Passport or Travel Document. Always determine the country name",
    "Line20e_ExpDate[0]": "The Expiration Date for your Passport or Travel Document. Format MM/DD/YYYY",

    # Add/remove other PDF fields as necessary
}
# --- End Target Fields Definition ---


# --- Prompt Template Definition ---
# General prompt template - relies on detailed descriptions in I765_TARGET_FIELDS
EXTRACTION_PROMPT_TEMPLATE = """
Based ONLY on the following document text, extract the information requested for filling Form I-765 (Application for Employment Authorization).
Provide the output STRICTLY as a JSON object where keys are the field identifiers and values are the extracted information.
The field identifiers to use are: {field_keys}
Read the specific instructions in the field descriptions below carefully, especially for options like checkboxes.
Descriptions of the fields:
{field_descriptions}

If information for a specific field cannot be determined according to its description, use the value "NOT_FOUND". Do not make up information.

Document Text:
---
{document_content}
---

Extracted JSON Data:
"""

EXTRACTION_PROMPT = PromptTemplate(
    template=EXTRACTION_PROMPT_TEMPLATE,
    input_variables=["document_content", "field_keys", "field_descriptions"]
)
# --- End Prompt Template Definition ---


# --- Data Extraction Function ---
def extract_data_with_llm(document_content: str) -> dict:
    """Uses LLM to extract data based on the predefined I-765 fields and prompt."""
    if not extraction_llm:
        raise ConnectionError("Extraction LLM not initialized.")
    if not document_content:
        print("No document content provided for extraction.")
        return {}

    # Use the fields defined for LLM extraction (includes both gender checkboxes now)
    field_keys = list(I765_TARGET_FIELDS.keys())
    field_descriptions = "\n".join([f"- {key}: {desc}" for key, desc in I765_TARGET_FIELDS.items()])

    extraction_chain = LLMChain(llm=extraction_llm, prompt=EXTRACTION_PROMPT)

    print("Invoking LLM for I-765 data extraction...")
    try:
        response = extraction_chain.invoke({
            "document_content": document_content,
            "field_keys": str(field_keys),
            "field_descriptions": field_descriptions
        })
        llm_output = response.get('text', '')
        print("LLM I-765 extraction response received.")

        try:
            json_response_cleaned = llm_output.strip().lstrip('```json').lstrip('```').rstrip('```')
            extracted_data = json.loads(json_response_cleaned)
            print(f"Parsed extracted data: {extracted_data}")

            # Filter based on target fields AND remove "NOT_FOUND" values.
            # Keep '0' values provided by the LLM for checkboxes.
            final_data = {k: v for k, v in extracted_data.items()
                          if k in I765_TARGET_FIELDS and v != "NOT_FOUND"}
            return final_data # Should contain keys for both checkboxes with '1' or '0'

        except json.JSONDecodeError as json_e:
            print(f"Error decoding LLM JSON response: {json_e}")
            print(f"LLM Raw Output was: {llm_output}")
            return {"error": "Failed to parse extraction result from LLM"}
        except Exception as parse_e:
            print(f"Unexpected error parsing LLM response: {parse_e}")
            return {"error": f"Unexpected error parsing LLM result: {parse_e}"}

    except Exception as llm_e:
        print(f"Error during LLM data extraction call: {llm_e}")
        if "API key not valid" in str(llm_e):
            raise ConnectionError("Extraction failed: Invalid Google API Key.")
        raise RuntimeError(f"LLM extraction failed: {llm_e}") from llm_e
# --- End Data Extraction Function ---


# --- Form Filling Function ---
def fill_i765_form(session_id: str) -> str:
    """
    Orchestrates document retrieval, data extraction (including direct 1/0 for checkboxes),
    and PDF filling for Form I-765. Relies on LLM to provide correct values for all fields.
    Uses absolute paths calculated from the backend directory.
    Returns the absolute path to the filled PDF file.
    """
    print(f"Starting Form I-765 filling process for session: {session_id}")

    template_path_abs = os.path.join(PDF_TEMPLATE_DIR_ABS, PDF_TEMPLATE_NAME)
    print(f"Using PDF template: {template_path_abs}")

    if not os.path.exists(template_path_abs):
        print(f"Error: PDF template not found at {template_path_abs}")
        raise FileNotFoundError(f"PDF template '{PDF_TEMPLATE_NAME}' not found at expected location.")

    # 1. Get aggregated text content
    document_content = get_session_documents_content(session_id)
    extracted_data = {} # Initialize empty dict
    if not document_content:
        print(f"No document content found for session {session_id}. Proceeding with empty form.")
    else:
        # 2. Extract data using LLM
        try:
            # LLM now directly extracts values for PDF fields, including '1' or '0' for checkboxes
            extracted_data = extract_data_with_llm(document_content)
            if "error" in extracted_data:
                raise ValueError(f"Data extraction failed: {extracted_data['error']}")
        except (ConnectionError, RuntimeError, ValueError) as e:
             print(f"Form filling aborted due to extraction error: {e}")
             raise e

    # REMOVED the Python mapping logic for gender here.
    print(f"Data extracted and prepared for PDF filling: {extracted_data}") # Log the final data dict going to PyPDFForm

    # 3. Fill the PDF form using PyPDFForm
    try:
        session_filled_form_dir_abs = os.path.join(FILLED_FORM_FOLDER_ABS, session_id)
        os.makedirs(session_filled_form_dir_abs, exist_ok=True)

        output_pdf_filename = f"{session_id}-filled-{PDF_TEMPLATE_NAME}"
        output_pdf_path_abs = os.path.join(session_filled_form_dir_abs, output_pdf_filename)

        filled_pdf = FormWrapper(template_path_abs)

        # Fill using the extracted_data dictionary directly.
        # PyPDFForm will ignore any keys in extracted_data that aren't actually in the PDF.
        filled_pdf.fill(
            extracted_data,
            adobe_mode=True
        )

        # Save the filled PDF using .read()
        with open(output_pdf_path_abs, "wb+") as output_file:
            output_file.write(filled_pdf.read()) # Use .read() here

        print(f"Filled I-765 PDF saved to: {output_pdf_path_abs}")
        return output_pdf_path_abs

    except Exception as pdf_e:
        print(f"Error during PDF processing for {template_path_abs}: {pdf_e}")
        print("Ensure keys in I765_TARGET_FIELDS match actual PDF field names and required values (e.g., '1' / '0' for checkboxes) are correct.")
        raise IOError(f"Failed to fill or save the I-765 PDF form: {pdf_e}") from pdf_e
# --- End Form Filling Function ---
