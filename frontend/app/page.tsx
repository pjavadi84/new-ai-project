// pages/page.tsx or app/page.tsx (depending on your Next.js version)

import DocumentUploader from './components/DocumentUploader';
import RAGQuery from './components/RAGQuery';
import RedditAnalyzer from './components/RedditAnalyzer';

export default function Home() {
  return (
    // Outer container with background and centering
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black px-6">
      {/* Main content container with fixed width and styling */}
      <main className="w-full max-w-3xl rounded-2xl bg-white/90 p-10 shadow-xl ring-1 ring-gray-200 dark:bg-zinc-900 dark:ring-zinc-700">
        
        {/* --- Header --- */}
        <p className="text-sm uppercase tracking-[0.2em] text-indigo-500">
          RAG Demo Status: Active
        </p>
        <h1 className="mt-3 text-3xl font-bold text-gray-900 dark:text-white">
          Document Q&A Pipeline
        </h1>
        <p className="mt-4 text-lg text-gray-700 leading-relaxed dark:text-gray-300">
          Upload a PDF to index it using **HuggingFace Embeddings**, then query it using the local **Llama 2 LLM (via Ollama)**.
        </p>
        
        <hr className="my-6 border-zinc-200 dark:border-zinc-700" />
        
        {/* --- 1. Document Upload Component --- */}
        <div className="mb-8 p-4 border rounded-xl border-gray-200 dark:border-zinc-700">
           <DocumentUploader />
        </div>

        <hr className="my-6 border-zinc-200 dark:border-zinc-700" />

        {/* --- 2. Query Component --- */}
        <div className="p-4 border rounded-xl border-gray-200 dark:border-zinc-700">
          <RAGQuery />
        </div>

        <hr className="my-6 border-zinc-200 dark:border-zinc-700" />

        {/* --- 3. Reddit Analyzer Component --- */}
        <div className="p-4 border rounded-xl border-gray-200 dark:border-zinc-700">
          <RedditAnalyzer />
        </div>

        {/* --- Footer Note --- */}
        <div className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
          <p>Ensure your **Django Backend**, **Ollama Application**, and **Reddit API credentials** are configured before testing.</p>
        </div>
      </main>
    </div>
  );
}