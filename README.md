# AI Project - RAG Pipeline with PDF and Reddit Support

A full-stack application implementing Retrieval-Augmented Generation (RAG) pipelines for both PDF documents and Reddit post comments. The system uses ChromaDB for vector storage, HuggingFace embeddings, and Google Gemini API for generating insights.

## Features

### 1. PDF Document RAG
- Upload PDF documents via web interface
- Automatic document parsing and chunking
- Vector indexing using ChromaDB with HuggingFace embeddings
- Query documents using natural language questions
- Generate insights using Google Gemini API

### 2. Reddit Insight Agent RAG
- Fetch Reddit post comments via PRAW API
- Filter and index comments (minimum 50 characters)
- Store comments in ChromaDB with metadata (author, score, source)
- Query indexed comments to generate insights
- Generate answers using Google Gemini API

## Architecture

### PDF RAG Flow
```
User uploads PDF → Backend parses document → Chunk text → 
HuggingFace embeddings → ChromaDB storage → 
User query → Retrieve relevant chunks → Gemini API → Answer
```

### Reddit RAG Flow
```
User provides Reddit URL → Backend extracts post ID → 
PRAW fetches submission & comments → Filter comments (>50 chars) → 
Create LangChain Documents → ChromaDB storage → 
User query → Retrieve top 10 relevant comments → Gemini API → Answer
```

## Tech Stack

### Backend
- **Django** - Web framework
- **ChromaDB** - Vector database for embeddings
- **LangChain** - RAG pipeline orchestration
- **HuggingFace Embeddings** - Text embeddings (all-MiniLM-L6-v2)
- **PRAW** - Reddit API wrapper
- **Google Gemini API** - LLM for generating answers
- **python-dotenv** - Environment variable management

### Frontend
- **Next.js** - React framework
- **TypeScript** - Type-safe JavaScript
- **Axios** - HTTP client
- **Tailwind CSS** - Styling

## Project Structure

```
new-ai-project/
├── backend/
│   ├── backend/
│   │   ├── settings.py      # Django settings with Reddit API config
│   │   └── urls.py          # API route definitions
│   └── tasks/
│       ├── rag_service.py   # PDF RAG implementation
│       ├── reddit_service.py # Reddit RAG implementation
│       └── views.py         # API endpoints
├── frontend/
│   └── app/
│       ├── components/
│       │   ├── DocumentUploader.tsx  # PDF upload component
│       │   ├── RAGQuery.tsx          # PDF query component
│       │   └── RedditAnalyzer.tsx    # Reddit analyzer component
│       └── page.tsx          # Main page with both features
└── README.md
```

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 18+
- Reddit API credentials (Client ID, Client Secret)
- Google Gemini API key

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install django djangorestframework langchain langchain-chroma langchain-huggingface langchain-google-genai chromadb praw python-dotenv django-cors-headers unstructured
```

4. Create `.env` file in `backend/` directory:
```env
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=RedditInsightAgent/1.0
GOOGLE_API_KEY=your_google_gemini_api_key
GOOGLE_GEMINI_MODEL=gemini-2.0-flash-exp
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Start Django server:
```bash
python manage.py runserver
```

The backend API will be available at `http://127.0.0.1:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

### PDF RAG Endpoints

- `POST /api/documents/upload/` - Upload and index a PDF document
- `POST /api/documents/{id}/query/` - Query an indexed document

### Reddit RAG Endpoints

- `POST /api/reddit/index/` - Index a Reddit post's comments
  - Request body: `{"url": "https://www.reddit.com/r/subreddit/comments/..."}`
  - Response: `{"status": "success", "post_title": "...", "post_id": "...", "comment_count": N}`

- `POST /api/reddit/query/` - Query indexed Reddit comments
  - Request body: `{"post_id": "...", "query": "Your question"}`
  - Response: `{"answer": "Generated insight..."}`

## Usage

### PDF RAG
1. Navigate to the main page
2. Upload a PDF document using the Document Uploader component
3. Wait for indexing to complete
4. Enter your question in the query field
5. Click "Query Document" to get insights

### Reddit Insight Agent
1. Navigate to the main page
2. Paste a Reddit post URL in the Reddit Analyzer component
3. Click "Analyze" to fetch and index comments
4. Once indexed, enter your question about the comments
5. Click "Generate Insight" to get an answer based on the comments

## Implementation Details

### Reddit Service Features
- **URL Parsing**: Extracts post ID from various Reddit URL formats
- **Comment Filtering**: Only indexes comments with 50+ characters
- **Metadata Storage**: Stores author, score, and source information
- **Collection Naming**: Uses `reddit_{post_id}` pattern to avoid conflicts
- **Retriever**: Standard similarity search with k=10 (top 10 relevant comments)

### PDF Service Features
- **Document Parsing**: Uses UnstructuredPDFLoader for complex PDFs
- **Chunking**: RecursiveCharacterTextSplitter with configurable chunk size and overlap
- **Metadata Filtering**: Filters complex metadata before processing
- **Collection Naming**: Uses `doc_{id}` pattern

## Environment Variables

Required environment variables (set in `backend/.env`):

- `REDDIT_CLIENT_ID` - Reddit API client ID
- `REDDIT_CLIENT_SECRET` - Reddit API client secret
- `REDDIT_USER_AGENT` - User agent string for Reddit API (default: "RedditInsightAgent/1.0")
- `GOOGLE_API_KEY` - Google Gemini API key
- `GOOGLE_GEMINI_MODEL` - Gemini model name (default: "gemini-2.0-flash-exp")

## Reddit API Compliance

This implementation complies with Reddit API terms:
- Data anonymization and privacy protection
- Proper attribution of Reddit content
- Respects Reddit's rate limits and usage policies

## Development Notes

- ChromaDB data is stored in `backend/chroma_db/` directory
- Each indexed document/post creates a separate collection
- Embeddings use HuggingFace's `all-MiniLM-L6-v2` model
- The system uses LangChain's LCEL (LangChain Expression Language) for chain construction

## License

[Add your license here]
