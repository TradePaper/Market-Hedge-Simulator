import numpy as np
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import plotly.graph_objects as go
import json

app = FastAPI(title="Sportsbook Hedge Simulator")

app.mount("/static", StaticFiles(directory="static"), name="static")


class SimulationInput(BaseModel):
    exposure: float = Field(..., gt=0, description="Sportsbook exposure in USD")
    sportsbook_prob: float = Field(..., gt=0, lt=1, description="Sportsbook implied probability (0-1)")
    market_price: float = Field(..., gt=0, lt=1, description="Prediction market price per share (0-1)")
    liquidity: float = Field(..., gt=0, description="Prediction market liquidity in USD")


class SimulationOutput(BaseModel):
    optimal_hedge_size: float
    hedge_cost: float
    expected_profit: float
    worst_case_loss: float
    best_case_gain: float
    profit_percentiles: dict
    chart_json: str
    summary: dict


def run_monte_carlo(
    exposure: float,
    sportsbook_prob: float,
    market_price: float,
    liquidity: float,
    n_sims: int = 10_000,
) -> dict:
    rng = np.random.default_rng(seed=42)

    # Optimal hedge: size that minimises variance between the two outcomes.
    # If event occurs:   profit = hedge_size - exposure  (market pays hedge_size, book pays -exposure)
    # If event does not: profit = -hedge_cost             (just the cost of buying contracts)
    # Setting both equal => hedge_size - exposure = -market_price * hedge_size
    # => hedge_size * (1 + market_price) = exposure
    # => hedge_size = exposure / (1 + market_price)
    # But we are constrained by available liquidity.
    unconstrained_hedge = exposure / (1.0 + market_price)
    optimal_hedge = min(unconstrained_hedge, liquidity)
    hedge_cost = optimal_hedge * market_price

    # Simulate true event probability with uncertainty (±5 pp noise around sportsbook estimate)
    true_prob_samples = np.clip(
        rng.normal(loc=sportsbook_prob, scale=0.05, size=n_sims), 0.001, 0.999
    )

    # Simulate whether the event occurs in each trial
    event_occurs = rng.random(size=n_sims) < true_prob_samples

    # P&L per simulation
    # When event occurs:   market pays back hedge_size, book loses exposure
    # When no event:       market contracts expire worthless
    pnl = np.where(
        event_occurs,
        optimal_hedge - exposure - hedge_cost,   # net: received hedge_size, paid hedge_cost, paid exposure
        -hedge_cost,                              # net: only paid hedge_cost
    )

    percentiles = {
        "p1":  float(np.percentile(pnl, 1)),
        "p5":  float(np.percentile(pnl, 5)),
        "p25": float(np.percentile(pnl, 25)),
        "p50": float(np.percentile(pnl, 50)),
        "p75": float(np.percentile(pnl, 75)),
        "p95": float(np.percentile(pnl, 95)),
        "p99": float(np.percentile(pnl, 99)),
    }

    return {
        "pnl": pnl,
        "optimal_hedge": optimal_hedge,
        "hedge_cost": hedge_cost,
        "expected_profit": float(np.mean(pnl)),
        "worst_case_loss": float(np.min(pnl)),
        "best_case_gain": float(np.max(pnl)),
        "percentiles": percentiles,
        "event_rate": float(np.mean(event_occurs)),
    }


def build_chart(pnl: np.ndarray) -> str:
    fig = go.Figure()

    fig.add_trace(
        go.Histogram(
            x=pnl,
            nbinsx=80,
            marker_color="steelblue",
            opacity=0.85,
            name="Simulated P&L",
        )
    )

    mean_val = float(np.mean(pnl))
    p5_val = float(np.percentile(pnl, 5))

    fig.add_vline(
        x=mean_val,
        line_dash="dash",
        line_color="orange",
        annotation_text=f"Mean: ${mean_val:,.0f}",
        annotation_position="top right",
    )
    fig.add_vline(
        x=p5_val,
        line_dash="dot",
        line_color="red",
        annotation_text=f"5th pct: ${p5_val:,.0f}",
        annotation_position="top left",
    )

    fig.update_layout(
        title="Distribution of Hedge P&L (10,000 Simulations)",
        xaxis_title="Profit / Loss (USD)",
        yaxis_title="Frequency",
        bargap=0.05,
        template="plotly_white",
        font=dict(family="Inter, sans-serif", size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=30, t=60, b=50),
    )

    return fig.to_json()


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.post("/simulate", response_model=SimulationOutput)
async def simulate(params: SimulationInput):
    result = run_monte_carlo(
        exposure=params.exposure,
        sportsbook_prob=params.sportsbook_prob,
        market_price=params.market_price,
        liquidity=params.liquidity,
    )

    chart_json = build_chart(result["pnl"])

    summary = {
        "simulated_event_rate": round(result["event_rate"] * 100, 2),
        "hedge_coverage_pct": round(
            min(result["optimal_hedge"] / params.exposure, 1.0) * 100, 2
        ),
        "liquidity_constrained": result["optimal_hedge"] < (params.exposure / (1.0 + params.market_price)),
    }

    return SimulationOutput(
        optimal_hedge_size=round(result["optimal_hedge"], 2),
        hedge_cost=round(result["hedge_cost"], 2),
        expected_profit=round(result["expected_profit"], 2),
        worst_case_loss=round(result["worst_case_loss"], 2),
        best_case_gain=round(result["best_case_gain"], 2),
        profit_percentiles={k: round(v, 2) for k, v in result["percentiles"].items()},
        chart_json=chart_json,
        summary=summary,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
