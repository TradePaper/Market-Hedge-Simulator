def max_hedge_notional(available_liquidity: float, participation_rate: float) -> float:
    return max(0.0, available_liquidity * participation_rate)


def apply_hedge_cap(requested_hedge: float, max_hedge: float) -> float:
    return max(0.0, min(requested_hedge, max_hedge))


def market_impact_delta_price(
    hedge_size: float,
    liquidity: float,
    impact_factor: float,
    depth_exponent: float = 1.0,
) -> float:
    if liquidity <= 0:
        return 0.0
    return impact_factor * (hedge_size / liquidity) ** depth_exponent


def effective_cost_rate(base_cost_rate: float, impact_delta: float) -> float:
    return max(0.0, base_cost_rate + impact_delta)
