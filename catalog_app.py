import sqlite3
import os
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn
import numpy as np
import plotly.graph_objects as go

os.makedirs("tmp", exist_ok=True)
DB_PATH = "tmp/contracts.db"

app = FastAPI(title="ProbEdge Research")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS contracts (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name       TEXT    NOT NULL,
                market_type      TEXT    NOT NULL CHECK(market_type IN ('binary','categorical')),
                oracle_source    TEXT    NOT NULL,
                settlement_rule  TEXT    NOT NULL,
                manipulation_risk TEXT  NOT NULL CHECK(manipulation_risk IN ('low','medium','high')),
                notes            TEXT,
                created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        existing = conn.execute("SELECT COUNT(*) FROM contracts").fetchone()[0]
        if existing == 0:
            seed = [
                (
                    "Super Bowl Winner",
                    "categorical",
                    "NFL official results (NFL.com)",
                    "Resolves YES for the team that wins Super Bowl LIX per official NFL records. "
                    "Categorical: one outcome per team. Settlement within 24 hours of final whistle.",
                    "low",
                    "Outcome determined by on-field play with thousands of independent observers. "
                    "Extremely difficult to manipulate. Major liquidity on Polymarket and Kalshi. "
                    "Single event per season — no replay risk.",
                ),
                (
                    "US Presidential Election Winner",
                    "categorical",
                    "Associated Press & major network calls; certified state results",
                    "Resolves to the candidate who receives a majority of Electoral College votes "
                    "as certified by Congress on Jan 6. Categorical market with one share per candidate. "
                    "Extended settlement window to accommodate certification.",
                    "medium",
                    "High-profile event with robust oracle sources. Medium risk due to potential "
                    "certification disputes (cf. Jan 2021) and litigation delays. Markets have "
                    "historically traded at compressed odds near resolution. Watch for regulatory "
                    "intervention — CFTC has previously challenged election contracts.",
                ),
                (
                    "Federal Reserve Rate Decision",
                    "binary",
                    "FOMC official statement (federalreserve.gov)",
                    "Resolves YES if the federal funds target rate is raised by ≥25 bps at the "
                    "scheduled FOMC meeting. Resolves NO otherwise (hold or cut). "
                    "Oracle: official Fed press release published same day as decision.",
                    "low",
                    "Binary contract with unambiguous settlement criteria. Oracle is the Fed itself — "
                    "no third-party interpretation needed. Rate decision is public and simultaneous. "
                    "Tight correlation with CME FedWatch tool provides natural price anchor. "
                    "Low manipulation risk: no individual actor can move Fed policy.",
                ),
                (
                    "Best Picture — Academy Awards",
                    "categorical",
                    "Academy of Motion Picture Arts and Sciences official announcement",
                    "Resolves to the film named Best Picture at the Academy Awards ceremony. "
                    "Categorical: one share per nominated film. Settlement at announcement, "
                    "typically late February/early March. No retroactive resolution.",
                    "high",
                    "High manipulation risk relative to other contracts. Voting body is ~10,000 "
                    "members — small enough that coordinated campaigns or early ballot leaks can "
                    "meaningfully shift true probabilities before markets reflect them. "
                    "Historical precedent: PricewaterhouseCoopers envelope incident (2017) shows "
                    "procedural error risk. Insider trading window between ballot close and ceremony "
                    "is a known concern. Recommend wide bid-ask spreads until final week.",
                ),
            ]
            conn.executemany(
                "INSERT INTO contracts (event_name, market_type, oracle_source, settlement_rule, manipulation_risk, notes) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                seed,
            )


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ContractIn(BaseModel):
    event_name: str
    market_type: str
    oracle_source: str
    settlement_rule: str
    manipulation_risk: str
    notes: Optional[str] = ""


class SimulationInput(BaseModel):
    exposure:        float = Field(..., gt=0)
    sportsbook_prob: float = Field(..., gt=0, lt=1)
    market_price:    float = Field(..., gt=0, lt=1)
    liquidity:       float = Field(..., gt=0)


class SimulationOutput(BaseModel):
    optimal_hedge_size:  float
    hedge_cost:          float
    expected_profit:     float
    worst_case_loss:     float
    best_case_gain:      float
    profit_percentiles:  dict
    chart_json:          str
    summary:             dict


# ---------------------------------------------------------------------------
# Monte Carlo simulation
# ---------------------------------------------------------------------------

def run_monte_carlo(exposure, sportsbook_prob, market_price, liquidity, n_sims=10_000):
    rng = np.random.default_rng(seed=42)
    unconstrained_hedge = exposure / (1.0 + market_price)
    optimal_hedge = min(unconstrained_hedge, liquidity)
    hedge_cost = optimal_hedge * market_price

    true_prob_samples = np.clip(
        rng.normal(loc=sportsbook_prob, scale=0.05, size=n_sims), 0.001, 0.999
    )
    event_occurs = rng.random(size=n_sims) < true_prob_samples

    pnl = np.where(
        event_occurs,
        optimal_hedge - exposure - hedge_cost,
        -hedge_cost,
    )

    return {
        "pnl":            pnl,
        "optimal_hedge":  optimal_hedge,
        "hedge_cost":     hedge_cost,
        "expected_profit": float(np.mean(pnl)),
        "worst_case_loss": float(np.min(pnl)),
        "best_case_gain":  float(np.max(pnl)),
        "percentiles": {
            "p1":  float(np.percentile(pnl, 1)),
            "p5":  float(np.percentile(pnl, 5)),
            "p25": float(np.percentile(pnl, 25)),
            "p50": float(np.percentile(pnl, 50)),
            "p75": float(np.percentile(pnl, 75)),
            "p95": float(np.percentile(pnl, 95)),
            "p99": float(np.percentile(pnl, 99)),
        },
        "event_rate": float(np.mean(event_occurs)),
    }


def build_chart(pnl):
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=pnl, nbinsx=80, marker_color="steelblue", opacity=0.85, name="Simulated P&L"))
    mean_val = float(np.mean(pnl))
    p5_val   = float(np.percentile(pnl, 5))
    fig.add_vline(x=mean_val, line_dash="dash",  line_color="orange", annotation_text=f"Mean: ${mean_val:,.0f}", annotation_position="top right")
    fig.add_vline(x=p5_val,   line_dash="dot",   line_color="red",    annotation_text=f"5th pct: ${p5_val:,.0f}", annotation_position="top left")
    fig.update_layout(
        title="Distribution of Hedge P&L (10,000 Simulations)",
        xaxis_title="Profit / Loss (USD)",
        yaxis_title="Frequency",
        bargap=0.05,
        template="plotly_white",
        font=dict(family="Inter, sans-serif", size=13),
        margin=dict(l=50, r=30, t=60, b=50),
    )
    return fig.to_json()


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index():
    return RedirectResponse(url="/event-markets")


