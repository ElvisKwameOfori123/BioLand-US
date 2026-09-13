"""Deterministic contractual-capacity and mobilization engine."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .validation import require_columns, require_nonnegative, require_unique, require_unit_interval

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

    Known-capacity cells:
        rho = A_P / K
        lambda = min(1, K / A_P)

    Zero-capacity binding:
        K = 0 and A_P > 0 -> rho = +inf, lambda = 0.

    Unsupported capacity:
        lambda remains missing.
        For full-denominator accounting, mobilization is reported as an
        identification interval:
            lower = 0 contribution from unsupported cells
            upper = full upstream contribution from unsupported cells

    This preserves unsupported evidence as unknown rather than recoding it to zero.
    """
    require_columns(
        capacity,
        ["A_P", "Q_P", "B", "K", "scenario_id", "contract_years", *POOL_KEYS],
        name="capacity",
    )

    out = capacity.copy()
    A = out["A_P"].to_numpy(float)
    Q = out["Q_P"].to_numpy(float)
    K = out["K"].to_numpy(float)

    unsupported = ~np.isfinite(K)
    zero_binding = np.isfinite(K) & (K == 0) & (A > 0)
    positive = np.isfinite(K) & (K > 0)
    no_requirement = np.isfinite(K) & (A == 0)

    rho = np.full(len(out), np.nan, dtype=float)
    rho[positive] = A[positive] / K[positive]
    rho[zero_binding] = np.inf

    lam = np.full(len(out), np.nan, dtype=float)
    lam[positive] = np.minimum(1.0, K[positive] / A[positive])
    lam[zero_binding] = 0.0
    lam[no_requirement] = 1.0

    binding = np.full(len(out), np.nan)
    known = np.isfinite(lam)
    binding[known] = (lam[known] < 1.0).astype(int)

    out["rho"] = rho
    out["lambda"] = lam
    out["binding"] = binding
    out["zero_capacity_binding"] = zero_binding.astype(int)
    out["capacity_status"] = np.select(
        [unsupported, zero_binding, positive & (rho > 1), positive, no_requirement],
        ["UNSUPPORTED", "ZERO_CAPACITY_BINDING", "BINDING", "NONBINDING", "NO_REQUIREMENT"],
        default="UNKNOWN",
    )

    out["A_M_known"] = np.where(known, lam * A, np.nan)
    out["Q_M_known"] = np.where(known, lam * Q, np.nan)

    out["A_M_full_lower"] = np.where(unsupported, 0.0, out["A_M_known"])
    out["Q_M_full_lower"] = np.where(unsupported, 0.0, out["Q_M_known"])
    out["A_M_full_upper"] = np.where(unsupported, A, out["A_M_known"])
    out["Q_M_full_upper"] = np.where(unsupported, Q, out["Q_M_known"])

    out["unmet_A_full_lower"] = A - out["A_M_full_upper"]
    out["unmet_A_full_upper"] = A - out["A_M_full_lower"]
    out["unmet_Q_full_lower"] = Q - out["Q_M_full_upper"]
    out["unmet_Q_full_upper"] = Q - out["Q_M_full_lower"]

    if (out["A_M_full_lower"] > A + 1e-9).any():
        raise ValueError("Lower mobilized acreage exceeds upstream acreage.")
    if (out["A_M_full_upper"] > A + 1e-9).any():
        raise ValueError("Upper mobilized acreage exceeds upstream acreage.")
    if (out["Q_M_full_lower"] > Q + 1e-9).any():
        raise ValueError("Lower mobilized biomass exceeds upstream biomass.")
    if (out["Q_M_full_upper"] > Q + 1e-9).any():
        raise ValueError("Upper mobilized biomass exceeds upstream biomass.")
    if (out["A_M_full_lower"] > out["A_M_full_upper"] + 1e-9).any():
        raise ValueError("Mobilization lower bound exceeds upper bound.")
    if (out["Q_M_full_lower"] > out["Q_M_full_upper"] + 1e-9).any():
        raise ValueError("Biomass lower bound exceeds upper bound.")

    return out


def national_summary(constrained: pd.DataFrame) -> pd.DataFrame:
    """Aggregate results to scenario × family × duration with full-denominator bounds."""
    keys = [
        column
        for column in [
            "track",
            "scenario_id",
            "rent_multiplier",
            "allocation_family",
            "contract_years",
        ]
        if column in constrained.columns
    ]

    def summarise(g: pd.DataFrame) -> pd.Series:
        q_p = float(g["Q_P"].sum())
        a_p = float(g["A_P"].sum())

        a_lo = float(g["A_M_full_lower"].sum())
        a_hi = float(g["A_M_full_upper"].sum())
        q_lo = float(g["Q_M_full_lower"].sum())
        q_hi = float(g["Q_M_full_upper"].sum())

        identified_a = float(g.loc[g["lambda"].notna(), "A_P"].sum())
        identified_q = float(g.loc[g["lambda"].notna(), "Q_P"].sum())

        return pd.Series(
            {
                "A_P": a_p,
                "Q_P": q_p,
                "A_M_full_lower": a_lo,
                "A_M_full_upper": a_hi,
                "Q_M_full_lower": q_lo,
                "Q_M_full_upper": q_hi,
                "M_A_full_lower": a_lo / a_p if a_p else np.nan,
                "M_A_full_upper": a_hi / a_p if a_p else np.nan,
                "M_Q_full_lower": q_lo / q_p if q_p else np.nan,
                "M_Q_full_upper": q_hi / q_p if q_p else np.nan,
                "identified_acreage_share": identified_a / a_p if a_p else np.nan,
                "identified_production_share": identified_q / q_p if q_p else np.nan,
                "binding_county_land_cells": int((g["binding"] == 1).sum()),
                "zero_capacity_binding_cells": int(g["zero_capacity_binding"].sum()),
                "unsupported_county_land_cells": int(g["lambda"].isna().sum()),
            }
        )

    return (
        constrained.groupby(keys, dropna=False)
        .apply(summarise, include_groups=False)
        .reset_index()
    )
