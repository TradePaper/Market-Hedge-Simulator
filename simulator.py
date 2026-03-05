import hashlib
import math
import numpy as np
import plotly.graph_objects as go
from pydantic import BaseModel, Field
from typing import List


# ---------------------------------------------------------------------------
# Input / Output models
# ---------------------------------------------------------------------------

class SimInput(BaseModel):
    stake:           float = Field(..., gt=0, description="Amount wagered on sportsbook (USD)")
    americanOdds:    float = Field(..., description="American odds (e.g. -110 or +150)")
    trueWinProb:     float = Field(..., gt=0, lt=1, description="Your estimate of true win probability (0-1)")
    hedgeFraction:   float = Field(..., ge=0, le=1, description="Fraction of optimal hedge to take (0=none, 1=full)")
    fillProbability: float = Field(..., ge=0, le=1, description="Probability hedge order fills at target price")
    slippageBps:     float = Field(..., ge=0, description="Market slippage in basis points")
    feeBps:          float = Field(..., ge=0, description="Transaction fee in basis points")
    latencyBps:      float = Field(..., ge=0, description="Adverse price movement due to latency (basis points)")
    nPaths:          int   = Field(default=10_000, ge=100, le=50_000, description="Number of Monte Carlo paths")
    seed:            int   = Field(default=42, description="RNG seed for reproducibility")


class SimOutput(BaseModel):
    ev:                float
    p5:                float
    p50:               float
    p95:               float
    maxLoss:           float
    breakEvenWinRate:  float
    paths:             List[float]
    chartJson:         str
    runId:             str
    optimalHedge:      float
    actualHedge:       float
    hedgeCost:         float


# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def american_to_payout_ratio(american_odds: float) -> float:
    """Return profit-per-unit-staked (e.g. -110 → 0.909, +150 → 1.50)."""
    if american_odds < 0:
        return 100.0 / (-american_odds)
    else:
        return american_odds / 100.0


def compute_breakeven(params: SimInput) -> float:
    """
    Analytical break-even win rate: the trueWinProb at which EV = 0.

    Model: bettor bets `stake` at `americanOdds`. Hedge leg buys NO contracts
    on a prediction market priced at trueWinProb (market is fairly priced).
    Friction (slippage + latency + fees) raises the cost of NO contracts.
    """
    pr = american_to_payout_ratio(params.americanOdds)
    payout_profit = params.stake * pr

    H_star = payout_profit + params.stake          # optimal NO contracts to equalize outcomes
    H = params.hedgeFraction * H_star

    # Effective price of NO contracts after friction
    eff_no_price = (1.0 - params.trueWinProb) * (
        1.0 + (params.slippageBps + params.latencyBps) / 10_000.0
    )
    total_cost = H * eff_no_price * (1.0 + params.feeBps / 10_000.0)

    f = params.fillProbability

    # Conditional EV on each outcome
    win_fill    = payout_profit - total_cost            # event occurs, hedge fills (NO expires 0)
    win_nofill  = payout_profit                         # event occurs, no fill
    lose_fill   = -params.stake + H - total_cost        # event doesn't occur, NO pays $1/contract
    lose_nofill = -params.stake                         # event doesn't occur, no fill

    A = f * win_fill   + (1.0 - f) * win_nofill        # weighted win EV
    B = f * lose_fill  + (1.0 - f) * lose_nofill       # weighted lose EV

    denom = B - A
    if abs(denom) < 1e-10:
        return float("nan")
    p_be = B / denom
    return float(max(0.0, min(1.0, p_be)))


# ---------------------------------------------------------------------------
# Monte Carlo engine
# ---------------------------------------------------------------------------

def run_simulation(params: SimInput) -> SimOutput:
    rng = np.random.default_rng(seed=params.seed)

    pr = american_to_payout_ratio(params.americanOdds)
    payout_profit = params.stake * pr

    H_star = payout_profit + params.stake
    H = params.hedgeFraction * H_star

    eff_no_price = (1.0 - params.trueWinProb) * (
        1.0 + (params.slippageBps + params.latencyBps) / 10_000.0
    )
    total_cost = H * eff_no_price * (1.0 + params.feeBps / 10_000.0)

    event_occurs  = rng.random(params.nPaths) < params.trueWinProb
    hedge_fills   = rng.random(params.nPaths) < params.fillProbability

    sb_pnl = np.where(event_occurs, payout_profit, -params.stake)

    # If hedge fills:
    #   event occurs  → NO contracts expire worthless → market_pnl = -total_cost
    #   event doesn't → NO contracts pay $1 each    → market_pnl = H - total_cost
    market_pnl_filled = np.where(event_occurs, -total_cost, H - total_cost)
    market_pnl = np.where(hedge_fills, market_pnl_filled, 0.0)

    pnl = sb_pnl + market_pnl

    ev       = float(np.mean(pnl))
    p5       = float(np.percentile(pnl, 5))
    p50      = float(np.percentile(pnl, 50))
    p95      = float(np.percentile(pnl, 95))
    max_loss = float(np.min(pnl))

    breakeven = compute_breakeven(params)
    if math.isnan(breakeven):
        breakeven = 0.0

    sample_size = min(1_000, params.nPaths)
    sample_idx = rng.choice(params.nPaths, size=sample_size, replace=False)
    sampled_paths = [round(float(v), 2) for v in pnl[sample_idx]]

    chart_json = _build_chart(pnl)
    run_id = _run_id(params)

    return SimOutput(
        ev=round(ev, 2),
        p5=round(p5, 2),
        p50=round(p50, 2),
        p95=round(p95, 2),
        maxLoss=round(max_loss, 2),
        breakEvenWinRate=round(breakeven, 4),
        paths=sampled_paths,
        chartJson=chart_json,
        runId=run_id,
        optimalHedge=round(H_star, 2),
        actualHedge=round(H, 2),
        hedgeCost=round(total_cost, 2),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_chart(pnl: np.ndarray) -> str:
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=pnl.tolist(),
        nbinsx=80,
        marker_color="#3b82f6",
        opacity=0.82,
        name="Simulated P&L",
    ))
    mean_val = float(np.mean(pnl))
    p5_val   = float(np.percentile(pnl, 5))
    fig.add_vline(
        x=mean_val, line_dash="dash", line_color="#f59e0b",
        annotation_text=f"EV: ${mean_val:,.0f}",
        annotation_position="top right",
    )
    fig.add_vline(
        x=p5_val, line_dash="dot", line_color="#ef4444",
        annotation_text=f"p5: ${p5_val:,.0f}",
        annotation_position="top left",
    )
    fig.update_layout(
        title="P&L Distribution (Monte Carlo)",
        xaxis_title="Profit / Loss (USD)",
        yaxis_title="Frequency",
        bargap=0.05,
        paper_bgcolor="#0d1520",
        plot_bgcolor="#0d1520",
        font=dict(color="#8899aa", family="Courier New, monospace", size=11),
        xaxis=dict(gridcolor="#1a2840", zerolinecolor="#243350"),
        yaxis=dict(gridcolor="#1a2840"),
        margin=dict(l=50, r=30, t=50, b=50),
    )
    return fig.to_json()


def _run_id(params: SimInput) -> str:
    key = (
        f"{params.seed}:{params.stake}:{params.americanOdds}:{params.trueWinProb}:"
        f"{params.hedgeFraction}:{params.fillProbability}:{params.slippageBps}:"
        f"{params.feeBps}:{params.latencyBps}:{params.nPaths}"
    )
    return hashlib.md5(key.encode()).hexdigest()[:8].upper()
