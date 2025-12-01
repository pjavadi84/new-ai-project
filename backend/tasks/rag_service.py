import os


from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from django.conf import settings
from langchain.text_splitter import RecursiveCharacterTextSplitter # pyright: ignore[reportMissingImports]

# This directory will store your ChromaDB files
CHROMA_DB_PATH = os.path.join(settings.BASE_DIR, "chroma_db")

def index_document(document_instance):
    """
    Handles the entire RAG ingestion pipeline for a single Document instance.
    """

    # 1. Get the path to the uploaded file
    file_path = document_instance.uploaded_file.path

    # --- 1. Load and Parse ---
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    # --- 2. Chunking (Splitting) ---
    # Interview Focus: Chunking is vital for context. 
    # Small chunks (e.g., 500) prevent hitting LLM token limits.
    # Overlap (e.g., 50) helps maintain context across chunks.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=100,
        length_function=len
    )

    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} pages into {len(chunks)} chunks.")

    # --- 3. Embedding ---
    # We use the OpenAI model for conversion (Text -> Vector)
    embeddings = OpenAIEmbeddings(openai_api_key=os.environ.get("OPENAI_API_KEY")) # type: ignore

    # --- 4. Storage in Vector Database ---
    # We use the document's ID as the collection name to isolate its vectors
    collection_name = f"doc_{document_instance.id}"

    # This creates/loads the vector store and adds the documents
    Chroma.from_documents(
        chunks, 
        embeddings, 
        collection_name=collection_name, 
        persist_directory=CHROMA_DB_PATH
    )

    # Final step: Mark the document as indexed
    document_instance.is_indexed = True
    document_instance.save()
    
    print(f"Indexing complete for Document ID: {document_instance.id}")

    return len(chunks)