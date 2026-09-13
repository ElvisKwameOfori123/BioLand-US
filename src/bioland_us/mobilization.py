"""Deterministic contractual-capacity and mobilization engine."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .validation import (
    require_columns,
    require_nonnegative,
    require_unique,
    require_unit_interval,
)

POOL_KEYS = ["allocation_family", "fips", "land_type"]


def aggregate_polysys_pools(resource: pd.DataFrame) -> pd.DataFrame:
    """Aggregate feedstock rows to county × land before capacity comparison."""
    require_columns(resource, [*POOL_KEYS, "A_P", "Q_P"], name="POLYSYS resource")
    require_nonnegative(resource["A_P"], name="A_P")
    require_nonnegative(resource["Q_P"], name="Q_P")

    pools = (
        resource.groupby(POOL_KEYS, as_index=False, dropna=False)
        .agg(A_P=("A_P", "sum"), Q_P=("Q_P", "sum"))
    )
    require_unique(pools, POOL_KEYS, name="POLYSYS pools")
    return pools


def compute_pool_capacity(
    pools: pd.DataFrame,
    land: pd.DataFrame,
    access: pd.DataFrame,
) -> pd.DataFrame:
    """Combine compatible land B with transmitted acreage-access rate kappa."""
    require_columns(land, ["fips", "land_type", "B"], name="compatible land")
    require_columns(
        access,
        [*POOL_KEYS, "scenario_id", "contract_years", "kappa"],
        name="access",
    )
    require_nonnegative(land["B"], name="compatible land B")
    require_unit_interval(access["kappa"], name="kappa", allow_missing=True)
    require_unique(land, ["fips", "land_type"], name="compatible land")

    x = access.merge(pools, on=POOL_KEYS, how="left", validate="m:1")
    x = x.merge(land, on=["fips", "land_type"], how="left", validate="m:1")

    if x[["A_P", "Q_P", "B"]].isna().any().any():
        raise ValueError("Capacity build produced unmatched POLYSYS or land rows.")

    x["K"] = x["B"] * x["kappa"]
    return x


def apply_capacity_constraint(capacity: pd.DataFrame) -> pd.DataFrame:
    """Apply the frozen no-reallocation matching rule.

    Zero-capacity binding:
      K = 0 and A_P > 0 -> binding = 1, rho = +inf, lambda = 0.
    """
    require_columns(
        capacity,
        ["A_P", "Q_P", "B", "K", "scenario_id", "contract_years", *POOL_KEYS],
        name="capacity",
    )

    out = capacity.copy()
    A = out["A_P"].to_numpy(float)
    K = out["K"].to_numpy(float)

    unsupported = ~np.isfinite(K)
    zero_binding = np.isfinite(K) & (K == 0) & (A > 0)
    positive = np.isfinite(K) & (K > 0)

    rho = np.full(len(out), np.nan, dtype=float)
    rho[positive] = A[positive] / K[positive]
    rho[zero_binding] = np.inf

    lam = np.full(len(out), np.nan, dtype=float)
    lam[positive] = np.minimum(1.0, K[positive] / A[positive])
    lam[zero_binding] = 0.0
    lam[np.isfinite(K) & (A == 0)] = 1.0

    binding = np.full(len(out), np.nan)
    known = np.isfinite(lam)
    binding[known] = (lam[known] < 1.0).astype(int)

    out["rho"] = rho
    out["lambda"] = lam
    out["binding"] = binding
    out["zero_capacity_binding"] = zero_binding.astype(int)
    out["capacity_status"] = np.select(
        [unsupported, zero_binding, positive & (rho > 1), positive],
        ["UNSUPPORTED", "ZERO_CAPACITY_BINDING", "BINDING", "NONBINDING"],
        default="NO_REQUIREMENT",
    )
    out["A_M"] = np.where(np.isfinite(lam), lam * out["A_P"], np.nan)
    out["Q_M"] = np.where(np.isfinite(lam), lam * out["Q_P"], np.nan)
    out["unmet_A"] = out["A_P"] - out["A_M"]
    out["unmet_Q"] = out["Q_P"] - out["Q_M"]

    if (out.loc[known, "A_M"] > out.loc[known, "A_P"] + 1e-9).any():
        raise ValueError("Mobilized acreage exceeds upstream acreage.")
    if (out.loc[known, "Q_M"] > out.loc[known, "Q_P"] + 1e-9).any():
        raise ValueError("Mobilized biomass exceeds upstream biomass.")
    return out


def national_summary(constrained: pd.DataFrame) -> pd.DataFrame:
    """Aggregate deterministic results to scenario × family × duration."""
    keys = ["scenario_id", "allocation_family", "contract_years"]

    def summarise(g: pd.DataFrame) -> pd.Series:
        q_p = g["Q_P"].sum()
        a_p = g["A_P"].sum()
        q_m = g["Q_M"].sum(min_count=1)
        a_m = g["A_M"].sum(min_count=1)
        identified_q = g.loc[g["Q_M"].notna(), "Q_P"].sum()

        return pd.Series(
            {
                "A_P": a_p,
                "Q_P": q_p,
                "A_M": a_m,
                "Q_M": q_m,
                "M_A": a_m / a_p if a_p else np.nan,
                "M_Q": q_m / q_p if q_p else np.nan,
                "identified_production_share": identified_q / q_p if q_p else np.nan,
                "binding_county_land_cells": int((g["binding"] == 1).sum()),
                "zero_capacity_binding_cells": int(g["zero_capacity_binding"].sum()),
            }
        )

    return (
        constrained.groupby(keys, dropna=False)
        .apply(summarise, include_groups=False)
        .reset_index()
    )
