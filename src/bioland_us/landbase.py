"""Completion of disclosure-suppressed Census county land values.

For each state and Census item, the acres withheld as "(D)" are known exactly:

    residual = state total - sum of disclosed county values

The residual is shared among the suppressed counties of that state in proportion
to a reference weight, subject to county bounds:

    x_c = clip(t * w_c, lower_c, upper_c),   with t chosen so that sum_c x_c = residual

Disclosed values are never changed, and every state total closes exactly.
"""

from __future__ import annotations

import numpy as np


class InfeasibleAllocation(ValueError):
    """Raised when the bounds cannot reproduce the state residual."""


def allocate_residual(
    residual: float,
    weights: np.ndarray,
    lower: np.ndarray | None = None,
    upper: np.ndarray | None = None,
    *,
    tolerance: float = 1e-9,
) -> np.ndarray:
    """Share ``residual`` across cells proportionally to ``weights`` within bounds.

    Weights that are all zero (or missing) fall back to equal shares. Upper bounds
    may be ``inf``. Raises InfeasibleAllocation when sum(lower) > residual or
    sum(upper) < residual.
    """
    w = np.asarray(weights, dtype=float)
    n = len(w)
    if n == 0:
        if abs(residual) > tolerance:
            raise InfeasibleAllocation(f"Residual {residual} with no suppressed cells.")
        return np.zeros(0)

    lo = np.zeros(n) if lower is None else np.asarray(lower, dtype=float)
    hi = np.full(n, np.inf) if upper is None else np.asarray(upper, dtype=float)
    if not np.all(np.isfinite(w)) or w.sum() <= 0 or np.any(w < 0):
        w = np.ones(n)

    scale = max(1.0, abs(residual))
    if lo.sum() > residual + tolerance * scale or hi.sum() < residual - tolerance * scale:
        raise InfeasibleAllocation(
            f"Bounds [{lo.sum():.1f}, {hi.sum():.1f}] cannot hold residual {residual:.1f}."
        )

    def total(t: float) -> float:
        return float(np.clip(t * w, lo, hi).sum())

    t_lo, t_hi = 0.0, 1.0
    while total(t_hi) < residual and t_hi < 1e30:
        t_hi *= 2.0
    for _ in range(200):
        t_mid = 0.5 * (t_lo + t_hi)
        if total(t_mid) < residual:
            t_lo = t_mid
        else:
            t_hi = t_mid
    x = np.clip(t_hi * w, lo, hi)

    # Remove the last bisection rounding error on cells not pinned at a bound.
    free = (x > lo) & (x < hi)
    gap = residual - x.sum()
    if free.any():
        x[free] += gap * w[free] / w[free].sum()
    if abs(residual - x.sum()) > tolerance * scale:
        raise InfeasibleAllocation("Allocation failed to close the state residual.")
    return x
