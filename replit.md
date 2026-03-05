# ProbEdge Research — Multi-tool Prediction Market Suite

Four integrated tools for prediction market research, accessible via a shared navigation bar.

## Stack
- **Backend**: Python 3.11 + FastAPI + SQLite (`sqlite3`)
- **Frontend**: Vanilla HTML/CSS/JS served by FastAPI
- **Entry point**: `catalog_app.py`
- **Database**: `tmp/contracts.db` (SQLite, auto-created, WAL mode)
- **Simulation engine**: `simulator.py` (Monte Carlo, seeded RNG)
- **Provider layer**: `providers/` package (MockProvider, PolymarketProvider, KalshiProvider, CachedProvider)

## Workflow
```
uvicorn catalog_app:app --host 0.0.0.0 --port 5000
```

## Pages
| Route | File | Description |
|---|---|---|
| `/` | — | Redirects to `/event-markets` |
| `/event-markets` | `static/event-markets.html` | Contract card grid with risk/type filters and stats bar |
| `/hedging-simulator` | `static/index.html` | Monte Carlo hedge simulator with presets, validation, URL sharing |
| `/probability-gap` | `static/probability-gap.html` | Odds→prob gap analysis with live market feed (Mock/Polymarket/Kalshi) |
| `/contract-library` | `static/catalog.html` | Full contract catalog with search, detail view, add/delete |

## Shared Navigation
`static/nav.js` — injected into every page. Renders a sticky top nav, highlights the active route.

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/contracts` | List contracts (optional `?q=` search) |
| GET | `/api/contracts/{id}` | Single contract details |
| POST | `/api/contracts` | Create contract |
| DELETE | `/api/contracts/{id}` | Delete contract |
| POST | `/simulate` | Run Monte Carlo hedge simulation |
| GET | `/api/markets` | List markets (`?source=mock\|polymarket\|kalshi&limit=N`) |
| GET | `/api/markets/{event_id}` | Single market by ID (`?source=...`) |

## Provider Layer (`providers/`)
| File | Class | Description |
|------|-------|-------------|
| `base.py` | `MarketProvider` | Abstract interface: `get_markets()`, `get_prices()`, `get_timestamp()` |
| `base.py` | `MarketData`, `Outcome` | Normalized schema shared by all providers |
| `mock.py` | `MockProvider` | Five static sample markets; always available |
| `polymarket.py` | `PolymarketProvider` | Polymarket CLOB public API (no auth required); 2-retry + timeout |
| `kalshi.py` | `KalshiProvider` | Kalshi trading API; reads `KALSHI_API_KEY` env var if present |
| `cache.py` | `CachedProvider` | In-memory TTL wrapper (default 30s); serves stale data on provider error |

**Normalized schema fields:** `event_id`, `title`, `outcomes`, `price`, `implied_prob`, `source`, `updated_at`, `volume`, `end_date`

## Database Schema
```sql
contracts (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name       TEXT NOT NULL,
    market_type      TEXT NOT NULL,   -- 'binary' | 'categorical'
    oracle_source    TEXT NOT NULL,
    settlement_rule  TEXT NOT NULL,
    manipulation_risk TEXT NOT NULL,  -- 'low' | 'medium' | 'high'
    notes            TEXT,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## Simulator Inputs (`simulator.py`)
`stake`, `americanOdds`, `trueWinProb`, `hedgeFraction`, `fillProbability`, `slippageBps`, `feeBps`, `latencyBps`, `nPaths`, `seed`

## Tests
```
tests/test_simulator.py    — 3 tests: EV parity, determinism, slippage monotonicity
tests/test_providers.py    — 17 tests: schema mapping, mock, API failure fallback, cache TTL
```
Run with: `python3 -m pytest tests/ -v`

## Deployment
VM target. Production command:
```
gunicorn --bind=0.0.0.0:5000 --reuse-port --worker-class=uvicorn.workers.UvicornWorker --workers=2 catalog_app:app
```

## Notes
- `tmp/contracts.db` is gitignored; auto-seeded with 4 contracts on first run
- Polymarket CLOB base URL overridable via `POLYMARKET_API_BASE` env var
- Kalshi API base overridable via `KALSHI_API_BASE`; auth via `KALSHI_API_KEY`
