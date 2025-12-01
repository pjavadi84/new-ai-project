from rest_framework import status, viewsets
from rest_framework.response import Response

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

    def perform_create(self, serializer) -> None:
        # Save the document and run indexing; stash results for use in create()
        self.document_instance = serializer.save()
        self.chunk_count = index_document(self.document_instance)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_create(serializer)  # side effects only
        except Exception as exc:
            # Clean up the uploaded file if indexing failed
            if hasattr(self, "document_instance"):
                self.document_instance.delete()
            return Response(
                {
                    "error": "Indexing failed. Check API key/file format.",
                    "details": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                **serializer.data,
                "status": "Indexing started successfully",
                "chunks": getattr(self, "chunk_count", None),
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )
