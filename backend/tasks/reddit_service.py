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
        "comment_count": len(documents)
    }


def query_reddit_post(post_id: str, query: str) -> str:
    """
    Queries indexed Reddit comments using RAG pipeline with Gemini 2.5 Flash.
    
    Args:
        post_id: Reddit post ID
        query: User question
        
    Returns:
        Generated answer string
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
    
    # Initialize Gemini LLM
    llm = ChatGoogleGenerativeAI(
        model=settings.GOOGLE_GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.0
    )
    
    # Define the prompt template
    template = """
    You are an assistant for analyzing Reddit comments and generating insights.
    Use the following retrieved Reddit comments to answer the user's question.
    Base your answer only on the provided comments. If the comments do not contain 
    enough information to answer the question, state that clearly.

    Context (Reddit Comments):
    {context}

    Question: {question}
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    
    # Define helper function to format documents
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    # Build the LCEL Chain
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    # Run the query
    answer = rag_chain.invoke(query)
    
    return answer

