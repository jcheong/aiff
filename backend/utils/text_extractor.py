import os
from pypdf import PdfReader
# --- Use Google Cloud Vision ---
try:
    from google.cloud import vision
    print("Google Cloud Vision library loaded.")
    # Initialize client once if possible (consider if text_extractor is called frequently)
    # For simplicity here, we initialize inside the function, but be mindful of performance.
    # vision_client = vision.ImageAnnotatorClient()
except ImportError:
    print("Warning: google-cloud-vision library not found. Install with 'pip install google-cloud-vision'")
    print("Warning: OCR functionality via Google Cloud Vision will be unavailable.")
    vision = None
# --- End Google Cloud Vision ---

# Keep Pillow for potential future image checks, but not strictly needed for API call
try:
    from PIL import Image
except ImportError:
    Image = None

# Define supported image extensions (can be broader now)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".raw", ".ico", ".pdf", ".tiff", ".gif"} # Vision API supports more

def extract_text(filepath: str) -> str:
    """
    Extracts text content from supported file types (PDF, TXT, Images via Cloud Vision API).
    Returns an empty string or error marker if extraction fails.
    """
    print(f"Attempting to extract text from: {filepath}")
    _, extension = os.path.splitext(filepath.lower())
    text = ""

    try:
        if extension == ".pdf":
            # Note: Vision API can also process PDFs, but pypdf might be faster/cheaper for text-based PDFs
            # You could potentially add logic here to use Vision API for image-based PDFs if pypdf fails.
            print(f"Processing PDF with pypdf: {filepath}")
            try:
                reader = PdfReader(filepath)
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + f"\n--- Page {page_num + 1} ---\n" # Add page separator
                print(f"Extracted approx {len(text)} characters from PDF using pypdf.")
            except Exception as pdf_err:
                print(f"Error reading PDF {filepath} with pypdf: {pdf_err}")
                text = f"[PDF Extraction Error: {pdf_err} - {os.path.basename(filepath)}]"

        elif extension == ".txt":
            print(f"Processing TXT: {filepath}")
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f: # Added errors='ignore'
                    text = f.read()
                print(f"Extracted {len(text)} characters from TXT.")
            except Exception as txt_err:
                print(f"Error reading TXT {filepath}: {txt_err}")
                text = f"[TXT Read Error: {txt_err} - {os.path.basename(filepath)}]"

        # --- Google Cloud Vision OCR Logic ---
        elif extension in IMAGE_EXTENSIONS:
            print(f"Processing Image with Google Cloud Vision: {filepath}")
            if vision is None:
                print("OCR skipped: google-cloud-vision library not installed.")
                text = f"[Cloud OCR Skipped: Library missing - {os.path.basename(filepath)}]"
            else:
                try:
                    # Initialize client here (or reuse a global/passed-in client for performance)
                    client = vision.ImageAnnotatorClient() # Assumes ADC is configured

                    # Read image file content as bytes
                    with open(filepath, "rb") as image_file:
                        content = image_file.read()

                    image = vision.Image(content=content)

                    # Use document_text_detection for better results on dense text/documents
                    print("Sending image to Google Cloud Vision API...")
                    response = client.document_text_detection(image=image)
                    print("Received response from Google Cloud Vision API.")

                    # Check for API errors indicated in the response object
                    if response.error.message:
                        print(f"!!! Cloud Vision API Error for {filepath}: {response.error.message}")
                        raise Exception(f"Cloud Vision API Error: {response.error.message}")

                    # Extract text if annotation exists
                    if response.full_text_annotation:
                        text = response.full_text_annotation.text
                        print(f"Extracted {len(text)} characters via Google Cloud Vision.")
                    else:
                        print(f"No text detected by Google Cloud Vision in {filepath}.")
                        text = f"[No text detected by Cloud OCR - {os.path.basename(filepath)}]"

                except Exception as vision_err:
                     # Catch errors during API call or processing
                     print(f"Error during Google Cloud Vision processing for {filepath}: {vision_err}")
                     text = f"[Cloud OCR Error: {vision_err} - {os.path.basename(filepath)}]"
        # --- End Google Cloud Vision OCR Logic ---

        else:
            print(f"Unsupported file type for text extraction: {extension}")
            text = f"[Unsupported file type: {os.path.basename(filepath)}]"

    except Exception as e:
         # Catch-all for other potential errors (e.g., file access issues)
         print(f"Error processing file {filepath}: {e}")
         text = f"[Error processing file {os.path.basename(filepath)}]"

    # Basic cleaning (optional, Vision API text is usually cleaner than Tesseract)
    # text = "\n".join([line for line in text.splitlines() if line.strip()])

    return text