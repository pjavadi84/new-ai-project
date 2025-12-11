"use client";

import React, { useState, FormEvent } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api/';

const RedditAnalyzer = () => {
  const [url, setUrl] = useState<string>('');
  const [postId, setPostId] = useState<string | null>(null);
  const [postTitle, setPostTitle] = useState<string | null>(null);
  const [commentCount, setCommentCount] = useState<number | null>(null);
  const [query, setQuery] = useState<string>('');
  const [answer, setAnswer] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [indexing, setIndexing] = useState<boolean>(false);
  const [status, setStatus] = useState<string>('');

  const handleIndex = async (e: FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setIndexing(true);
    setStatus('Indexing Reddit post comments...');
    setPostId(null);
    setPostTitle(null);
    setCommentCount(null);
    setAnswer('');

    try {
      const response = await axios.post(`${API_BASE_URL}reddit/index/`, {
        url: url,
      }, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.data.status === 'success') {
        setPostId(response.data.post_id);
        setPostTitle(response.data.post_title);
        setCommentCount(response.data.comment_count);
        setStatus(`Successfully indexed ${response.data.comment_count} comments from "${response.data.post_title}"`);
      } else {
        setStatus(`Error: ${response.data.error || 'Indexing failed'}`);
      }
    } catch (error: any) {
      console.error('Indexing Error:', error);
      const errorMessage = error.response?.data?.error || error.response?.data?.details || 'Indexing failed. Check your Reddit API credentials and URL.';
      setStatus(`Error: ${errorMessage}`);
    } finally {
      setIndexing(false);
    }
  };

  const handleQuery = async (e: FormEvent) => {
    e.preventDefault();
    if (!query || !postId) return;

    setLoading(true);
    setAnswer('Generating insight using Gemini 2.5 Flash...');
    setStatus('');

    try {
      const response = await axios.post(`${API_BASE_URL}reddit/query/`, {
        post_id: postId,
        query: query,
      }, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      setAnswer(response.data.answer);
      setStatus('Insight generated successfully!');
    } catch (error: any) {
      console.error('Query Error:', error);
      const errorMessage = error.response?.data?.error || error.response?.data?.details || 'Query failed. Ensure your Django server and Gemini API are configured.';
      setAnswer('');
      setStatus(`Error: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ marginTop: '40px', border: '1px solid #ccc', padding: '20px' }}>
      <h2>Reddit Insight Agent</h2>
      
      {/* Index Section */}
      <form onSubmit={handleIndex} style={{ marginBottom: '20px' }}>
        <input
          type="text"
          placeholder="Reddit Post URL (e.g., https://www.reddit.com/r/python/comments/...)"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
          required
        />
        <button type="submit" disabled={indexing}>
          {indexing ? 'Analyzing...' : 'Analyze'}
        </button>
      </form>

      {/* Status Display */}
      {status && (
        <div style={{ marginTop: '10px', padding: '10px', border: '1px solid #eee', backgroundColor: '#f9f9f9' }}>
          <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{status}</p>
        </div>
      )}

      {/* Post Info Display */}
      {postId && postTitle && commentCount !== null && (
        <div style={{ marginTop: '20px', padding: '10px', border: '1px solid #4CAF50', backgroundColor: '#e8f5e9' }}>
          <h3 style={{ marginTop: 0 }}>Post Indexed</h3>
          <p><strong>Title:</strong> {postTitle}</p>
          <p><strong>Post ID:</strong> {postId}</p>
          <p><strong>Comments Indexed:</strong> {commentCount}</p>
        </div>
      )}

      {/* Query Section (only show if postId exists) */}
      {postId && (
        <div style={{ marginTop: '20px', padding: '15px', border: '1px solid #ddd', backgroundColor: '#fafafa' }}>
          <h3>Ask a Question</h3>
          <form onSubmit={handleQuery}>
            <textarea
              placeholder="e.g., What do users dislike? What are the main concerns?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              rows={4}
              style={{ width: '100%', marginTop: '10px', padding: '8px' }}
              required
            />
            <button type="submit" disabled={loading} style={{ marginTop: '10px' }}>
              {loading ? 'Generating Insight...' : 'Generate Insight'}
            </button>
          </form>
        </div>
      )}

      {/* Answer Display */}
      {answer && (
        <div style={{ marginTop: '20px', padding: '10px', border: '1px solid #2196F3', backgroundColor: '#e3f2fd' }}>
          <h3>Insight:</h3>
          <p style={{ whiteSpace: 'pre-wrap' }}>{answer}</p>
        </div>
      )}
    </div>
  );
};

export default RedditAnalyzer;

