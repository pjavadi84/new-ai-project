import os
import re
import praw
import prawcore.exceptions
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
    if not settings.REDDIT_CLIENT_ID or not settings.REDDIT_CLIENT_SECRET:
        raise ValueError("Reddit API credentials not configured. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env file")
    
    reddit = praw.Reddit(
        client_id=settings.REDDIT_CLIENT_ID,
        client_secret=settings.REDDIT_CLIENT_SECRET,
        user_agent=settings.REDDIT_USER_AGENT
    )
    
    # Fetch submission
    try:
        submission = reddit.submission(id=post_id)
        # Load submission attributes (title, etc.) - this triggers API call
        _ = submission.title  # This triggers loading if not already loaded
        if not submission.title:
            raise ValueError("Submission has no title - may be deleted or inaccessible")
    except prawcore.exceptions.NotFound:
        raise ValueError(f"Reddit post with ID '{post_id}' not found. The post may have been deleted or the ID is invalid.")
    except prawcore.exceptions.Forbidden:
        raise ValueError(f"Access forbidden to Reddit post '{post_id}'. The post may be private or restricted.")
    except ValueError:
        raise  # Re-raise ValueError as-is to preserve specific error messages
    except Exception as e:
        raise ValueError(f"Failed to fetch Reddit submission: {str(e)}. Check if the post ID is valid and accessible.")
    
    # Flatten comment tree
    try:
        submission.comments.replace_more(limit=0)
    except Exception as e:
        raise ValueError(f"Failed to load comments: {str(e)}")
    
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
    # Validate inputs
    if not post_id:
        raise ValueError("post_id is required")
    if not query:
        raise ValueError("query is required")
    
    # Check Gemini API key
    if not settings.GOOGLE_API_KEY:
        raise ValueError("Google Gemini API key not configured. Please set GOOGLE_API_KEY in .env file")
    
    # Initialize embeddings
    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    except Exception as e:
        raise ValueError(f"Failed to initialize embeddings: {str(e)}")
    
    collection_name = f"reddit_{post_id}"
    
    # Load the Vector Store and Create the Retriever
    try:
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=CHROMA_DB_PATH
        )
    except Exception as e:
        raise ValueError(f"Failed to load ChromaDB collection '{collection_name}'. The post may not have been indexed yet. Error: {str(e)}")
    
    # Create retriever with k=10 (standard similarity search)
    try:
        retriever = vectorstore.as_retriever(
            search_kwargs={"k": 10}
        )
    except Exception as e:
        raise ValueError(f"Failed to create retriever: {str(e)}")
    
    # Retrieve documents with metadata (for attribution)
    try:
        # In newer LangChain versions, use invoke() instead of get_relevant_documents()
        retrieved_docs = retriever.invoke(query)
        if not retrieved_docs:
            raise ValueError(f"No relevant comments found for query. The post may not have enough indexed comments.")
    except ValueError:
        raise  # Re-raise ValueError as-is
    except Exception as e:
        raise ValueError(f"Failed to retrieve documents: {str(e)}")
    
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
    try:
        llm = ChatGoogleGenerativeAI(
            model=settings.GOOGLE_GEMINI_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.0,
            # Safety settings - these may vary by LangChain version
            # The prompt will also enforce content safety
        )
    except Exception as e:
        raise ValueError(f"Failed to initialize Gemini LLM. Check your GOOGLE_API_KEY and GOOGLE_GEMINI_MODEL settings. Error: {str(e)}")
    
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
    try:
        answer = rag_chain.invoke(query)
        if not answer or not answer.strip():
            raise ValueError("Gemini API returned an empty response")
    except Exception as e:
        error_msg = str(e)
        if "API key" in error_msg or "authentication" in error_msg.lower():
            raise ValueError(f"Gemini API authentication failed. Check your GOOGLE_API_KEY. Error: {error_msg}")
        elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
            raise ValueError(f"Gemini API quota exceeded or rate limited. Please try again later. Error: {error_msg}")
        else:
            raise ValueError(f"Failed to generate answer from Gemini API: {error_msg}")
    
    # Prepare response with attribution
    # Extract unique authors for citation
    unique_authors = list(set([c["author"] for c in citation_mapping if c["author"] != "[deleted]"]))
    
    return {
        "answer": answer,
        "citations": unique_authors,
        "source_url": original_url or f"https://www.reddit.com/comments/{post_id}/"
    }

