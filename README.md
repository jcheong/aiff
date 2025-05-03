# Automated Immigration Form Filling MVP

This project is a Minimum Viable Product (MVP) demonstrating the concept of using AI (Large Language Models and RAG) to assist users in answering questions about USCIS procedures and automatically filling a specific immigration form (USCIS Form I-765) based on uploaded documents (including images via OCR).

**Core Problem Solved:** Aims to reduce errors and speed up the process of filling specific USCIS PDF forms by leveraging AI for information retrieval and data extraction from various document types.

**Target Users:** Individuals applying for immigration benefits, Immigration Lawyers/Paralegals.

**Disclaimer:** This is an MVP for demonstration purposes only. It is **NOT** a substitute for professional legal advice. Immigration forms and laws are complex. Always consult with a qualified immigration attorney. The information provided by the chatbot may be incomplete or inaccurate based on the limited pre-loaded data. Data extracted for form filling, especially via OCR, **MUST** be carefully reviewed by the user for correctness before any submission. Use at your own risk.

## MVP Features

*   **Chat Assistant (RAG):** Ask questions about USCIS procedures (specifically related to **pre-loaded I-765 information**) and receive answers generated via Retrieval-Augmented Generation.
*   **Document Upload:** Upload supporting documents (PDF, TXT, common image types like PNG, JPG).
*   **Text Extraction (including OCR):** Extracts text content from uploaded PDF and TXT files. Uses **Google Cloud Vision AI** to perform OCR on uploaded image files.
*   **Automated Form Filling:** Trigger the filling of **Form I-765** using data extracted by an LLM (Gemini 1.5 Pro) from the aggregated text content of uploaded documents for the current session. Handles mapping for specific fields like gender checkboxes.

## Technology Stack

*   **Backend:** Python / Flask
*   **Frontend:** React
*   **AI / LLM:** Google Gemini 1.5 Pro (via `langchain-google-genai`)
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
*   **USCIS Form I-765 PDF:** Download the official, fillable Form I-765 PDF from the USCIS website.

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
        PDF_TEMPLATE_DIR=templates
        PDF_TEMPLATE_NAME=i-765.pdf # Or your exact PDF filename
        UPLOAD_FOLDER=uploads
        FILLED_FORM_FOLDER=filled_forms
        VECTOR_DB_PATH=vector_store_data/chroma_db
        SAMPLE_DATA_DIR=sample_uscis_data
        ```
        **Note:** Replace `YOUR_GOOGLE_API_KEY_HERE`. Ensure no quotes around the key.
    *   Navigate back to the **root `aiff/` directory**.
    *   Create required directories inside `backend` *from the root*:
        ```bash
        # Ensure you are in the root 'aiff/' directory
        mkdir backend/templates
        mkdir backend/sample_uscis_data
        # Note: uploads, filled_forms, vector_store_data created automatically if needed
        ```
    *   Place the downloaded fillable `i-765.pdf` (or the filename matching `PDF_TEMPLATE_NAME` in `.env`) inside the `backend/templates/` directory.
    *   Create a sample FAQ file `backend/sample_uscis_data/sample_faq.txt`. Add relevant Q&A content about Form I-765.
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
    *   **(CRITICAL - Manual Step):** Inspect your specific `i-765.pdf` to get the **exact** field names required by `PyPDFForm`. Update the constants (`PDF_MALE_CHECKBOX_KEY`, `PDF_FEMALE_CHECKBOX_KEY`) and the keys within the `I765_TARGET_FIELDS` dictionary in `backend/services/form_filler_service.py` accordingly. Verify the value needed to check boxes (`PDF_CHECKBOX_TRUE_VALUE`, `PDF_CHECKBOX_FALSE_VALUE` - likely '1' and '0').

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
2.  **Chat:** Ask a question related to the I-765 information in your `sample_faq.txt` (e.g., "What documents do I need for I-765?"). Verify a relevant answer is received.
3.  **Prepare Test Data:** Create:
    *   A text file (`my_data.txt`) with some sample info.
    *   An image file (`my_image.png` or `.jpg`) with *different* sample info (e.g., passport details clearly visible).
4.  **Upload:** Upload both `my_data.txt` and `my_image.png` using the "Choose File" button. Verify success messages.
5.  **Fill Form:** Click the "Fill Form I-765" button.
6.  **Observe:** Monitor the backend logs. Look for:
    *   Text extraction messages for both TXT and Image (mentioning "Google Cloud Vision").
    *   LLM extraction starting and completing.
    *   "Parsed raw extracted data" log showing data potentially from both files.
    *   "Final data prepared for PDF filling" log showing the mapped data (e.g., gender checkboxes set to '1'/'0').
    *   PDF filling and saving messages.
7.  **Download & Verify:** Wait for the `filled_i-765.pdf` download. Open the PDF and **carefully check** if fields are populated correctly, combining data extracted from both the text file and the image via OCR. Verify the gender checkbox.

## Project Structure (Simplified)

/aiff
├── backend/
│ ├── services/ # Core logic (chat, docs, form filling)
│ ├── utils/ # Utility functions (text extraction with OCR)
│ ├── vector_store/ # Vector DB interaction (ChromaDB)
│ ├── templates/ # PDF form templates (e.g., i-765.pdf)
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

*   **Single Form:** Only supports automated filling for Form I-765.
*   **RAG Data Scope:** Chat answers are limited to the pre-loaded content in `sample_faq.txt`.
*   **OCR Accuracy:** Relies on Google Cloud Vision API accuracy, which can vary based on image quality. Costs associated with Vision API calls.
*   **LLM Extraction:** Data extraction relies on LLM performance and prompt quality. **User verification of extracted data before relying on the filled form is essential.**
*   **Basic UI/UX:** Interface is minimal; error handling is basic.
*   **No User Accounts:** Sessions are temporary; no data is saved persistently for users.
*   **PDF Field Names:** Requires manual inspection and configuration of PDF field names in the backend code for the specific `i-765.pdf` used.

## Future Enhancements

Detailed plans for improving the application beyond the MVP stage can be found here:

*   **Technical Enhancements:** See `ENHANCEMENT_PLAN.md` (You should create this file using the plan generated earlier).
*   **User Experience Enhancements:** See `UX_ENHANCEMENT_PLAN.md` (You should create this file using the plan generated earlier).

## Contributing

(Add contribution guidelines if this were an open-source project).

## License

(Add license information, e.g., MIT, Apache 2.0, or Proprietary).