import sqlite3
import os
import dataclasses
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import uvicorn

from simulator import SimInput, run_simulation
from providers import MockProvider, PolymarketProvider, KalshiProvider, CachedProvider
from core.types_v12 import SimulationInputV12, LiquidityModel, InternalRepriceModel
from core.strategies import simulate_strategy
from core.optimizer import optimize_hedge_ratio, build_risk_transfer_curve

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
                    "Super Bowl Winner", "categorical",
                    "NFL official results (NFL.com)",
                    "Resolves YES for the team that wins Super Bowl LIX per official NFL records. "
                    "Categorical: one outcome per team. Settlement within 24 hours of final whistle.",
                    "low",
                    "Outcome determined by on-field play with thousands of independent observers. "
                    "Extremely difficult to manipulate. Major liquidity on Polymarket and Kalshi.",
                ),
                (
                    "US Presidential Election Winner", "categorical",
                    "Associated Press & major network calls; certified state results",
                    "Resolves to the candidate who receives a majority of Electoral College votes "
                    "as certified by Congress on Jan 6.",
                    "medium",
                    "High-profile event with robust oracle sources. Medium risk due to potential "
                    "certification disputes and litigation delays.",
                ),
                (
                    "Federal Reserve Rate Decision", "binary",
                    "FOMC official statement (federalreserve.gov)",
                    "Resolves YES if the federal funds target rate is raised by ≥25 bps at the "
                    "scheduled FOMC meeting. Resolves NO otherwise.",
                    "low",
                    "Binary contract with unambiguous settlement criteria. Oracle is the Fed itself.",
                ),
                (
                    "Best Picture — Academy Awards", "categorical",
                    "Academy of Motion Picture Arts and Sciences official announcement",
                    "Resolves to the film named Best Picture at the Academy Awards ceremony.",
                    "high",
                    "High manipulation risk. Voting body is ~10,000 members — small enough that "
                    "coordinated campaigns can shift probabilities.",
                ),
            ]
            conn.executemany(
                "INSERT INTO contracts (event_name, market_type, oracle_source, settlement_rule, manipulation_risk, notes) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                seed,
            )


# ---------------------------------------------------------------------------
# Contract model
# ---------------------------------------------------------------------------

class ContractIn(BaseModel):
    event_name: str
    market_type: str
    oracle_source: str
    settlement_rule: str
    manipulation_risk: str
    notes: Optional[str] = ""


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
# API — contracts
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
                "SELECT id, event_name, market_type, oracle_source, manipulation_risk, created_at "
                "FROM contracts ORDER BY id DESC"
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
                contract.event_name.strip(), contract.market_type,
                contract.oracle_source.strip(), contract.settlement_rule.strip(),
                contract.manipulation_risk, (contract.notes or "").strip(),
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
# API — simulation
# ---------------------------------------------------------------------------

@app.post("/simulate")
def simulate(params: SimInput):
    return run_simulation(params)


class LiquidityModelIn(BaseModel):
    available_liquidity: float
    participation_rate: float
    impact_factor: float
    depth_exponent: float = 1.0


class InternalRepriceModelIn(BaseModel):
    enabled: bool
    odds_move_sensitivity: float
    handle_retention_decay: float
    min_prob: float = 0.01
    max_prob: float = 0.99


class SimulateV12In(BaseModel):
    stake: float
    american_odds: int
    true_win_prob: float
    hedge_fraction: float = 0.5
    fill_probability: float = 1.0
    slippage_bps: float = 20.0
    fee_bps: float = 10.0
    latency_bps: float = 5.0
    n_paths: int = 5000
    seed: Optional[str] = None
    liability: float = 0.0
    strategy: str = "external_hedge"
    objective: str = "min_cvar"
    optimize: bool = False
    liquidity: Optional[LiquidityModelIn] = None
    internal_reprice: Optional[InternalRepriceModelIn] = None

    class Config:
        extra = "ignore"


class RiskCurveIn(BaseModel):
    base: SimulateV12In
    liabilities: list
    strategy: str = "external_hedge"


