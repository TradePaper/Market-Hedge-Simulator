"use client";

import dynamic from "next/dynamic";
import { EnrichedEvent, TimePoint } from "@/lib/mockData";

const DivergenceBar = dynamic(() => import("./DivergenceBar"), {
  ssr: false,
  loading: () => (
    <div className="bg-[#161b22] border border-[#21262d] rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-[#21262d]">
        <span className="text-sm font-semibold text-gray-300">Probability Divergence by Event</span>
      </div>
      <div className="p-4 h-[300px] flex items-center justify-center">
        <span className="text-gray-600 text-sm animate-pulse">Loading chart…</span>
      </div>
    </div>
  ),
});

const DivergenceTimeSeries = dynamic(() => import("./DivergenceTimeSeries"), {
  ssr: false,
  loading: () => (
    <div className="bg-[#161b22] border border-[#21262d] rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-[#21262d]">
        <span className="text-sm font-semibold text-gray-300">Divergence Over Time (24h)</span>
      </div>
      <div className="p-4 h-[340px] flex items-center justify-center">
        <span className="text-gray-600 text-sm animate-pulse">Loading chart…</span>
      </div>
    </div>
  ),
});

interface Props {
  events: EnrichedEvent[];
  timeSeries: TimePoint[];
}

export default function ChartsWrapper({ events, timeSeries }: Props) {
  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <DivergenceBar events={events} />
        <div className="bg-[#161b22] border border-[#21262d] rounded-lg p-4">
          <h2 className="text-sm font-semibold text-gray-300 mb-1">How to Read This Dashboard</h2>
          <p className="text-xs text-gray-500 mb-3">
            Divergence is calculated as{" "}
            <span className="font-mono text-gray-300">Market Prob − Sportsbook Implied Prob</span>.
            Positive values mean the market assigns a higher probability than the sportsbook.
          </p>
          <div className="space-y-2">
            {[
              { color: "#3fb950", label: "Green bar",  desc: "Market probability higher than sportsbook (potential underlay)" },
              { color: "#f85149", label: "Red bar",    desc: "Market probability lower than sportsbook (potential overlay)" },
              { color: "#d29922", label: "Yellow bar", desc: "Divergence exceeds 5% threshold — arbitrage alert" },
            ].map((item) => (
              <div key={item.label} className="flex items-start gap-2.5">
                <span className="w-2.5 h-2.5 rounded-sm mt-0.5 shrink-0" style={{ backgroundColor: item.color }} />
                <p className="text-xs text-gray-400">
                  <span className="text-gray-300 font-medium">{item.label}: </span>
                  {item.desc}
                </p>
              </div>
            ))}
            <div className="mt-3 pt-3 border-t border-[#21262d]">
              <p className="text-xs text-gray-500">
                American odds converted using{" "}
                <span className="font-mono text-gray-300">p = |odds| / (|odds| + 100)</span>{" "}
                for favourites and{" "}
                <span className="font-mono text-gray-300">p = 100 / (odds + 100)</span>{" "}
                for underdogs.
              </p>
            </div>
          </div>
        </div>
      </div>

      <DivergenceTimeSeries data={timeSeries} />
    </>
  );
}
