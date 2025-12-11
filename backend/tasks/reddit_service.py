import os
import re
import praw
from django.conf import settings
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI

# This directory will store your ChromaDB files (reuse from rag_service)
CHROMA_DB_PATH = os.path.join(settings.BASE_DIR, "chroma_db")


def extract_post_id_from_url(url: str) -> str:
    """
    Extract Reddit post ID from various URL formats.
    Handles patterns like:
    - https://www.reddit.com/r/subreddit/comments/{post_id}/title/
    - https://reddit.com/r/subreddit/comments/{post_id}/title/
    - https://old.reddit.com/r/subreddit/comments/{post_id}/title/
    """
    # Pattern to match /comments/{post_id}/
    pattern = r'/comments/([a-zA-Z0-9]+)/'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    raise ValueError(f"Could not extract post ID from URL: {url}")


def index_reddit_post(url: str) -> dict:
    """
    Fetches Reddit post comments and indexes them into ChromaDB.
    
    Args:
        url: Reddit post URL
        
    Returns:
        dict with status, post_title, post_id, and comment_count
    """
    # Extract post ID from URL
    post_id = extract_post_id_from_url(url)
    
    # Initialize PRAW Reddit instance
    reddit = praw.Reddit(
        client_id=settings.REDDIT_CLIENT_ID,
        client_secret=settings.REDDIT_CLIENT_SECRET,
        user_agent=settings.REDDIT_USER_AGENT
    )
    
    # Fetch submission
    submission = reddit.submission(id=post_id)
    
    # Flatten comment tree
    submission.comments.replace_more(limit=0)
    
    # Filter and create documents
    documents = []
    for comment in submission.comments.list():
        # Skip if comment doesn't have body attribute or body is None/empty
        if not hasattr(comment, 'body') or not comment.body:
            continue
        
        # Filter out short comments (minimum 50 characters)
        comment_body = str(comment.body).strip()
        if len(comment_body) >= 50:
            # Handle deleted/removed authors
            author_name = comment.author.name if comment.author else "[deleted]"
            
            # Create LangChain Document
            doc = Document(
                page_content=comment_body,
                metadata={
                    "author": author_name,
                    "score": getattr(comment, 'score', 0),
                    "source": submission.title,
                    "post_id": submission.id
                }
            )
            documents.append(doc)
    
    if not documents:
        return {
            "status": "error",
            "error": "No comments found that meet the minimum length requirement (50 characters)"
        }
    
    # Initialize embeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Store in ChromaDB
    collection_name = f"reddit_{submission.id}"
    
    Chroma.from_documents(
        documents,
        embeddings,
        collection_name=collection_name,
        persist_directory=CHROMA_DB_PATH
    )
    
    print(f"Indexed {len(documents)} comments for Reddit post: {submission.id}")
    
    return {
        "status": "success",
        "post_title": submission.title,
        "post_id": submission.id,
        "comment_count": len(documents),
        "original_url": url  # Return original URL for attribution
    }


def query_reddit_post(post_id: str, query: str, original_url: str = None) -> dict:
    """
    Queries indexed Reddit comments using RAG pipeline with Gemini.
    Implements data anonymization and compliance features.
    
    Args:
        post_id: Reddit post ID
        query: User question
        original_url: Original Reddit post URL for attribution
        
    Returns:
        dict with 'answer', 'citations' (list of comment authors), and 'source_url'
    """
    # Initialize embeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    collection_name = f"reddit_{post_id}"
    
    # Load the Vector Store and Create the Retriever
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_PATH
    )
    
    # Create retriever with k=10 (standard similarity search)
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 10}
    )
    
    # Retrieve documents with metadata (for attribution)
    retrieved_docs = retriever.get_relevant_documents(query)
    
    # Anonymize data: strip PII before sending to LLM
    # Keep mapping for attribution in final output
    anonymized_comments = []
    citation_mapping = []  # Store author info for attribution
    
    for i, doc in enumerate(retrieved_docs):
        # Extract comment text only (no usernames, no metadata)
        comment_text = doc.page_content.strip()
        anonymized_comments.append(f"Comment {i+1}: {comment_text}")
        
        # Store author info separately for attribution (not sent to LLM)
        author = doc.metadata.get("author", "[deleted]")
        citation_mapping.append({
            "author": author,
            "comment_id": i+1
        })
    
    # Initialize Gemini LLM with safety settings
    # Note: LangChain's ChatGoogleGenerativeAI may not expose all safety settings
    # We'll configure what's available and rely on prompt guardrails
    llm = ChatGoogleGenerativeAI(
        model=settings.GOOGLE_GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.0,
        # Safety settings - these may vary by LangChain version
        # The prompt will also enforce content safety
    )
    
    # Define the prompt template with content guardrails
    template = """
    You are an impartial summarization assistant. Your sole purpose is to synthesize answers based only on the provided discussion comments.
    
    CRITICAL SAFETY RULES:
    - You must refuse to generate or summarize any content that promotes illegal activity, self-harm, hate speech, or harassment.
    - If an answer cannot be generated safely or accurately from the provided comments, you must return a neutral error message: "The content necessary to answer this question is unavailable or violates safety guidelines."
    - Base your answer ONLY on the provided comments. Do not add external knowledge or assumptions.
    - If the comments do not contain enough information to answer the question, state that clearly.
    
    Context (Discussion Comments - anonymized):
    {context}

    Question: {question}
    
    Provide a clear, factual summary based solely on the comments above.
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    
    # Format anonymized comments (no PII)
    anonymized_context = "\n\n".join(anonymized_comments)
    
    # Build the LCEL Chain with anonymized context
    # Create a simple function that returns the formatted context
    def format_context(_):
        return anonymized_context
    
    # Use RunnablePassthrough to pass query, and format context separately
    rag_chain = (
        {
            "context": lambda _: anonymized_context,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    # Run the query
    answer = rag_chain.invoke(query)
    
    # Prepare response with attribution
    # Extract unique authors for citation
    unique_authors = list(set([c["author"] for c in citation_mapping if c["author"] != "[deleted]"]))
    
    return {
        "answer": answer,
        "citations": unique_authors,
        "source_url": original_url or f"https://www.reddit.com/comments/{post_id}/"
    }