@app.post("/simulate/v12")
def simulate_v12(params: SimulateV12In):
    liq = (
        LiquidityModel(**params.liquidity.dict())
        if params.liquidity else None
    )
    reprice = (
        InternalRepriceModel(**params.internal_reprice.dict())
        if params.internal_reprice else None
    )
    inp = SimulationInputV12(
        stake=params.stake,
        american_odds=params.american_odds,
        true_win_prob=params.true_win_prob,
        hedge_fraction=params.hedge_fraction,
        fill_probability=params.fill_probability,
        slippage_bps=params.slippage_bps,
        fee_bps=params.fee_bps,
        latency_bps=params.latency_bps,
        n_paths=params.n_paths,
        seed=params.seed,
        liability=params.liability,
        strategy=params.strategy,
        objective=params.objective,
        liquidity=liq,
        internal_reprice=reprice,
    )
    if params.optimize:
        metrics = optimize_hedge_ratio(inp)
    else:
        metrics = simulate_strategy(inp)
    return dataclasses.asdict(metrics)


@app.post("/simulate/v12/curve")
def simulate_v12_curve(params: RiskCurveIn):
    base = params.base
    liq = LiquidityModel(**base.liquidity.dict()) if base.liquidity else None
    reprice = InternalRepriceModel(**base.internal_reprice.dict()) if base.internal_reprice else None
    inp = SimulationInputV12(
        stake=base.stake,
        american_odds=base.american_odds,
        true_win_prob=base.true_win_prob,
        hedge_fraction=base.hedge_fraction,
        fill_probability=base.fill_probability,
        slippage_bps=base.slippage_bps,
        fee_bps=base.fee_bps,
        latency_bps=base.latency_bps,
        n_paths=base.n_paths,
        seed=base.seed,
        liability=base.liability,
        strategy=base.strategy,
        objective=base.objective,
        liquidity=liq,
        internal_reprice=reprice,
    )
    sorted_liabilities = sorted(float(x) for x in params.liabilities)
    curve = build_risk_transfer_curve(inp, sorted_liabilities, params.strategy)
    assert len(curve.points) == len(sorted_liabilities)
    return {
        "strategy": curve.strategy,
        "liabilities_requested": len(sorted_liabilities),
        "points": [dataclasses.asdict(pt) for pt in curve.points],
    }


# ---------------------------------------------------------------------------
# Market providers
# ---------------------------------------------------------------------------

_PROVIDERS = {
    "mock":       CachedProvider(MockProvider(),        ttl=30),
    "polymarket": CachedProvider(PolymarketProvider(),  ttl=30),
    "kalshi":     CachedProvider(KalshiProvider(),      ttl=30),
}


@app.get("/api/markets")
def list_markets(
    source: str = Query("mock", pattern="^(mock|polymarket|kalshi)$"),
    limit: int  = Query(20, ge=1, le=100),
):
    provider = _PROVIDERS[source]
    try:
        markets = provider.get_markets(limit=limit)
    except Exception as exc:
        fallback = _PROVIDERS["mock"].get_markets(limit=limit)
        return {
            "source": "mock",
            "fallback": True,
            "error": str(exc),
            "updated_at": _PROVIDERS["mock"].get_timestamp(),
            "markets": [dataclasses.asdict(m) for m in fallback],
        }
    return {
        "source": source,
        "fallback": False,
        "error": None,
        "updated_at": provider.get_timestamp(),
        "markets": [dataclasses.asdict(m) for m in markets],
    }


@app.get("/api/markets/{event_id}")
def get_market(
    event_id: str,
    source: str = Query("mock", pattern="^(mock|polymarket|kalshi)$"),
):
    provider = _PROVIDERS[source]
    try:
        market = provider.get_prices(event_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Provider error: {exc}")
    if market is None:
        raise HTTPException(status_code=404, detail="Market not found")
    return dataclasses.asdict(market)


@app.get("/api/providers/health")
def providers_health():
    return {
        name: dataclasses.asdict(provider.health)
        for name, provider in _PROVIDERS.items()
    }


@app.get("/api/config")
def app_config():
    return {
        "posthogKey": os.environ.get("POSTHOG_KEY", ""),
    }


@app.get("/status")
def status():
    health = {
        name: dataclasses.asdict(provider.health)
        for name, provider in _PROVIDERS.items()
    }
    overall = "ok"
    for h in health.values():
        if h["status"] == "down":
            overall = "down"
            break
        if h["status"] == "degraded":
            overall = "degraded"
    return {
        "status": overall,
        "providers": health,
        "analytics": bool(os.environ.get("POSTHOG_KEY")),
        "version": "1.1.0",
    }


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

init_db()

if __name__ == "__main__":
    uvicorn.run("catalog_app:app", host="0.0.0.0", port=5000, reload=False)
