# Replit Project

## Current Application: ProbEdge Research — Multi-tool Prediction Market Suite

Four integrated tools for prediction market research, accessible via a shared navigation bar.

### Stack
- **Backend**: Python 3.11 + FastAPI + SQLite (standard library `sqlite3`)
- **Frontend**: Single-page vanilla HTML/CSS/JS served by FastAPI
- **Entry point**: `catalog_app.py`
- **Database**: `contracts.db` (SQLite, auto-created on first run)
- **Static files**: `static/catalog.html`

### Workflow
```
uvicorn catalog_app:app --host 0.0.0.0 --port 5000
```

### Database Schema

```sql
contracts (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name       TEXT NOT NULL,
    market_type      TEXT NOT NULL  -- 'binary' | 'categorical'
    oracle_source    TEXT NOT NULL,
    settlement_rule  TEXT NOT NULL,
    manipulation_risk TEXT NOT NULL -- 'low' | 'medium' | 'high'
    notes            TEXT,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Pages
| Route | File | Description |
|---|---|---|
| `/` | — | Redirects to `/event-markets` |
| `/event-markets` | `static/event-markets.html` | Contract card grid with risk/type filters and stats bar |
| `/hedging-simulator` | `static/index.html` | Monte Carlo hedge simulator (10k runs, Plotly chart) |
| `/probability-gap` | `static/probability-gap.html` | American odds → implied prob vs market price gap analysis |
| `/contract-library` | `static/catalog.html` | Full contract catalog with search, detail view, add/delete |

### Shared Navigation
`static/nav.js` — injected into every page via `<script src="/static/nav.js">`. Renders a sticky top nav, highlights the active route, and maintains consistent styling across pages.

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Serves the single-page UI |
| GET | `/api/contracts` | List all contracts (optional `?q=` search) |
| GET | `/api/contracts/{id}` | Get single contract details |
| POST | `/api/contracts` | Create a new contract (JSON body) |
| DELETE | `/api/contracts/{id}` | Delete a contract |

### Seed Data
Four contracts are seeded on first run if the database is empty:
- Super Bowl Winner (categorical, low risk)
- US Presidential Election Winner (categorical, medium risk)
- Federal Reserve Rate Decision (binary, low risk)
- Best Picture — Academy Awards (categorical, high risk)

---

## Archived: ProbEdge — Sportsbook vs Markets Dashboard (Next.js)

Previously the active app; now deployed as a standalone production build.
Source files remain in the repo: `app/`, `lib/`, `next.config.js`, etc.
Build output: `tmp/nextbuild/` (gitignored).

## Archived: Hedge Simulator (FastAPI)

Monte Carlo hedge calculator. Entry point: `app.py`. Static UI: `static/index.html`.
Not currently served by the workflow.
