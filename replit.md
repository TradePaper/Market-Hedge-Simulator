# Sportsbook Hedge Simulator

A FastAPI web application that simulates how a sportsbook can hedge risk using prediction markets, powered by Monte Carlo simulation (10,000 runs).

## Architecture

- **Backend**: FastAPI (`app.py`) served via Uvicorn on port 5000
- **Frontend**: Single-page HTML (`static/index.html`) with Plotly for charting
- **Simulation**: NumPy-based Monte Carlo engine in `app.py`

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | FastAPI app, simulation logic, `/simulate` POST endpoint |
| `static/index.html` | HTML/JS frontend with parameter inputs and Plotly chart |

## API Endpoint

`POST /simulate`

**Input (JSON):**
- `exposure` — Sportsbook payout liability in USD
- `sportsbook_prob` — Implied probability from the book (0–1)
- `market_price` — Prediction market contract price (0–1)
- `liquidity` — Max hedge size available in the market (USD)

**Output (JSON):**
- `optimal_hedge_size` — Variance-minimising hedge, capped at liquidity
- `hedge_cost` — Upfront premium: `hedge_size × market_price`
- `expected_profit` — Mean P&L across 10,000 simulations
- `worst_case_loss` — Minimum simulated P&L
- `best_case_gain` — Maximum simulated P&L
- `profit_percentiles` — p1/p5/p25/p50/p75/p95/p99
- `chart_json` — Plotly figure JSON for the histogram
- `summary` — Coverage %, liquidity constraint flag, simulated event rate

## Simulation Assumptions

- Sportsbook pays `exposure` when event occurs
- Prediction market pays back `hedge_size` when event occurs
- Hedge cost = `hedge_size × market_price` (paid upfront regardless)
- True event probability is sampled with ±5 pp Gaussian noise around `sportsbook_prob`
- Optimal hedge formula: `hedge_size = exposure / (1 + market_price)` (variance-minimising), constrained by `liquidity`

## Workflow

```
uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

## Dependencies

- fastapi, uvicorn — web server
- numpy — Monte Carlo simulation
- plotly — chart serialisation
