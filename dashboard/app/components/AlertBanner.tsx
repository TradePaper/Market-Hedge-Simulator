"use client";

import { EnrichedEvent } from "@/lib/mockData";
import { useState } from "react";

interface Props {
  alerts: EnrichedEvent[];
}

export default function AlertBanner({ alerts }: Props) {
  const [dismissed, setDismissed] = useState(false);

  if (alerts.length === 0 || dismissed) return null;

  return (
    <div className="flex items-start gap-3 px-4 py-3 rounded-lg border border-yellow-500/30 bg-yellow-500/10 text-yellow-300 text-sm mb-4">
      <svg className="w-5 h-5 mt-0.5 shrink-0 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
      </svg>
      <div className="flex-1">
        <span className="font-semibold text-yellow-200">Arbitrage Alert — </span>
        {alerts.length} event{alerts.length > 1 ? "s" : ""} exceed the 5% divergence threshold:{" "}
        {alerts.map((a, i) => (
          <span key={a.id}>
            <span className="font-mono font-semibold text-yellow-200">{a.event}</span>
            {" "}
            <span className="text-yellow-400/80">
              ({a.diff >= 0 ? "+" : ""}{(a.diff * 100).toFixed(1)} pp)
            </span>
            {i < alerts.length - 1 ? ", " : ""}
          </span>
        ))}
      </div>
      <button onClick={() => setDismissed(true)} className="text-yellow-400/60 hover:text-yellow-200 transition-colors shrink-0">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}
