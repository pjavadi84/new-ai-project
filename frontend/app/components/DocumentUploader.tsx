"use client";

import React, { useState, FormEvent } from 'react';
import axios from 'axios';

// Set your Django API base URL
const API_BASE_URL = 'http://127.0.0.1:8000/api/';

const DocumentUploader = () => {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [documentId, setDocumentId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file || !title) {
      setMessage('Please select a file and enter a title.');
      return;
    }

    setLoading(true);
    setMessage('Indexing document... This may take a moment.');

    // 1. Use FormData for file uploads
    const formData = new FormData();
    formData.append('title', title);
    formData.append('uploaded_file', file);

    try {
      // 2. POST request to your Django DocumentViewSet
      const response = await axios.post(`${API_BASE_URL}documents/`, formData, {
        headers: {
          // This is critical for Django file uploads
          'Content-Type': 'multipart/form-data',
        },
      });

      // 3. Handle successful response
      const data = response.data;
      setDocumentId(data.id);
      setMessage(
        `Success! Document ID ${data.id} indexed (${data.chunks} chunks).`,
      );
    } catch (error) {
      console.error('Upload Error:', error);
      setMessage('Upload failed. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ border: '1px solid #ccc', padding: '20px' }}>
      <h2>Upload Document (Indexing)</h2>
      <input
        type="text"
        placeholder="Document Title (e.g., My Resume)"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        required
      />
      <input
        type="file"
        accept=".pdf"
        onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Processing...' : 'Upload & Index'}
      </button>

      <p>{message}</p>
      {documentId && (
        <p>
          **Ready to Query! Use Document ID:** **{documentId}**
        </p>
      )}
    </form>
  );
};

export default DocumentUploader;