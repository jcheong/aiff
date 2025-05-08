# Automated Immigration Form Filling MVP

This project is a Minimum Viable Product (MVP) demonstrating the concept of using AI (Large Language Models and RAG) to assist users in answering questions about USCIS procedures and automatically filling a specific immigration form (USCIS Form I-765) based on uploaded documents (including images via OCR).

**Core Problem Solved:** Aims to reduce errors and speed up the process of filling specific USCIS PDF forms by leveraging AI for information retrieval and data extraction from various document types.

**Target Users:** Individuals applying for immigration benefits, Immigration Lawyers/Paralegals.

**Disclaimer:** This is an MVP for demonstration purposes only. It is **NOT** a substitute for professional legal advice. Immigration forms and laws are complex. Always consult with a qualified immigration attorney. The information provided by the chatbot may be incomplete or inaccurate based on the limited pre-loaded data. Data extracted for form filling, especially via OCR, **MUST** be carefully reviewed by the user for correctness before any submission. Use at your own risk.

## MVP Features

*   **Chat Assistant (RAG):** Ask questions about USCIS procedures (based on pre-loaded information, initially focused on I-765) and receive answers generated via Retrieval-Augmented Generation.
*   **Document Upload:** Upload supporting documents (PDF, TXT, common image types like PNG, JPG).
*   **Text Extraction (including OCR):** Extracts text content from uploaded PDF and TXT files. Uses **Google Cloud Vision AI** to perform OCR on uploaded image files.
*   **Dynamic Form Listing:** Lists available USCIS forms based on JSON configuration files.
*   **Automated Form Filling:** Trigger the filling of **any configured USCIS form** (e.g., Form I-765) using data extracted by an LLM (gemini-2.0-flash-lite) from the aggregated text content of uploaded documents for the current session. Handles mapping for specific fields as defined in form configurations.

## Technology Stack

*   **Backend:** Python / Flask
*   **Frontend:** React
*   **AI / LLM:** gemini-2.0-flash-lite (via `langchain-google-genai`)
*   **OCR:** Google Cloud Vision AI API
*   **RAG Framework:** Langchain
*   **Vector Database:** ChromaDB (local)
*   **PDF Manipulation:** PyPDFForm
*   **Architecture:** Modular / Layered (within MVP constraints)

## Prerequisites

*   Python 3.10+ and Pip
*   Node.js and npm (or Yarn)
*   Git (optional, for cloning)
*   **Google Cloud SDK (`gcloud` CLI):** Installed and configured ([https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)). Required for Vision API authentication.
*   **Google Cloud Project:** A GCP project with billing enabled.
*   **APIs Enabled:**
    *   **Cloud Vision API:** Enabled in your GCP project.
    *   **Generative Language API (or Vertex AI):** Enabled for Gemini model access.
*   **Google Gemini API Key:** Obtain from Google AI Studio or configure access via your GCP project.
*   **USCIS Form PDFs:** Download official, fillable PDF versions of any forms you intend to support (e.g., I-765) from the USCIS website.
*   **Form Configuration Files:** Create JSON configuration files for each supported PDF form.

## Setup Instructions

1.  **Clone the Repository (if applicable):**
    ```bash
    git clone <your-repository-url>
    cd aiff # Navigate to the project root directory
    ```

