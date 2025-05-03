import os
import uuid
from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS
from dotenv import load_dotenv
import sys

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
# PDF_TEMPLATE_DIR is likely relative to backend dir too, adjust if needed in form_filler_service
# Ensure PDF_TEMPLATE_NAME is just the filename in .env
PDF_TEMPLATE_NAME = os.getenv("PDF_TEMPLATE_NAME", "i-765.pdf")
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


@app.route('/api/fill-form', methods=['POST'])
def handle_fill_form():
    """Triggers form filling based on session documents and returns the filled PDF."""
    data = request.get_json()
    if not data or 'form_type' not in data or 'session_id' not in data:
        return jsonify({"error": "Missing 'form_type' or 'session_id' in request"}), 400

    form_type = data['form_type']
    session_id = data['session_id']

    # MVP Restriction: Only allow I-765
    if form_type.upper() != "I-765": # <--- CHANGED Form number
        return jsonify({"error": "MVP only supports 'I-765' form type."}), 400 # <--- CHANGED Error message

    print(f"Received request to fill form {form_type} for session {session_id}")

    try:
        # Call the updated service function
        filled_pdf_path = form_filler_service.fill_i765_form(session_id) # <--- CHANGED Function call

        if not filled_pdf_path or not os.path.exists(filled_pdf_path):
             print(f"Form filling process completed but no valid PDF path returned for session {session_id}.")
             document_service.cleanup_session_files(session_id)
             return jsonify({"error": "Form filling failed to produce a file."}), 500

        # Schedule cleanup after the file is sent (same logic as before)
        @after_this_request
        def cleanup(response):
            try:
                print(f"Scheduling cleanup for session {session_id} after request.")
                if os.path.exists(filled_pdf_path):
                    os.remove(filled_pdf_path)
                    print(f"Removed specific filled file: {filled_pdf_path}")
                document_service.cleanup_session_files(session_id)
            except Exception as e:
                print(f"Error during post-request cleanup for session {session_id}: {e}")
            return response

        # Construct download filename based on the template name from .env
        download_filename = f"filled_{os.path.splitext(PDF_TEMPLATE_NAME)[0]}.pdf" # <--- CHANGED: Dynamic name e.g., filled_i-765.pdf

        # Send the file back to the client
        return send_file(
            filled_pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=download_filename # <--- CHANGED
        )

    except FileNotFoundError as fnf_e:
        print(f"Fill form error (FileNotFound) for session {session_id}: {fnf_e}")
        document_service.cleanup_session_files(session_id)
        return jsonify({"error": str(fnf_e)}), 404
    except (ValueError, ConnectionError, RuntimeError, IOError) as service_e:
        print(f"Fill form error (Service Error) for session {session_id}: {service_e}")
        document_service.cleanup_session_files(session_id)
        return jsonify({"error": f"Form filling process failed: {service_e}"}), 500
    except Exception as e:
        print(f"Unexpected fill form error for session {session_id}: {e}")
        import traceback
        traceback.print_exc()
        document_service.cleanup_session_files(session_id)
        return jsonify({"error": "An unexpected error occurred during form filling."}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)