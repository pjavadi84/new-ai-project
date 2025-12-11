import Link from 'next/link';

export default function PrivacyPolicy() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black px-6">
      <main className="w-full max-w-3xl rounded-2xl bg-white/90 p-10 shadow-xl ring-1 ring-gray-200 dark:bg-zinc-900 dark:ring-zinc-700">
        <Link href="/" className="text-indigo-500 hover:text-indigo-700 mb-4 inline-block">
          ← Back to Home
        </Link>
        
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">
          Privacy Policy
        </h1>

        <div className="prose prose-gray dark:prose-invert max-w-none">
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Data Handling</h2>
            <p className="mb-4">
              This application processes discussion post data temporarily for analysis purposes only.
            </p>

            <h3 className="text-xl font-semibold mb-3">Key Points:</h3>
            <ul className="list-disc pl-6 space-y-2 mb-6">
              <li>
                <strong>No Permanent Storage</strong>: Discussion data is not stored permanently. 
                Data is processed in memory and discarded after analysis.
              </li>
              <li>
                <strong>No Data Sharing</strong>: We do not share, sell, or distribute any processed 
                data to third parties.
              </li>
              <li>
                <strong>No AI Training</strong>: Data is not used to train, improve, modify, or fine-tune 
                any AI models, machine learning systems, or natural language processing models.
              </li>
              <li>
                <strong>Temporary Processing</strong>: Data is only held in memory during the active 
                analysis session and is immediately discarded afterward.
              </li>
              <li>
                <strong>User Privacy</strong>: User identifiers (usernames) are anonymized during 
                processing and only displayed in final attribution with user consent.
              </li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Contact</h2>
            <p>
              For questions about this privacy policy, please contact [your contact information].
            </p>
          </section>

          <hr className="my-6 border-zinc-200 dark:border-zinc-700" />
          
          <p className="text-sm text-gray-500 dark:text-gray-400 italic">
            Last updated: [Date]
          </p>
        </div>
      </main>
    </div>
  );
}

