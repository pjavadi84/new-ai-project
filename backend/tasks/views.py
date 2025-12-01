from django.shortcuts import render
# Create your views here.
from rest_framework import viewsets
from .models import Document, Task
from .serializers import TaskSerializer
from .document_serializers import DocumentSerializer
from 

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().order_by('-created_at')
    serializer_class = TaskSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all().order_by('-uploaded-at')
    serializer_class = DocumentSerializer

    # Optional: Allow viewing file metadata without authentication for now