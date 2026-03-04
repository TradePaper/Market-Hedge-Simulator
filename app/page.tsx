import { enrichEvents, TIME_SERIES } from "@/lib/mockData";
import AlertBanner from "./components/AlertBanner";
import StatsBar from "./components/StatsBar";
import ProbabilityTable from "./components/ProbabilityTable";
import DivergenceBar from "./components/DivergenceBar";
import DivergenceTimeSeries from "./components/DivergenceTimeSeries";

export default function Dashboard() {
  const events = enrichEvents();
  const alerts = events.filter((e) => e.alert);

  return (
    <div className="min-h-screen bg-[#0d1117] text-white">
      <header className="border-b border-[#21262d] bg-[#0d1117]/95 backdrop-blur sticky top-0 z-10">
        <div className="max-w-screen-xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-sm font-bold text-white leading-none">ProbEdge</h1>
              <p className="text-[10px] text-gray-500 leading-none mt-0.5">Sportsbook vs Markets</p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 ml-2">
            <span className="text-[10px] text-gray-500 uppercase tracking-wider">Data:</span>
            <span className="px-1.5 py-0.5 rounded text-[10px] bg-[#161b22] border border-[#21262d] text-gray-400 font-mono">
              Mock — Simulated
            </span>
          </div>

          <div className="ml-auto flex items-center gap-3">
            {alerts.length > 0 && (
              <div className="flex items-center gap-1.5 text-yellow-400">
                <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
                <span className="text-xs font-semibold">{alerts.length} Alert{alerts.length > 1 ? "s" : ""}</span>
              </div>
            )}
            <div className="flex items-center gap-1.5 text-xs text-gray-500">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              Live
            </div>
            <span className="text-xs text-gray-600 font-mono hidden sm:block">
              {new Date().toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })}
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-screen-xl mx-auto px-4 sm:px-6 py-5 space-y-4">
        <AlertBanner alerts={alerts} />
        <StatsBar events={events} />
        <ProbabilityTable events={events} />

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
                  American odds are converted using:{" "}
                  <span className="font-mono text-gray-300">p = |odds| / (|odds| + 100)</span>{" "}
                  for favourites and{" "}
                  <span className="font-mono text-gray-300">p = 100 / (odds + 100)</span>{" "}
                  for underdogs.
                </p>
              </div>
            </div>
          </div>
        </div>

        <DivergenceTimeSeries data={TIME_SERIES} />

        <footer className="text-center text-xs text-gray-600 py-2">
          ProbEdge · Simulated data only · Not financial advice
        </footer>
      </main>
    </div>
  );
}
