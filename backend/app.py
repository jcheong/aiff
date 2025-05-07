import os
import uuid
from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS
from dotenv import load_dotenv
import sys
import json
import glob

# --- Adjust Path Loading for .env ---
# Get the directory where app.py is located
backend_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the path to the .env file within the backend directory
dotenv_path = os.path.join(backend_dir, '.env')
print(f"Loading .env file from: {dotenv_path}")
load_dotenv(dotenv_path=dotenv_path)
# --- End Path Adjustment ---

# Use ONLY absolute imports now
from backend.services import chat_service, document_service, form_filler_service
from backend.vector_store import chroma_db

# --- Adjust Paths for Folders ---
# Use paths relative to the backend directory where app.py lives
UPLOAD_FOLDER = os.path.join(backend_dir, os.getenv("UPLOAD_FOLDER", "uploads"))
FILLED_FORM_FOLDER = os.path.join(backend_dir, os.getenv("FILLED_FORM_FOLDER", "filled_forms"))
_app_dir = os.path.dirname(os.path.abspath(__file__)) 
FORM_CONFIGS_DIR_REL = os.getenv("FORM_CONFIGS_DIR", "form_configs")
FORM_CONFIGS_DIR_ABS = os.path.join(_app_dir, FORM_CONFIGS_DIR_REL)
# --- End Path Adjustment ---

print(f"UPLOAD_FOLDER set to: {UPLOAD_FOLDER}")
print(f"FILLED_FORM_FOLDER set to: {FILLED_FORM_FOLDER}")

# Create folders if they don't exist using the absolute paths
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FILLED_FORM_FOLDER, exist_ok=True)

app = Flask(__name__)
CORS(app)

# Initialize vector store (same as before)
try:
    print("Initializing vector store connection on app start...")
    # Pass the backend_dir if chroma_db needs it to construct full path from .env relative path
    chroma_db.initialize_vector_store(base_path=backend_dir)
except Exception as e:
    print(f"WARNING: Failed to initialize vector store on startup: {e}")


@app.route('/api/chat', methods=['POST'])
def handle_chat():
    data = request.get_json()
    if not data or 'message' not in data or 'session_id' not in data:
        return jsonify({"error": "Missing 'message' or 'session_id' in request"}), 400

    user_message = data['message']
    session_id = data['session_id']

    print(f"Received chat message for session {session_id}: {user_message}")

    # Basic command detection updated for I-765
    # Convert message to lowercase for case-insensitive matching
    if "fill form i-765" in user_message.lower(): # <--- CHANGED Form number
         return jsonify({"reply": "Okay, I can help with that. Please use the 'Fill Form I-765' button.", "action_needed": "trigger_fill_form"}) # <--- CHANGED Form number

    try:
        response = chat_service.get_rag_response(user_message)
        return jsonify({"reply": response})
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        if "API key not valid" in str(e) or isinstance(e, ConnectionError):
             return jsonify({"error": f"Chat service error: {e}"}), 503
        return jsonify({"error": "An internal error occurred in the chat service."}), 500


# /api/upload remains the same

