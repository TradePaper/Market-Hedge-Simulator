import numpy as np
from typing import List


def cvar(paths: List[float], alpha: float = 0.95) -> float:
    """CVaR at alpha = mean of worst (1 - alpha) fraction of outcomes."""
    if not paths:
        return 0.0
    arr = np.sort(np.asarray(paths, dtype=float))
    n_tail = max(1, int(len(arr) * (1.0 - alpha)))
    return float(arr[:n_tail].mean())
