# Sports Probability Platform

Two tools for analysing and hedging sports event risk:

1. **Hedge Simulator** — FastAPI + Monte Carlo engine (Python, port 5000 when active)
2. **ProbEdge Dashboard** — Next.js probability comparison dashboard (currently running on port 5000)

---

## ProbEdge Dashboard (Next.js — active)

A financial-market-style dashboard that compares sportsbook implied probabilities against prediction market prices for 8 live sports events.

### Stack
- **Framework**: Next.js 14 (App Router, TypeScript)
- **Styling**: Tailwind CSS v4 + `@tailwindcss/postcss`
- **Charts**: Recharts
- **Data**: Mock/simulated in `lib/mockData.ts`

### Key Files

| File | Purpose |
|------|---------|
| `app/page.tsx` | Main dashboard page (server component) |
| `app/layout.tsx` | Root layout + metadata |
| `app/globals.css` | Tailwind v4 import + theme variables |
| `app/components/AlertBanner.tsx` | Dismissable yellow alert for >5% divergence |
| `app/components/StatsBar.tsx` | 4 headline stat cards |
| `app/components/ProbabilityTable.tsx` | Sortable 8-event table with probability bars |
| `app/components/ChartsWrapper.tsx` | Client wrapper: dynamic-imports both chart components with `ssr: false` |
| `app/components/ClientDate.tsx` | `ClientDate` + `ClientTime` client components (fix SSR hydration) |
| `app/components/DivergenceBar.tsx` | Recharts bar chart of divergence per event |
| `app/components/DivergenceTimeSeries.tsx` | Recharts 24h line chart with event toggles |
| `lib/mockData.ts` | Mock events, odds conversion, time-series generation |

### Features
- **American odds → implied probability**: `p = |odds|/(|odds|+100)` for favourites; `p = 100/(odds+100)` for underdogs
- **Divergence alert**: badges and banner fire when `|market_prob − sb_prob| > 0.05`
- **Sortable table**: click any column header to sort ascending/descending
- **Time series**: deterministic 24h divergence simulation; click legend to show/hide lines
- **Bar chart**: sorted by absolute divergence; yellow bars = alert threshold exceeded

### Workflow
```
next start -p 5000 -H 0.0.0.0
```
Serves the pre-built `.next` output. Production mode only — no file watching, no HMR, instant
startup (~260ms). The `.next` build artifact is committed to the repo so the server can start
without running `next build` on every restart.

To rebuild after code changes, run this once via shell:
```
NODE_OPTIONS='--max-old-space-size=2048' next build
```

**Known issues fixed:**
- Webpack WasmHash crash: set `hashFunction: "sha256"` in webpack config + `cache: false`
- CSS @import ordering: Google Fonts `@import url()` moved before `@import "tailwindcss"` in `globals.css`
- SSR hydration mismatch: all `new Date()` calls moved to client-only components (`ClientDate`, `ClientTime`)
- Recharts SSR crash: both chart components loaded via `next/dynamic` with `ssr: false`
- Fast Refresh "module sharing" loop: all client-component imports from `mockData.ts` are either
  `import type` (erased at build) or data threaded as props so no client chunk imports `mockData.ts`

---

## Hedge Simulator (FastAPI — background)

Monte Carlo sportsbook hedge calculator. Files remain in the repo but the workflow currently runs Next.js.

| File | Purpose |
|------|---------|
| `app.py` | FastAPI app + `/simulate` POST endpoint |
| `static/index.html` | HTML/Plotly frontend |

To run it separately: `uvicorn app:app --host 0.0.0.0 --port 5000 --reload`

---

## Dependencies

### Node.js
- next, react, react-dom, recharts, clsx
- tailwindcss v4, @tailwindcss/postcss, postcss, autoprefixer
- typescript, @types/node, @types/react, @types/react-dom

### Python
- fastapi, uvicorn, numpy, plotly, streamlit
