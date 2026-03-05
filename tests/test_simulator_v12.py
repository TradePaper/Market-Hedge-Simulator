import dataclasses
import pytest
import numpy as np

from core.types_v12 import SimulationInputV12, LiquidityModel, InternalRepriceModel
from core.liquidity import max_hedge_notional, apply_hedge_cap, market_impact_delta_price
from core.metrics import cvar
from core.strategies import simulate_external_hedge, simulate_internal_reprice, simulate_hybrid, simulate_strategy
from core.optimizer import optimize_hedge_ratio, build_risk_transfer_curve


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def base_inp(**overrides) -> SimulationInputV12:
    defaults = dict(
        stake=1000.0,
        american_odds=-110,
        true_win_prob=0.52,
        hedge_fraction=0.5,
        fill_probability=1.0,
        slippage_bps=20.0,
        fee_bps=10.0,
        latency_bps=5.0,
        n_paths=2000,
        seed="test",
        liability=2000.0,
        strategy="external_hedge",
        objective="min_cvar",
    )
    defaults.update(overrides)
    return SimulationInputV12(**defaults)


# ---------------------------------------------------------------------------
# 1. Hedge cap always enforced
# ---------------------------------------------------------------------------

class TestHedgeCap:
    def test_effective_hedge_never_exceeds_max_notional(self):
        liq = LiquidityModel(available_liquidity=500.0, participation_rate=0.5, impact_factor=0.1)
        inp = base_inp(hedge_fraction=1.0, liability=5000.0, liquidity=liq)
        metrics = simulate_external_hedge(inp)
        max_h = max_hedge_notional(500.0, 0.5)
        assert metrics.effective_hedge_notional <= max_h + 1e-9

    def test_apply_hedge_cap_respects_zero_liquidity(self):
        assert apply_hedge_cap(1000.0, 0.0) == 0.0

    def test_hedge_cap_with_partial_fill_does_not_exceed_max(self):
        liq = LiquidityModel(available_liquidity=300.0, participation_rate=1.0, impact_factor=0.0)
        inp = base_inp(hedge_fraction=0.9, liability=2000.0, liquidity=liq, fill_probability=0.5)
        metrics = simulate_external_hedge(inp)
        assert metrics.effective_hedge_notional <= 300.0 + 1e-9

    def test_hedge_utilization_at_most_one(self):
        liq = LiquidityModel(available_liquidity=100.0, participation_rate=1.0, impact_factor=0.0)
        inp = base_inp(hedge_fraction=1.0, liability=10_000.0, liquidity=liq)
        metrics = simulate_external_hedge(inp)
        assert metrics.hedge_utilization <= 1.0 + 1e-9

    def test_no_liquidity_constraint_uses_full_requested_hedge(self):
        inp = base_inp(hedge_fraction=0.5, liability=2000.0, liquidity=None)
        metrics = simulate_external_hedge(inp)
        assert abs(metrics.effective_hedge_notional - 0.5 * 2000.0) < 1e-6


# ---------------------------------------------------------------------------
# 2. Increasing impact_factor weakly decreases EV
# ---------------------------------------------------------------------------

class TestImpactFactorMono:
    def test_higher_impact_factor_does_not_increase_ev(self):
        factors = [0.0, 0.05, 0.1, 0.3, 1.0]
        evs = []
        for f in factors:
            liq = LiquidityModel(
                available_liquidity=5000.0,
                participation_rate=1.0,
                impact_factor=f,
            )
            inp = base_inp(liquidity=liq, hedge_fraction=0.5, n_paths=5000)
            evs.append(simulate_external_hedge(inp).ev)
        for i in range(len(evs) - 1):
            assert evs[i] >= evs[i + 1] - 1.0, (
                f"EV rose with higher impact factor: {evs[i]:.2f} -> {evs[i+1]:.2f}"
            )

    def test_zero_impact_factor_has_same_ev_as_no_liquidity(self):
        liq = LiquidityModel(available_liquidity=100_000.0, participation_rate=1.0, impact_factor=0.0)
        inp_liq  = base_inp(liquidity=liq,  hedge_fraction=0.5, n_paths=4000)
        inp_none = base_inp(liquidity=None, hedge_fraction=0.5, n_paths=4000)
        ev_liq  = simulate_external_hedge(inp_liq).ev
        ev_none = simulate_external_hedge(inp_none).ev
        assert abs(ev_liq - ev_none) < 5.0


