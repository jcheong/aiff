import os
import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.docstore.document import Document
from dotenv import load_dotenv

load_dotenv()

# Configuration from .env
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "vector_store_data/chroma_db")
SAMPLE_DATA_DIR = os.getenv("SAMPLE_DATA_DIR", "sample_uscis_data")

# Ensure API key is available
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file.")

# Initialize Embeddings model
try:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
    print("Gemini Embeddings model initialized successfully.")
except Exception as e:
    print(f"Error initializing Gemini Embeddings model: {e}")
    # Provide guidance if the API key is likely the issue
    if "API key not valid" in str(e):
        print("Please ensure your GOOGLE_API_KEY in the .env file is correct and has access to the Gemini API.")
    exit(1) # Exit if embeddings can't be initialized

# Function to load documents from a directory
def load_documents_from_directory(directory_path):
    documents = []
    print(f"Loading documents from: {directory_path}")
    for filename in os.listdir(directory_path):
        if filename.endswith(".txt"):
            filepath = os.path.join(directory_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Create Langchain Document objects
                    # Using filename as metadata source for simplicity
                    documents.append(Document(page_content=content, metadata={"source": filename}))
                print(f"Loaded: {filename}")
            except Exception as e:
                print(f"Error loading file {filename}: {e}")
    return documents

# Function to setup ChromaDB
def setup_vector_store(documents):
    if not documents:
        print("No documents loaded, skipping vector store setup.")
        return None

    print("Splitting documents...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)

    if not texts:
        print("No text chunks generated after splitting, skipping vector store setup.")
        return None

    print(f"Generated {len(texts)} text chunks.")
    print(f"Creating Chroma vector store at: {VECTOR_DB_PATH}")
    os.makedirs(VECTOR_DB_PATH, exist_ok=True)

    try:
        # Ensure the directory exists and is writable
        if not os.path.isdir(VECTOR_DB_PATH) or not os.access(VECTOR_DB_PATH, os.W_OK):
             raise OSError(f"Vector DB path '{VECTOR_DB_PATH}' is not a writable directory.")

        # Use Chroma.from_documents to create and persist the store
        vector_store = Chroma.from_documents(
            documents=texts,
            embedding=embeddings,
            persist_directory=VECTOR_DB_PATH
        )
        print("Vector store created and persisted successfully.")
        return vector_store
    except Exception as e:
        print(f"Error creating/persisting Chroma vector store: {e}")
        # Attempt to clean up potentially partially created store
        # Be cautious with rimraf type operations in real scenarios
        # shutil.rmtree(VECTOR_DB_PATH, ignore_errors=True)
        return None

if __name__ == "__main__":
    print("--- Starting USCIS Data Loading Script ---")
    loaded_docs = load_documents_from_directory(SAMPLE_DATA_DIR)
    if loaded_docs:
        vector_store_instance = setup_vector_store(loaded_docs)
        if vector_store_instance:
            print("--- Data Loading and Vector Store Setup Complete ---")
            # Optional: Test query
            # try:
            #     results = vector_store_instance.similarity_search("How to replace green card?", k=1)
            #     print("\nTest query result:", results)
            # except Exception as e:
            #     print(f"Error during test query: {e}")
        else:
            print("--- Vector Store setup failed ---")
    else:
        print("--- No documents were loaded ---")