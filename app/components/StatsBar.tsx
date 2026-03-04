import { EnrichedEvent } from "@/lib/mockData";

interface Props {
  events: EnrichedEvent[];
}

function StatCard({
  label,
  value,
  sub,
  highlight,
}: {
  label: string;
  value: string;
  sub?: string;
  highlight?: "green" | "red" | "yellow" | "blue";
}) {
  const colors: Record<string, string> = {
    green:  "text-[#3fb950]",
    red:    "text-[#f85149]",
    yellow: "text-[#d29922]",
    blue:   "text-[#58a6ff]",
  };
  return (
    <div className="bg-[#161b22] border border-[#21262d] rounded-lg px-4 py-3 flex flex-col gap-0.5 min-w-0">
      <span className="text-xs text-gray-500 uppercase tracking-widest font-medium">{label}</span>
      <span className={`text-xl font-bold font-mono ${highlight ? colors[highlight] : "text-white"}`}>
        {value}
      </span>
      {sub && <span className="text-xs text-gray-500">{sub}</span>}
    </div>
  );
}

export default function StatsBar({ events }: Props) {
  const alerts = events.filter((e) => e.alert);
  const avgDiff = events.reduce((s, e) => s + Math.abs(e.diff), 0) / events.length;
  const maxDiff = events.reduce((m, e) => (Math.abs(e.diff) > Math.abs(m.diff) ? e : m));

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
      <StatCard
        label="Active Events"
        value={String(events.length)}
        sub="Across 7 sports"
        highlight="blue"
      />
      <StatCard
        label="Divergence Alerts"
        value={String(alerts.length)}
        sub="> 5% threshold"
        highlight={alerts.length > 0 ? "yellow" : "green"}
      />
      <StatCard
        label="Avg Abs Divergence"
        value={`${(avgDiff * 100).toFixed(2)} pp`}
        sub="Market vs Sportsbook"
        highlight={avgDiff > 0.05 ? "red" : "green"}
      />
      <StatCard
        label="Most Divergent"
        value={maxDiff.event.split(" vs ")[0]}
        sub={`${(Math.abs(maxDiff.diff) * 100).toFixed(1)} pp spread`}
        highlight="yellow"
      />
    </div>
  );
}
