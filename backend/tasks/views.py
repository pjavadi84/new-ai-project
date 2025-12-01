# backend/tasks/views.py

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.parsers import MultiPartParser, FormParser # <-- NEW Import
from .document_serializers import DocumentSerializer
from .models import Document, Task
from .rag_service import index_document
from .serializers import TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().order_by("-created_at")
    serializer_class = TaskSerializer


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