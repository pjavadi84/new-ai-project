import os


from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
# from langchain_community.embeddings import HuggingFaceEmbeddings # <-- NEW Import
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from django.conf import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain.text_splitter import RecursiveCharacterTextSplitter # pyright: ignore[reportMissingImports]
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_ollama import OllamaLLM



# This directory will store your ChromaDB files
CHROMA_DB_PATH = os.path.join(settings.BASE_DIR, "chroma_db")

def index_document(document_instance):
    """
    Handles the entire RAG ingestion pipeline for a single Document instance.
    """

    # 1. Get the path to the uploaded file
    file_path = document_instance.uploaded_file.path

    # --- 1. Load and Parse ---
    # Using UnstructuredPDFLoader for pdfs that can contain ustructured combinations oftables, objects, credentials, etc.
    # than PyPDFLoader. Let's try this:
    loader = UnstructuredPDFLoader(file_path, mode="elements", strategy="hi_res")
    documents = loader.load()

    # NEW: Filter out complex metadata before chunking/splitting
    documents = filter_complex_metadata(documents)


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
    # RUNNING OUT OF TOKEN. SWITCHED TO HUGGINGFACE EMBEDDINGS  
    # embeddings = OpenAIEmbeddings() # type: ignore
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

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

def query_document(document_id: int, query: str) -> str:
    """
    Builds and invokes an LCEL chain for RAG retrieval and generation.
    """
    # 1. Initialize Components
    # (CURRENTLY RAN OUT OF TOKEN. SWITCHED TO LOCAL EMBEDDING FROM HUGGINGFACE)
    # embeddings = OpenAIEmbeddings()
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    collection_name = f"doc_{document_id}"

    # 2. Load the Vector Store and Create the Retriever
    vectorstore = Chroma(
        collection_name=collection_name, 
        embedding_function=embeddings, 
        persist_directory=CHROMA_DB_PATH
    )

    # The retriever object handles the semantic search (Retrieval)
    retriever = vectorstore.as_retriever(
        search_type="similarity", 
        search_kwargs={"k": 4} # Retrieve the top 4 most relevant chunks
    )

    # 3. Define the LLM (The Generator)
    llm = OllamaLLM(
        model="llama2", # <-- The model name you ran in the terminal
        temperature=0.0
    )

    # 4. Define the Prompt (Crucial for Contextualization)
    template = """
    You are an assistant for question-answering based on the provided document context.
    Use the following retrieved context to answer the user's question concisely.
    If the context does not contain the answer, state that you cannot find the answer in the provided documents.

    Context: {context}

    Question: {question}
    """

    prompt = ChatPromptTemplate.from_template(template)

    # 5. Build the LCEL Chain (The Pipeline)
    
    # Define a helper function to format the retrieved documents into a single string
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # The LCEL Pipeline uses the pipe operator '|' for seamless data flow:
    rag_chain = (
        # 5a. RunnablePassthrough provides the initial input (the question)
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        # 5b. Pass the context and question to the prompt template
        | prompt
        # 5c. Pass the formatted prompt to the LLM
        | llm
        # 5d. Convert the LLM's structured output into a simple string
        | StrOutputParser()
    )

    # 6. Run the query using the final chain
    # We use the key "question" because RunnablePassthrough takes the full input
    answer = rag_chain.invoke(query) 
    
    return answer