@app.get("/event-markets", response_class=HTMLResponse)
def event_markets():
    with open("static/event-markets.html") as f:
        return f.read()


@app.get("/hedging-simulator", response_class=HTMLResponse)
def hedging_simulator():
    with open("static/index.html") as f:
        return f.read()


@app.get("/probability-gap", response_class=HTMLResponse)
def probability_gap():
    with open("static/probability-gap.html") as f:
        return f.read()


@app.get("/contract-library", response_class=HTMLResponse)
def contract_library():
    with open("static/catalog.html") as f:
        return f.read()


# ---------------------------------------------------------------------------
# API routes — contracts
# ---------------------------------------------------------------------------

@app.get("/api/contracts")
def list_contracts(q: Optional[str] = Query(None)):
    with get_db() as conn:
        if q and q.strip():
            like = f"%{q.strip()}%"
            rows = conn.execute(
                """SELECT id, event_name, market_type, oracle_source, manipulation_risk, created_at
                   FROM contracts
                   WHERE event_name LIKE ? OR oracle_source LIKE ? OR notes LIKE ? OR settlement_rule LIKE ?
                   ORDER BY id DESC""",
                (like, like, like, like),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT id, event_name, market_type, oracle_source, manipulation_risk, created_at
                   FROM contracts ORDER BY id DESC"""
            ).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/contracts/{contract_id}")
def get_contract(contract_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Contract not found")
    return dict(row)


@app.post("/api/contracts", status_code=201)
def create_contract(contract: ContractIn):
    if contract.market_type not in ("binary", "categorical"):
        raise HTTPException(status_code=422, detail="market_type must be binary or categorical")
    if contract.manipulation_risk not in ("low", "medium", "high"):
        raise HTTPException(status_code=422, detail="manipulation_risk must be low, medium, or high")
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO contracts (event_name, market_type, oracle_source, settlement_rule, manipulation_risk, notes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                contract.event_name.strip(),
                contract.market_type,
                contract.oracle_source.strip(),
                contract.settlement_rule.strip(),
                contract.manipulation_risk,
                (contract.notes or "").strip(),
            ),
        )
        new_id = cur.lastrowid
    return {"id": new_id, "message": "Contract created"}


@app.delete("/api/contracts/{contract_id}", status_code=204)
def delete_contract(contract_id: int):
    with get_db() as conn:
        result = conn.execute("DELETE FROM contracts WHERE id = ?", (contract_id,))
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Contract not found")


# ---------------------------------------------------------------------------
# API routes — simulation
# ---------------------------------------------------------------------------

@app.post("/simulate", response_model=SimulationOutput)
def simulate(params: SimulationInput):
    result = run_monte_carlo(
        exposure=params.exposure,
        sportsbook_prob=params.sportsbook_prob,
        market_price=params.market_price,
        liquidity=params.liquidity,
    )
    chart_json = build_chart(result["pnl"])
    summary = {
        "simulated_event_rate":  round(result["event_rate"] * 100, 2),
        "hedge_coverage_pct":    round(min(result["optimal_hedge"] / params.exposure, 1.0) * 100, 2),
        "liquidity_constrained": result["optimal_hedge"] < (params.exposure / (1.0 + params.market_price)),
    }
    return SimulationOutput(
        optimal_hedge_size=round(result["optimal_hedge"], 2),
        hedge_cost=round(result["hedge_cost"], 2),
        expected_profit=round(result["expected_profit"], 2),
        worst_case_loss=round(result["worst_case_loss"], 2),
        best_case_gain=round(result["best_case_gain"], 2),
        profit_percentiles=result["percentiles"],
        chart_json=chart_json,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

init_db()

if __name__ == "__main__":
    uvicorn.run("catalog_app:app", host="0.0.0.0", port=5000, reload=False)
