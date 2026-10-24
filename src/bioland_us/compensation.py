"""Rent-indexed compensation scenarios (decision C01).

A rent-indexed contract offers O_cl = m * R_cl. The reference multipliers are
the family-balanced, harvested-acre weighted median of X / R_cl, i.e. the
multiplier at which half of the (family-balanced) POLYSYS acreage is offered at
least the Study-A treatment X in {50, 100, 200, 300}. Rent parity (m = 1) is a
benchmark.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SCENARIO_FOR_OFFER = {
    50.0: "SUPPORT_ENTRY_REFERENCE",
    100.0: "SUPPORT_BALANCED_REFERENCE",
    200.0: "HIGHER_COMPENSATION_200_REFERENCE",
    300.0: "HIGHER_COMPENSATION_300_REFERENCE",
}
RENT_PARITY = "RENT_PARITY_BENCHMARK"


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cw = np.cumsum(w)
    return float(v[min(np.searchsorted(cw, 0.5 * cw[-1], side="left"), len(v) - 1)])


def reference_multipliers(pools: pd.DataFrame, rents: pd.DataFrame, offers) -> pd.DataFrame:
    """Return scenario_id / rent_multiplier rows, rent parity first."""
    x = pools.groupby(["allocation_family", "fips", "land_type"], as_index=False)["A_P"].sum()
    x = x.merge(rents[["fips", "land_type", "rent_supported", "rent_2012usd_per_acre"]],
                on=["fips", "land_type"], how="left", validate="m:1")
    x = x.loc[x["rent_supported"].fillna(False).astype(bool) & x["A_P"].gt(0)]
    w = (x["A_P"] / x.groupby("allocation_family")["A_P"].transform("sum")).to_numpy()
    rent = x["rent_2012usd_per_acre"].to_numpy(float)

    rows = [{"scenario_id": RENT_PARITY, "rent_multiplier": 1.0, "anchor_offer": np.nan}]
    for offer in offers:
        rows.append({
            "scenario_id": SCENARIO_FOR_OFFER[float(offer)],
            "rent_multiplier": weighted_median(float(offer) / rent, w),
            "anchor_offer": float(offer),
        })
    return pd.DataFrame(rows)
