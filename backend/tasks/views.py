# backend/tasks/views.py

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.parsers import MultiPartParser, FormParser # <-- NEW Import
from .document_serializers import DocumentSerializer
from .models import Document
from .rag_service import index_document
from rest_framework.views import APIView
from .rag_service import index_document, query_document


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all().order_by("uploaded_at")
    serializer_class = DocumentSerializer

    # TEMPORARY: These settings bypass authentication/CSRF checks for easier testing
    authentication_classes = [SessionAuthentication, BasicAuthentication] 
    permission_classes = [AllowAny]

    # 🌟 THE FINAL FIX: Explicitly declare the parsers needed for file uploads
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer) -> None:
        # 1. Save the document (This is the file upload and database record creation)
        self.document_instance = serializer.save()
        
        # 2. Run indexing on the saved document instance
        # This will update the instance's 'is_indexed' field inside rag_service.py
        self.chunk_count = index_document(self.document_instance)
        
        # REMOVED BUG: The line 'document_instance = serializer.save()' was duplicated here.

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_create(serializer)  # Runs the saving and indexing logic
        except Exception as exc:
            # Clean up the uploaded file if indexing failed
            if hasattr(self, "document_instance"):
                self.document_instance.delete()
            return Response(
                {
                    "error": "Indexing failed. Check API key/file format or file integrity.",
                    "details": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Ensure the final response uses the data saved/modified in perform_create
        final_response_data = self.get_serializer(self.document_instance).data
        headers = self.get_success_headers(final_response_data)
        
        return Response(
            {
                **final_response_data, # Use the freshly serialized instance data
                "status": "Indexing started successfully",
                "chunks": getattr(self, "chunk_count", None),
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )
    
# --- View for Querying the Document (The RAG Agent) ---
class QueryDocumentView(APIView):
    # TEMPORARY: Allow anyone to access the view for testing
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        # Expecting JSON: {"document_id": 4, "query": "What are my work experiences?"}
        document_id = request.data.get('document_id')
        query = request.data.get('query')

        if not document_id or not query:
            return Response(
                {"error": "Missing 'document_id' or 'query'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Call the LCEL-based RAG service to get the generated answer
            answer = query_document(document_id, query)
            
            return Response(
                {"answer": answer},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            # This catches LLM errors, ChromaDB errors, etc.
            return Response(
                {"error": "Query failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# --- Views for Reddit Insight Agent ---
class RedditIndexView(APIView):
    """View for indexing Reddit post comments."""
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        # Expecting JSON: {"url": "https://www.reddit.com/r/..."}
        url = request.data.get('url')

        if not url:
            return Response(
                {"error": "Missing 'url' parameter"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from .reddit_service import index_reddit_post
            result = index_reddit_post(url)
            
            if result.get("status") == "error":
                return Response(
                    result,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(
                result,
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            # Invalid URL format
            return Response(
                {"error": "Invalid Reddit URL", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # This catches PRAW errors, ChromaDB errors, etc.
            return Response(
                {"error": "Indexing failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RedditQueryView(APIView):
    """View for querying indexed Reddit comments."""
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        # Expecting JSON: {"post_id": "abc123", "query": "What do users think?"}
        post_id = request.data.get('post_id')
        query = request.data.get('query')

        if not post_id or not query:
            return Response(
                {"error": "Missing 'post_id' or 'query'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from .reddit_service import query_reddit_post
            answer = query_reddit_post(post_id, query)
            
            return Response(
                {"answer": answer},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            # This catches LLM errors, ChromaDB errors, etc.
            return Response(
                {"error": "Query failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
