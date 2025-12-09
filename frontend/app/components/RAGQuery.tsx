import React, { useState, FormEvent } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api/';

const RAGQuery = () => {
  // IMPORTANT: Replace 4 with the Document ID you want to query
  const [documentId, setDocumentId] = useState<number>(4); 
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!query || !documentId) return;

    setLoading(true);
    setAnswer('Searching and generating answer using Llama 2...');

    try {
      // 1. POST request to your dedicated query endpoint
      const response = await axios.post(`${API_BASE_URL}query/`, {
        document_id: documentId,
        query: query,
      }, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      // 2. Display the final answer
      setAnswer(response.data.answer); 

    } catch (error) {
      console.error('Query Error:', error);
      setAnswer('Query failed. Ensure your Django server and Ollama are running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ marginTop: '40px', border: '1px solid #ccc', padding: '20px' }}>
      <h2>Ask Llama 2 (RAG Query)</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="number"
          placeholder="Document ID (e.g., 4)"
          value={documentId}
          onChange={(e) => setDocumentId(Number(e.target.value))}
          required
        />
        <textarea
          placeholder="What is my most recent work experience?"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          rows={4}
          style={{ width: '100%', marginTop: '10px' }}
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Generating...' : 'Get Answer'}
        </button>
      </form>
      
      <div style={{ marginTop: '20px', padding: '10px', border: '1px solid #eee' }}>
        <h3>Answer:</h3>
        <p style={{ whiteSpace: 'pre-wrap' }}>{answer}</p>
      </div>
    </div>
  );
};

export default RAGQuery;