2.  **Backend Setup:**
    *   Navigate to the backend directory *from the root*:
        ```bash
        cd backend
        ```
    *   Create and activate a Python virtual environment:
        ```bash
        python -m venv venv
        # Windows
        .\venv\Scripts\activate
        # macOS / Linux
        source venv/bin/activate
        ```
    *   Install backend dependencies:
        ```bash
        pip install -r requirements.txt
        ```
        *(Ensure `requirements.txt` includes `google-cloud-vision`, `langchain-google-genai`, `flask`, `langchain`, `langchain-community`, `chromadb`, `PyPDFForm`, `python-dotenv`, `Pillow`, `Flask-Cors`, `uuid`)*
    *   Create the environment file `.env` inside the `backend` directory:
        ```dotenv
        # backend/.env
        GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY_HERE # Still needed for embedding/LLM if not using ADC for everything
        PDF_TEMPLATE_DIR=templates # Relative to backend_dir
        # PDF_TEMPLATE_NAME is no longer used directly here; form selection is dynamic
        UPLOAD_FOLDER=uploads # Relative to backend_dir
        FILLED_FORM_FOLDER=filled_forms # Relative to backend_dir
        FORM_CONFIGS_DIR=form_configs # Relative to backend_dir
        VECTOR_DB_PATH=vector_store_data/chroma_db # Relative to backend_dir for load script, absolute in app
        SAMPLE_DATA_DIR=sample_uscis_data # Relative to backend_dir
        ```
        **Note:** Replace `YOUR_GOOGLE_API_KEY_HERE`. Ensure no quotes around the key.
    *   Navigate back to the **root `aiff/` directory**.
    *   Create required directories inside `backend` *from the root*:
        ```bash
        # Ensure you are in the root 'aiff/' directory
        mkdir backend/templates
        mkdir backend/form_configs 
        mkdir backend/sample_uscis_data
        # Note: uploads, filled_forms, vector_store_data created automatically by the app if needed
        ```
    *   Place your downloaded fillable PDF forms (e.g., `i-765.pdf`) inside the `backend/templates/` directory.
    *   For each PDF form in `backend/templates/`, create a corresponding JSON configuration file in `backend/form_configs/`. Example `i-765.json`:
        ```json
        // backend/form_configs/i-765.json (example structure)
        {
          "form_id": "I-765",
          "form_name": "Application for Employment Authorization",
          "pdf_template_filename": "i-765.pdf", // Must match a file in backend/templates/
          "target_fields": {
            "Family Name": "form1[0].#subform[0].Pt1Line1a_FamilyName[0]",
            "Given Name": "form1[0].#subform[0].Pt1Line1b_GivenName[0]",
            // ... other field mappings ...
            "Gender Male Checkbox": "form1[0].#subform[0].Checkbox_Male[0]", // Example checkbox field name
            "Gender Female Checkbox": "form1[0].#subform[0].Checkbox_Female[0]" // Example checkbox field name
          },
          "checkbox_true_value": "1", // Value to check a box (e.g., "1", "Yes", "On")
          "checkbox_false_value": "0" // Value to uncheck a box (e.g., "0", "No", "Off")
        }
        ```
        **Note:** The `target_fields` keys are what the LLM will try to extract. The values are the **exact** field names from your PDF, obtainable using tools that inspect PDF form fields.
    *   Create a sample FAQ file `backend/sample_uscis_data/sample_faq.txt`. Add relevant Q&A content (e.g., about Form I-765).
    *   **Authenticate for Google Cloud Services:** Run this command in your terminal (you only need to do this once per machine usually):
        ```bash
        gcloud auth application-default login
        ```
        Follow the prompts to log in via your browser. This allows the Vision API and potentially the Gemini API client libraries to authenticate automatically.
    *   **Load Vector Database:** Run the data loading script *from the root `aiff/` directory* while the venv is active:
        ```bash
        # Ensure you are in the root 'aiff/' directory
        # Ensure venv is active: .\backend\venv\Scripts\activate (if not already)
        python backend/load_uscis_data.py
        ```
        Verify this script runs without errors. It uses the API key from `.env` for embeddings.
    *   **(CRITICAL - Manual Step for Each Form):** For each PDF form you add:
        1.  Inspect the PDF (e.g., using Adobe Acrobat Pro or an online PDF field inspector) to get the **exact** field names required by `PyPDFForm`.
        2.  Populate the `target_fields` in its corresponding JSON configuration file (in `backend/form_configs/`) with these exact field names.
        3.  Verify the `checkbox_true_value` and `checkbox_false_value` required by your specific PDF for checkboxes.

3.  **Frontend Setup:**
    *   Navigate to the frontend directory *from the root*:
        ```bash
        cd frontend
        ```
    *   Install frontend dependencies:
        ```bash
        npm install
        ```

## Running the Application

1.  **Start the Backend:**
    *   Open a terminal in the **root `aiff/` directory**.
    *   Activate the backend virtual environment:
        ```bash
        # Windows
        .\backend\venv\Scripts\activate
        # macOS / Linux
        source backend/venv/bin/activate
        ```
    *   Run the Flask application using the `--app` flag:
        ```bash
        flask --app backend.app run --port 5001
        ```
    *   Keep this terminal running. Watch for initialization messages ("Gemini LLM initialized...", "Google Cloud Vision library loaded...", etc.) and potential errors.

