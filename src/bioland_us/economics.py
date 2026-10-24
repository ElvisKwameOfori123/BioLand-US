"""Offer affordability: the largest annual land payment the POLYSYS price can fund.

For a perennial stand of T years, discount rate r, mature yield y (dry short tons
per acre, from POLYSYS) and farmgate price P (US$ per dry ton):

    PV revenue = P * y * (s2 * d_2 + sum_{t=3..T} d_t)
    PV cost    = C_1 d_1 + (C_2 + c_2 * s2 * y) d_2 + sum_{t=3..T} (C_r + c_r * y) d_t
    L_max      = (PV revenue - PV cost) / sum_{t=1..T} d_t        (US$ per acre per year)

with d_t = (1 + r)^-t, s2 the year-2 yield share, C per-area and c per-ton costs
from the published budget (decision E01). An offer above L_max cannot be paid out
of biomass revenue. The budget does not itemise harvest machinery, so L_max is an
upper bound on the payable land rent; an offer above it is unaffordable a fortiori.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

HA_PER_ACRE = 0.404686
T_PER_DRY_SHORT_TON = 0.907185
BUDGET_FOR_FEEDSTOCK = {"Switchgrass": "Switchgrass", "Miscanthus": "Miscanthus", "Energy cane": "Miscanthus"}


def max_land_payment(
    yield_dt_per_acre: np.ndarray,
    price_usd_per_dt: float,
    budget: pd.Series,
    *,
    stand_years: int,
    discount_rate: float,
    year2_yield_share: float,
    cost_deflator: float = 1.0,
) -> np.ndarray:
    """Annual land payment (US$/acre) that leaves the grower at zero NPV."""
    y = np.asarray(yield_dt_per_acre, dtype=float)
    t = np.arange(1, stand_years + 1)
    d = (1.0 + discount_rate) ** -t
    area = HA_PER_ACRE * cost_deflator
    tonne = T_PER_DRY_SHORT_TON * cost_deflator

    revenue = price_usd_per_dt * y * (year2_yield_share * d[1] + d[2:].sum())
    cost = (
        budget["year1_usd_per_ha"] * area * d[0]
        + (budget["year2_usd_per_ha"] * area + budget["year2_usd_per_t"] * tonne * year2_yield_share * y) * d[1]
        + (budget["later_usd_per_ha"] * area + budget["later_usd_per_t"] * tonne * y) * d[2:].sum()
    )
    return (revenue - cost) / d.sum()
