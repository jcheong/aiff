import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from backend.vector_store.chroma_db import get_vector_store
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize LLM
try:
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", google_api_key=GOOGLE_API_KEY,
                                 temperature=0.2, convert_system_message_to_human=True)
    print("Gemini LLM (gemini-2.0-flash-lite) initialized successfully.")
except Exception as e:
    print(f"Error initializing Gemini LLM: {e}")
    # Provide guidance if the API key is likely the issue
    if "API key not valid" in str(e):
        print("Please ensure your GOOGLE_API_KEY in the .env file is correct and has access to the Gemini API.")
    llm = None # Set llm to None if initialization fails

# Define a prompt template for RAG
RAG_PROMPT_TEMPLATE = """
Use the following pieces of context from the USCIS information database to answer the user's question.
If you don't know the answer from the context, just say that you don't know, don't try to make up an answer.
Keep the answer concise and helpful.

Context:
{context}

Question: {question}

Helpful Answer:"""

RAG_PROMPT = PromptTemplate(
    template=RAG_PROMPT_TEMPLATE, input_variables=["context", "question"]
)

# Function to get RAG response
def get_rag_response(query: str) -> str:
    """Gets a response from the RAG chain."""
    if llm is None:
         return "Error: LLM not initialized. Please check API key and configuration."

    try:
        vector_store = get_vector_store()
        if not vector_store:
            return "Error: Vector store not available. Please run the data loading script."

        # Create the RetrievalQA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff", # Simple chain type suitable for smaller contexts
            retriever=vector_store.as_retriever(search_kwargs={"k": 3}), # Retrieve top 3 chunks
            chain_type_kwargs={"prompt": RAG_PROMPT},
            return_source_documents=False # Don't return source docs in the response for MVP
        )

        print(f"Invoking RAG chain for query: '{query}'")
        # Langchain key for input is 'query' for RetrievalQA
        result = qa_chain({"query": query})

        print(f"RAG chain response received.")
        # Langchain key for output is 'result'
        return result.get('result', "Sorry, I couldn't process that.")

    except Exception as e:
        print(f"Error during RAG chain execution: {e}")
        # Check for common API key errors
        if "API key not valid" in str(e):
            return "Error: The provided Google API Key is invalid or missing permissions for the Gemini API."
        # Check for vector store connection errors
        if isinstance(e, ConnectionError):
             return f"Error: Could not connect to the vector store. {e}"
        return f"An error occurred: {e}"