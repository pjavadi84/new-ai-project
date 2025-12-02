export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black px-6">
      <main className="w-full max-w-3xl rounded-2xl bg-white/90 p-10 shadow-xl ring-1 ring-gray-200 dark:bg-zinc-900 dark:ring-zinc-700">
        <p className="text-sm uppercase tracking-[0.2em] text-indigo-500">Status</p>
        <h1 className="mt-3 text-3xl font-bold text-gray-900 dark:text-white">
          Todo functionality removed
        </h1>
        <p className="mt-4 text-lg text-gray-700 leading-relaxed dark:text-gray-300">
          The previous task manager UI and API endpoints have been removed. This frontend is now a clean slate for the remaining document features.
        </p>
        <div className="mt-8 rounded-xl border border-dashed border-gray-300 bg-gray-50 p-6 dark:border-zinc-700 dark:bg-zinc-800">
          <p className="text-sm font-semibold text-gray-800 dark:text-gray-100">What changed?</p>
          <ul className="mt-3 space-y-2 text-gray-700 dark:text-gray-300">
            <li>• Task pages, components, and types were removed.</li>
            <li>• Task API routes were decommissioned on the backend.</li>
            <li>• You can repurpose this page for document workflows.</li>
          </ul>
        </div>
      </main>
    </div>
  );
}
