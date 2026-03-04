"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { EnrichedEvent } from "@/lib/mockData";

interface Props {
  events: EnrichedEvent[];
}

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-[#1c2128] border border-[#30363d] rounded-lg p-3 text-xs shadow-xl">
      <p className="font-semibold text-white mb-1">{d.event}</p>
      <p className="text-gray-400">{d.league} · {d.sport}</p>
      <div className="mt-2 space-y-1">
        <p className="font-mono">
          <span className="text-gray-500">SB:  </span>
          <span className="text-[#58a6ff]">{(d.sbProb * 100).toFixed(1)}%</span>
        </p>
        <p className="font-mono">
          <span className="text-gray-500">MKT: </span>
          <span className="text-[#bc8cff]">{(d.marketProb * 100).toFixed(1)}%</span>
        </p>
        <p className="font-mono">
          <span className="text-gray-500">Δ:   </span>
          <span className={d.diff >= 0 ? "text-[#3fb950]" : "text-[#f85149]"}>
            {d.diff >= 0 ? "+" : ""}{(d.diff * 100).toFixed(2)} pp
          </span>
        </p>
      </div>
    </div>
  );
};

export default function DivergenceBar({ events }: Props) {
  const data = events
    .map((e) => ({ ...e, diffPct: parseFloat((e.diff * 100).toFixed(3)) }))
    .sort((a, b) => Math.abs(b.diffPct) - Math.abs(a.diffPct));

  const shortLabel = (ev: string) => {
    const parts = ev.split(" vs ");
    return parts[0].split(" ").at(-1) ?? ev;
  };

  return (
    <div className="bg-surface-card border border-surface-border rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-surface-border">
        <span className="text-sm font-semibold text-gray-300">Probability Divergence by Event</span>
        <p className="text-xs text-gray-500 mt-0.5">Market − Sportsbook (percentage points)</p>
      </div>
      <div className="p-4">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#21262d" vertical={false} />
            <XAxis
              dataKey="event"
              tick={{ fill: "#8b949e", fontSize: 11 }}
              tickFormatter={shortLabel}
              axisLine={{ stroke: "#21262d" }}
              tickLine={false}
            />
            <YAxis
              tickFormatter={(v) => `${v > 0 ? "+" : ""}${v.toFixed(1)}`}
              tick={{ fill: "#8b949e", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              unit=" pp"
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(88,166,255,0.05)" }} />
            <ReferenceLine y={0} stroke="#30363d" strokeWidth={1.5} />
            <ReferenceLine y={5} stroke="#d29922" strokeDasharray="4 4" strokeWidth={1} label={{ value: "+5%", fill: "#d29922", fontSize: 10 }} />
            <ReferenceLine y={-5} stroke="#d29922" strokeDasharray="4 4" strokeWidth={1} label={{ value: "−5%", fill: "#d29922", fontSize: 10 }} />
            <Bar dataKey="diffPct" radius={[3, 3, 0, 0]} maxBarSize={48}>
              {data.map((entry, i) => (
                <Cell
                  key={i}
                  fill={
                    Math.abs(entry.diffPct) > 5
                      ? "#d29922"
                      : entry.diffPct >= 0
                      ? "#3fb950"
                      : "#f85149"
                  }
                  fillOpacity={0.85}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
