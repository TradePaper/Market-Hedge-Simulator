"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Page error:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-[#0d1117] flex items-center justify-center p-6">
      <div className="bg-[#161b22] border border-[#21262d] rounded-xl p-8 max-w-md w-full text-center">
        <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
          </svg>
        </div>
        <h2 className="text-white font-semibold text-lg mb-1">Something went wrong</h2>
        <p className="text-gray-500 text-sm mb-6">
          The dashboard encountered an error. This usually resolves itself — click below to reload.
        </p>
        <button
          onClick={() => window.location.reload()}
          className="w-full bg-[#238636] hover:bg-[#2ea043] text-white font-semibold text-sm py-2.5 rounded-lg transition-colors"
        >
          Reload Dashboard
        </button>
      </div>
    </div>
  );
}