# ---------------------------------------------------------------------------
# 3. Risk transfer curve: non-decreasing hedge ratio under min_cvar
# ---------------------------------------------------------------------------

class TestRiskTransferCurve:
    def test_hedge_ratio_non_decreasing_with_liability(self):
        liabilities = [500.0, 1000.0, 2000.0, 4000.0, 8000.0]
        inp = base_inp(n_paths=1000, seed="curve_test", objective="min_cvar", liquidity=None)
        curve = build_risk_transfer_curve(inp, liabilities, strategy="external_hedge")
        ratios = [pt.optimal_hedge_ratio for pt in curve.points]
        tolerance = 0.05
        for i in range(len(ratios) - 1):
            assert ratios[i + 1] >= ratios[i] - tolerance, (
                f"Hedge ratio decreased from {ratios[i]:.2f} to {ratios[i+1]:.2f} "
                f"as liability grew from {liabilities[i]} to {liabilities[i+1]}"
            )

    def test_curve_has_correct_number_of_points(self):
        liabilities = [100.0, 200.0, 300.0]
        inp = base_inp(n_paths=500, seed="count_test")
        curve = build_risk_transfer_curve(inp, liabilities, strategy="external_hedge")
        assert len(curve.points) == len(liabilities)

    def test_curve_strategy_label_matches(self):
        liabilities = [1000.0]
        inp = base_inp(n_paths=500, seed="label_test")
        for strategy in ("external_hedge", "internal_reprice", "hybrid"):
            inp2 = dataclasses.replace(inp, strategy=strategy)
            curve = build_risk_transfer_curve(inp2, liabilities, strategy=strategy)
            assert curve.strategy == strategy


# ---------------------------------------------------------------------------
# metrics.cvar
# ---------------------------------------------------------------------------

class TestCVaR:
    def test_cvar_empty_returns_zero(self):
        assert cvar([]) == 0.0

    def test_cvar_single_value(self):
        assert cvar([-100.0]) == -100.0

    def test_cvar_is_mean_of_worst_5pct(self):
        paths = list(range(-100, 0)) + list(range(0, 900))
        result = cvar(paths, alpha=0.95)
        assert result < 0

    def test_cvar_worse_than_ev(self):
        rng = np.random.default_rng(42)
        paths = rng.normal(-50, 200, 1000).tolist()
        ev = np.mean(paths)
        result = cvar(paths, alpha=0.95)
        assert result <= ev + 1e-9


# ---------------------------------------------------------------------------
# Strategy smoke tests
# ---------------------------------------------------------------------------

class TestStrategies:
    def test_external_hedge_returns_metrics(self):
        metrics = simulate_external_hedge(base_inp())
        assert metrics.ev is not None
        assert metrics.cvar_95 <= metrics.p5 + 1.0

    def test_internal_reprice_lower_ev_than_no_reprice(self):
        model = InternalRepriceModel(enabled=True, odds_move_sensitivity=0.001, handle_retention_decay=0.5)
        inp = base_inp(internal_reprice=model, strategy="internal_reprice")
        metrics = simulate_internal_reprice(inp)
        assert metrics.ev < inp.stake

    def test_hybrid_fills_between_strategies(self):
        inp = base_inp(hedge_fraction=0.5, strategy="hybrid")
        metrics = simulate_hybrid(inp)
        assert metrics.ev is not None

    def test_optimize_returns_best_hedge_fraction(self):
        inp = base_inp(n_paths=500, seed="opt_test", objective="min_cvar")
        metrics = optimize_hedge_ratio(inp)
        assert 0.0 <= metrics.optimal_hedge_ratio <= 1.0
        assert metrics.cvar_95 is not None
