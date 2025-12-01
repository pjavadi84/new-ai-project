from django.db import models


class Task(models.Model):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Document(models.Model):
    title = models.CharField(max_length=255)
    # FileField is key: 'documents/' is a subfolder inside MEDIA_ROOT
    uploaded_file=models.FileField(upload_to='documents/')

    # We will use this flag later to track if the RAG indexing is done
    is_indexed = models.BooleanField(default=False)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title