@app.route('/api/upload', methods=['POST'])
def handle_upload():
    """Handles file uploads associated with a session."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    if 'session_id' not in request.form:
         return jsonify({"error": "Missing 'session_id' in form data"}), 400

    file = request.files['file']
    session_id = request.form['session_id']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Assuming document_service is correctly imported
        filename = document_service.save_uploaded_file(file, session_id)
        print(f"File {filename} uploaded for session {session_id}")
        return jsonify({"message": "File uploaded successfully", "filename": filename})
    except ValueError as ve:
         print(f"Upload error for session {session_id}: {ve}")
         return jsonify({"error": str(ve)}), 400
    except IOError as ioe:
         print(f"Upload IO error for session {session_id}: {ioe}")
         return jsonify({"error": "Failed to save uploaded file."}), 500
    except Exception as e:
        print(f"Unexpected upload error for session {session_id}: {e}")
        return jsonify({"error": "An unexpected error occurred during upload."}), 500


@app.route('/api/list-forms', methods=['GET'])
def list_available_forms():
    available_forms = []
    try:
        # Ensure the configuration directory exists
        if not os.path.isdir(FORM_CONFIGS_DIR_ABS):
            print(f"Error: Form configurations directory not found at {FORM_CONFIGS_DIR_ABS}")
            # It might be better to return an empty list or a specific error code
            # depending on how you want the frontend to handle this.
            return jsonify({"error": "Form configurations directory not found.", "path_checked": FORM_CONFIGS_DIR_ABS}), 500

        # Scan for .json files in the form_configs directory
        # Adjust the pattern if your config files might have different casing, e.g., "*.json" or "*.JSON"
        config_files_pattern = os.path.join(FORM_CONFIGS_DIR_ABS, "*.json")
        config_files = glob.glob(config_files_pattern)
        
        if not config_files:
            print(f"No .json configuration files found in {FORM_CONFIGS_DIR_ABS}")
            # Return empty list if no configs are found, which is not necessarily an error.
            return jsonify([]), 200

        for config_file_path in config_files:
            try:
                with open(config_file_path, 'r', encoding='utf-8') as f: # Added encoding
                    config_data = json.load(f)
                
                form_id = config_data.get('form_id')
                form_name = config_data.get('form_name') # This is the user-friendly name

                if form_id and form_name:
                    available_forms.append({"id": form_id, "name": form_name})
                else:
                    # Log if a JSON file is missing required fields, but don't break the whole list
                    file_name = os.path.basename(config_file_path)
                    print(f"Warning: Config file '{file_name}' is missing 'form_id' or 'form_name'. Skipping.")

            except json.JSONDecodeError:
                file_name = os.path.basename(config_file_path)
                print(f"Warning: Could not decode JSON from '{file_name}'. Skipping.")
            except Exception as e: # Catch more general errors during file processing
                file_name = os.path.basename(config_file_path)
                print(f"Warning: Error processing config file '{file_name}': {e}. Skipping.")
        
        return jsonify(available_forms), 200

    except Exception as e:
        # Catch-all for unexpected errors in the route logic itself
        print(f"Error in /api/list-forms endpoint: {e}")
        return jsonify({"error": "An unexpected error occurred while listing forms."}), 500


@app.route('/api/fill-form', methods=['POST'])
def handle_fill_form():
    """Triggers form filling based on session documents and returns the filled PDF."""
    data = request.get_json()
    if not data or 'form_type' not in data or 'session_id' not in data:
        return jsonify({"error": "Missing 'form_type' or 'session_id' in request"}), 400

    form_type = data['form_type']
    session_id = data['session_id']

    # Removed MVP Restriction:
    # No longer restricting to "I-765" only.
    # The form_filler_service will handle whether the form_type is supported.

    print(f"Received request to fill form '{form_type}' for session '{session_id}'")

    try:
        # Call a new generic service function that accepts form_type
        # This function will be responsible for loading the correct form config
        # and using it to process the form.
        # It should return the path to the filled PDF and ideally the suggested download filename.
        filled_pdf_details = form_filler_service.fill_dynamic_form(session_id, form_type)
        # Let's assume fill_dynamic_form returns a dictionary like:
        # {"path": "/path/to/filled_form.pdf", "download_filename": "filled_i-765_john_doe.pdf"}
        # Or, for simplicity now, just the path, and we construct a generic download name.

        if not filled_pdf_details or "path" not in filled_pdf_details or not filled_pdf_details["path"] or not os.path.exists(filled_pdf_details["path"]):
             print(f"Form filling process for '{form_type}' completed but no valid PDF path returned for session '{session_id}'.")
             document_service.cleanup_session_files(session_id) # Cleanup uploaded docs
             return jsonify({"error": f"Form filling for '{form_type}' failed to produce a file."}), 500

        filled_pdf_path = filled_pdf_details["path"]
        # Use a generic download name or one provided by the service
        download_filename = filled_pdf_details.get("download_filename", f"filled_{form_type.replace(' ', '_')}.pdf")


        # Schedule cleanup after the file is sent
        @after_this_request
        def cleanup(response):
            try:
                print(f"Scheduling cleanup for session '{session_id}' after request for form '{form_type}'.")
                if os.path.exists(filled_pdf_path):
                    os.remove(filled_pdf_path)
                    print(f"Removed specific filled file: {filled_pdf_path}")
                # Keep cleaning up uploaded session files
                document_service.cleanup_session_files(session_id)
            except Exception as e:
                print(f"Error during post-request cleanup for session '{session_id}', form '{form_type}': {e}")
            return response

        # Send the file back to the client
        return send_file(
            filled_pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=download_filename
        )

    except FileNotFoundError as fnf_e:
        print(f"Fill form error (FileNotFound) for form '{form_type}', session '{session_id}': {fnf_e}")
        document_service.cleanup_session_files(session_id)
        return jsonify({"error": str(fnf_e)}), 404
    except ValueError as ve: # Specific error for unsupported form type from service
        print(f"Fill form error (ValueError) for form '{form_type}', session '{session_id}': {ve}")
        document_service.cleanup_session_files(session_id)
        return jsonify({"error": str(ve)}), 400 # Bad request if form type is invalid/unsupported
    except (ConnectionError, RuntimeError, IOError) as service_e: # Broader service errors
        print(f"Fill form error (Service Error) for form '{form_type}', session '{session_id}': {service_e}")
        document_service.cleanup_session_files(session_id)
        return jsonify({"error": f"Form filling process for '{form_type}' failed: {service_e}"}), 500
    except Exception as e:
        print(f"Unexpected fill form error for form '{form_type}', session '{session_id}': {e}")
        import traceback
        traceback.print_exc()
        document_service.cleanup_session_files(session_id)
        return jsonify({"error": f"An unexpected error occurred during form '{form_type}' filling."}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)