import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator import SimInput, run_simulation, american_to_payout_ratio

BASE = dict(
    stake=1000,
    americanOdds=-110,
    trueWinProb=0.52,
    hedgeFraction=0.5,
    fillProbability=0.75,
    slippageBps=40,
    feeBps=15,
    latencyBps=10,
    nPaths=10_000,
    seed=42,
)


def test_no_hedge_matches_analytical_ev():
    """hedgeFraction=0 simulation EV must match analytical sportsbook EV."""
    params = SimInput(**{**BASE, "hedgeFraction": 0})
    result = run_simulation(params)

    pr = american_to_payout_ratio(params.americanOdds)
    analytical_ev = params.trueWinProb * params.stake * pr - (1 - params.trueWinProb) * params.stake

    assert abs(result.ev - analytical_ev) < 15, (
        f"Simulated EV ${result.ev:.2f} too far from analytical EV ${analytical_ev:.2f}"
    )


def test_deterministic_with_seed():
    """Same seed and inputs must produce identical outputs every time."""
    params = SimInput(**BASE)
    r1 = run_simulation(params)
    r2 = run_simulation(params)

    assert r1.ev    == r2.ev,    "EV not deterministic"
    assert r1.p5    == r2.p5,    "p5 not deterministic"
    assert r1.p50   == r2.p50,   "p50 not deterministic"
    assert r1.p95   == r2.p95,   "p95 not deterministic"
    assert r1.runId == r2.runId, "runId not deterministic"


def test_higher_slippage_lowers_ev():
    """Increasing slippageBps must monotonically decrease EV."""
    def ev_at(bps):
        return run_simulation(SimInput(**{**BASE, "slippageBps": bps})).ev

    ev_0   = ev_at(0)
    ev_50  = ev_at(50)
    ev_150 = ev_at(150)

    assert ev_0 > ev_50,  f"EV should drop from 0→50 bps slippage ({ev_0:.2f} vs {ev_50:.2f})"
    assert ev_50 > ev_150, f"EV should drop from 50→150 bps slippage ({ev_50:.2f} vs {ev_150:.2f})"


if __name__ == "__main__":
    tests = [
        test_no_hedge_matches_analytical_ev,
        test_deterministic_with_seed,
        test_higher_slippage_lowers_ev,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
        except Exception as e:
            print(f"  ERROR {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} tests passed")
    if passed < len(tests):
        sys.exit(1)