2.  **Start the Frontend:**
    *   Open *another* terminal in the **`frontend` directory** (`aiff/frontend/`).
    *   Run the React development server:
        ```bash
        npm start
        ```
    *   This should automatically open the application in your default web browser at `http://localhost:3000`.

## Usage / Basic Test Flow

1.  **Open:** Navigate to `http://localhost:3000`.
2.  **Chat:** Ask a question related to the information in your `sample_faq.txt` (e.g., "What documents do I need for I-765?"). Verify a relevant answer is received.
3.  **Prepare Test Data:** Create:
    *   A text file (`my_data.txt`) with some sample info relevant to the form you want to fill.
    *   An image file (`my_image.png` or `.jpg`) with *different* sample info (e.g., passport details clearly visible).
4.  **Upload:** Upload both `my_data.txt` and `my_image.png` using the "Choose File" button. Verify success messages.
5.  **List & Fill Form:**
    *   The application should list available forms (e.g., "Application for Employment Authorization (I-765)").
    *   Select the desired form and click the corresponding "Fill Form" button (e.g., "Fill Form I-765").
6.  **Observe:** Monitor the backend logs. Look for:
    *   Text extraction messages for both TXT and Image (mentioning "Google Cloud Vision").
    *   LLM extraction starting and completing (mentioning the selected form type).
    *   "Parsed raw extracted data" log showing data potentially from both files.
    *   "Final data prepared for PDF filling" log showing the mapped data based on the form's JSON configuration.
    *   PDF filling and saving messages.
7.  **Download & Verify:** Wait for the filled PDF download (e.g., `filled_I-765.pdf`). Open the PDF and **carefully check** if fields are populated correctly, combining data extracted from both the text file and the image via OCR. Verify any checkboxes.

## Project Structure (Simplified)

/aiff
├── backend/
│ ├── services/ # Core logic (chat, docs, form filling)
│ ├── utils/ # Utility functions (text extraction with OCR)
│ ├── vector_store/ # Vector DB interaction (ChromaDB)
│ ├── templates/ # PDF form templates (e.g., i-765.pdf)
│ ├── form_configs/ # JSON configurations for each PDF form
│ ├── sample_uscis_data/ # Sample data for RAG (e.g., sample_faq.txt)
│ ├── vector_store_data/ # ChromaDB persistent storage (.gitignored)
│ ├── uploads/ # Temp storage for uploads (.gitignored)
│ ├── filled_forms/ # Temp storage for filled PDFs (.gitignored)
│ ├── app.py # Flask application, API routes
│ ├── load_uscis_data.py # Script to populate vector DB
│ ├── requirements.txt # Backend dependencies
│ ├── .env # Environment variables (API Key, paths - .gitignored)
│ └── venv/ # Python virtual environment (.gitignored)
├── frontend/
│ ├── public/
│ ├── src/ # React components and logic
│ ├── package.json # Frontend dependencies
│ └── node_modules/ # Frontend libraries (.gitignored)
├── .gitignore # Specifies intentionally untracked files
└── README.md # This file

## Limitations (Current MVP State)

*   **Form Support:** Supports automated filling for any form for which a PDF template and a valid JSON configuration file are provided. The initial example focuses on Form I-765.
*   **RAG Data Scope:** Chat answers are limited to the pre-loaded content in `sample_faq.txt`.
*   **OCR Accuracy:** Relies on Google Cloud Vision API accuracy, which can vary based on image quality. Costs associated with Vision API calls.
*   **LLM Extraction:** Data extraction relies on LLM performance and prompt quality. **User verification of extracted data before relying on the filled form is essential.**
*   **Basic UI/UX:** Interface is minimal; error handling is basic.
*   **No User Accounts:** Sessions are temporary; no data is saved persistently for users.
*   **PDF Field Names & Configuration:** Requires manual inspection of each PDF to get exact field names and careful creation of a corresponding JSON configuration file in `backend/form_configs/`. Errors in configuration will lead to incorrect form filling.

## Future Enhancements

Detailed plans for improving the application beyond the MVP stage can be found here:

*   **Technical Enhancements:** See `ENHANCEMENT_PLAN.md` (You should create this file using the plan generated earlier).
*   **User Experience Enhancements:** See `UX_ENHANCEMENT_PLAN.md` (You should create this file using the plan generated earlier).

## Contributing

(Add contribution guidelines if this were an open-source project).

## License

(Add license information, e.g., MIT, Apache 2.0, or Proprietary).
