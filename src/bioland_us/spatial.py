"""Spatial robustness summaries for county implementation exposure."""

from __future__ import annotations

import numpy as np
import pandas as pd


def county_central_summary(constrained: pd.DataFrame) -> pd.DataFrame:
    """Aggregate county outcomes over land pools while preserving unsupported bounds."""
    keys = ["allocation_family", "scenario_id", "contract_years", "fips"]

    def summarise(g: pd.DataFrame) -> pd.Series:
        a_p = float(g["A_P"].sum())
        q_p = float(g["Q_P"].sum())
        k = g["K"].sum(min_count=1)

        a_lo = float(g["A_M_full_lower"].sum())
        a_hi = float(g["A_M_full_upper"].sum())
        q_lo = float(g["Q_M_full_lower"].sum())
        q_hi = float(g["Q_M_full_upper"].sum())

        if a_p > 0 and np.isfinite(k):
            rho = np.inf if k == 0 else a_p / float(k)
        else:
            rho = np.nan

        return pd.Series(
            {
                "A_P": a_p,
                "Q_P": q_p,
                "K": k,
                "rho": rho,
                "M_A_full_lower": a_lo / a_p if a_p else np.nan,
                "M_A_full_upper": a_hi / a_p if a_p else np.nan,
                "M_Q_full_lower": q_lo / q_p if q_p else np.nan,
                "M_Q_full_upper": q_hi / q_p if q_p else np.nan,
                "unmet_A_full_lower": a_p - a_hi,
                "unmet_A_full_upper": a_p - a_lo,
                "unmet_Q_full_lower": q_p - q_hi,
                "unmet_Q_full_upper": q_p - q_lo,
                "binding": int(np.isinf(rho) or (np.isfinite(rho) and rho > 1)),
                "unsupported_land_cells": int(g["lambda"].isna().sum()),
            }
        )

    return (
        constrained.groupby(keys, dropna=False)
        .apply(summarise, include_groups=False)
        .reset_index()
    )


def structural_disagreement(
    variants: pd.DataFrame,
    *,
    value: str = "M_Q_full_lower",
) -> pd.DataFrame:
    """D_c = max_S(M_Q,c) - min_S(M_Q,c), reported separately from bootstrap."""
    keys = ["allocation_family", "scenario_id", "contract_years", "fips"]
    out = variants.groupby(keys)[value].agg(["min", "max"]).reset_index()
    out["D_structural"] = out["max"] - out["min"]
    return out
