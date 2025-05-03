# backend/vector_store/chroma_db.py
import os
# Use community version
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# Remove load_dotenv here if app.py handles it

VECTOR_DB_REL_PATH = os.getenv("VECTOR_DB_PATH", "vector_store_data/chroma_db")

vector_store = None
embeddings = None # Keep track of embeddings instance at module level too

def initialize_vector_store(base_path=None):
    global vector_store, embeddings # Declare modification of globals
    if vector_store is not None: # Already initialized? Skip.
         print("Vector store already initialized.")
         return

    print("Attempting to initialize vector store...") # Indicate start

    # Construct absolute path only once
    if base_path is None:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    vector_db_abs_path = os.path.join(base_path, VECTOR_DB_REL_PATH)
    print(f"Target ChromaDB absolute path: {vector_db_abs_path}")

    if not os.path.isdir(vector_db_abs_path): # Check directory existence first
         raise FileNotFoundError(f"Chroma DB persist directory does not exist: {vector_db_abs_path}. Run load_uscis_data.py first.")

    try:
        print(f"Initializing embeddings model...")
        temp_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=os.getenv("GOOGLE_API_KEY"))

        if temp_embeddings is None:
             print("!!! ERROR: Failed to initialize GoogleGenerativeAIEmbeddings object (returned None).")
             raise ValueError("Failed to initialize embeddings function.")

        print(f"Embeddings object created successfully: {type(temp_embeddings)}")
        embeddings = temp_embeddings # Assign to global *after* successful creation

        print(f"Loading existing Chroma vector store from: {vector_db_abs_path}")
        # Pass the validated embeddings object
        vector_store = Chroma(persist_directory=vector_db_abs_path, embedding_function=embeddings)

        if vector_store is None:
             print("!!! ERROR: Chroma object is None after initialization.")
             raise ValueError("Failed to load Chroma vector store.")

        print(f"Chroma vector store loaded successfully: {type(vector_store)}")

        # --- ADD DEBUG QUERY ---
        print("--- Attempting debug query within initialization ---")
        try:
            # Ensure both objects seem valid before trying query
            if not hasattr(vector_store, 'similarity_search'):
                 print("!!! ERROR: vector_store object lacks similarity_search method. Cannot perform debug query.")
            elif embeddings is None:
                 print("!!! ERROR: embeddings object is None. Cannot perform debug query.")
            else:
                 test_query = "A-Number" # Simple query string
                 print(f"--- Performing similarity_search for: '{test_query}' ---")
                 # This call requires the embedding function internally
                 debug_results = vector_store.similarity_search(test_query, k=1)
                 print(f"--- Debug query results for '{test_query}': {debug_results} ---")
                 print(f"--- Debug query successful! Embedding function was attached correctly during initialization. ---")
        except Exception as debug_e:
            print(f"!!! ERROR during debug query: {debug_e} !!!")
            print(f"!!! This indicates the embedding function is likely missing or invalid immediately after Chroma object creation. !!!")
        # --- END DEBUG QUERY ---

    except Exception as e:
        print(f"!!! EXCEPTION during vector store initialization: {e}")
        embeddings = None
        vector_store = None
        raise ConnectionError(f"Failed to initialize ChromaDB or embeddings: {e}") from e

def get_vector_store():
    """Returns the initialized vector store instance. Initializes if needed."""
    # Relying on explicit init during app startup
    if vector_store is None:
         print("!!! ERROR in get_vector_store: vector_store is None. Initialization likely failed.")
         # Avoid trying to re-initialize here as path context might be missing
         raise RuntimeError("Vector store was not successfully initialized during startup.")
    return vector_store