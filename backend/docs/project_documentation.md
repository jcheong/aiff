# Project Overview

This project is designed to fill out Form I-765 (Application for Employment Authorization) using data extracted from various documents. It leverages Large Language Models (LLM) for data extraction and PyPDFForm for filling PDF forms.

## Key Components

### app.py
The main application file that orchestrates the overall workflow.

### services/
Directory containing service files that handle specific functionalities.

#### chat_service.py
Handles chat-related functionality, potentially used for user interaction or document processing.

#### document_service.py
Manages document-related operations, including retrieval and cleanup of session files.

#### form_filler_service.py
Orchestrates the form filling process, including data extraction using LLM and PDF processing.

### utils/
Directory containing utility files.

#### text_extractor.py
Handles text extraction from various file types, including PDFs, text files, and images using the Google Cloud Vision API.

## Detailed Functionality

### Data Extraction
The application uses LLM (specifically Gemini) to extract relevant data from documents. The extraction process is guided by predefined field descriptions and instructions for handling specific data types, such as checkboxes. The `extract_data_with_llm` function in `form_filler_service.py` orchestrates this process by:
1. Initializing the LLM chain with a prompt template that includes field keys and descriptions.
   - **Prompt Template**: The `EXTRACTION_PROMPT_TEMPLATE` defines how the LLM should extract data. It includes placeholders for `field_keys` and `field_descriptions`, which are populated based on `I765_TARGET_FIELDS`.
2. Invoking the LLM to extract data based on the document content.
   - **LLM Invocation**: The `extraction_chain.invoke` method is used to call the LLM with the prepared prompt. The response is then processed to extract the required information.
3. Parsing the LLM's response into a JSON object and filtering the results based on the target fields defined in `I765_TARGET_FIELDS`.
   - **Response Handling**: The LLM's response is expected to be a JSON object. The code cleans and parses this response, filtering out any "NOT_FOUND" values and ensuring that checkbox values are correctly represented as '1' or '0'.

**Example**:
- For a document containing a user's name and gender, the LLM will extract the name and gender information.
- The gender information will be used to fill the corresponding checkbox in the I-765 form.

### Form Filling
After data extraction, the application fills out a PDF form (I-765) using the extracted data. It utilizes PyPDFForm to handle PDF processing. The `fill_i765_form` function in `form_filler_service.py`:
1. Retrieves the document content for the given session ID.
2. Extracts data using the LLM.
3. Fills the PDF form using the extracted data, ensuring that checkbox values are correctly represented as '1' or '0'.

**Example**:
- If the extracted data includes "Line1a_FamilyName[0]: Smith" and "Line9_Checkbox[1]: 1", the PDF form will be filled with "Smith" in the family name field and the male gender checkbox will be checked.

### Text Extraction
The project supports text extraction from various file types:
1. **PDFs**: Using pypdf for text-based PDFs. The `extract_text` function in `text_extractor.py` reads PDF files page by page and extracts text content.
2. **Text files**: Simple reading of text content.
3. **Images**: Using the Google Cloud Vision API for OCR (Optical Character Recognition). The `extract_text` function initializes the Google Cloud Vision client and uses the `document_text_detection` method to extract text from images.

**Example**:
- For a PDF document, the text extraction will result in a string containing the text content of all pages.
- For an image, the Google Cloud Vision API will be used to detect and extract text, handling cases where the image contains dense text or document-like content.

## Project Structure and Workflow

The project follows a modular structure with key components:
- `app.py`: The main entry point that orchestrates the workflow.
- `services/`: Contains business logic for chat, document management, and form filling.
- `utils/`: Utility functions for text extraction.

The workflow typically involves:
1. Document upload or retrieval.
2. Text extraction from documents.
3. Data extraction using LLM.
4. Form filling using the extracted data.
5. Saving the filled PDF form.

## Examples and Use Cases

1. **Basic Usage**: Provide documents (PDFs, images, or text files) to the application. The application will extract relevant data and fill out the I-765 form accordingly.
2. **Customization**: Modify the `I765_TARGET_FIELDS` in `form_filler_service.py` to include or exclude PDF fields as necessary for different form templates.

## Configuration and Usage

1. Ensure the required environment variables are set, such as `GOOGLE_API_KEY`, `PDF_TEMPLATE_DIR`, `PDF_TEMPLATE_NAME`, and `FILLED_FORM_FOLDER`.
2. Place the PDF template (I-765) in the specified template directory.
3. Run the application, providing the necessary documents for processing.
4. Verify that the PDF template field names match those defined in `I765_TARGET_FIELDS`.

## Notes

- The project relies on external services (LLM and Google Cloud Vision API), so ensure these are properly configured and accessible.
