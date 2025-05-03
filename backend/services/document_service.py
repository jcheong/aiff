# backend/services/document_service.py

import os
import shutil
from werkzeug.utils import secure_filename
# Use absolute import for text_extractor
from backend.utils.text_extractor import extract_text
# No load_dotenv here - app.py handles it

# --- Path Setup ---
_service_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_service_dir)

# Read relative paths/names from environment variables
UPLOAD_FOLDER_REL = os.getenv("UPLOAD_FOLDER", "uploads")
FILLED_FORM_FOLDER_REL = os.getenv("FILLED_FORM_FOLDER", "filled_forms") # Needed for cleanup

# Construct absolute paths relative to the backend directory
UPLOAD_FOLDER_ABS = os.path.join(_backend_dir, UPLOAD_FOLDER_REL)
FILLED_FORM_FOLDER_ABS = os.path.join(_backend_dir, FILLED_FORM_FOLDER_REL)

# Ensure the base upload directory exists
os.makedirs(UPLOAD_FOLDER_ABS, exist_ok=True)
# --- End Path Setup ---

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif', 'webp'} # Added more image types

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, session_id: str):
    """Saves an uploaded file to a session-specific directory using absolute paths."""
    if not session_id:
        raise ValueError("session_id is required to save file.")
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Use the absolute path for the base uploads folder
        session_upload_path = os.path.join(UPLOAD_FOLDER_ABS, session_id)
        os.makedirs(session_upload_path, exist_ok=True) # Create session dir if not exists
        filepath = os.path.join(session_upload_path, filename)
        try:
            file.save(filepath)
            print(f"File saved successfully: {filepath}")
            return filename
        except Exception as e:
            print(f"Error saving file {filename} for session {session_id}: {e}")
            raise IOError(f"Could not save file {filename}.") from e
    elif file:
        raise ValueError(f"File type not allowed: {file.filename}")
    else:
        raise ValueError("No file provided.")

def get_session_documents_content(session_id: str) -> str:
    """Aggregates text content from all supported files in a session's upload directory using absolute paths."""
    if not session_id:
        print("No session ID provided for document retrieval.")
        return ""

    # Use the absolute path for the base uploads folder
    session_upload_path = os.path.join(UPLOAD_FOLDER_ABS, session_id)
    aggregated_content = ""

    if not os.path.isdir(session_upload_path):
        print(f"No upload directory found for session: {session_id} at {session_upload_path}")
        return ""

    print(f"Aggregating content for session: {session_id} from {session_upload_path}")
    for filename in os.listdir(session_upload_path):
        filepath = os.path.join(session_upload_path, filename)
        if os.path.isfile(filepath):
            print(f"Processing file: {filename}")
            aggregated_content += f"\n--- Content from {filename} ---\n"
            # text_extractor expects an absolute path already
            file_content = extract_text(filepath)
            aggregated_content += file_content + "\n"

    print(f"Total aggregated content length for session {session_id}: {len(aggregated_content)}")
    return aggregated_content

def cleanup_session_files(session_id: str):
    """Removes the upload and filled form directories for a given session using absolute paths."""
    # Use the absolute paths calculated at the top
    session_upload_path = os.path.join(UPLOAD_FOLDER_ABS, session_id)
    session_filled_form_path = os.path.join(FILLED_FORM_FOLDER_ABS, session_id)

    print(f"Cleaning up files for session: {session_id}")
    if os.path.isdir(session_upload_path):
        try:
            shutil.rmtree(session_upload_path)
            print(f"Removed upload directory: {session_upload_path}")
        except Exception as e:
            print(f"Error removing upload directory {session_upload_path}: {e}")

    if os.path.isdir(session_filled_form_path):
         try:
             shutil.rmtree(session_filled_form_path)
             print(f"Removed filled forms directory: {session_filled_form_path}")
         except Exception as e:
             print(f"Error removing filled forms directory {session_filled_form_path}: {e}")