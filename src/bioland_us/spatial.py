"""Spatial robustness summaries for county implementation exposure."""

from __future__ import annotations

import numpy as np
import pandas as pd


def county_central_summary(constrained: pd.DataFrame) -> pd.DataFrame:
    """Aggregate county implementation outcomes over land pools."""
    keys = ["allocation_family", "scenario_id", "contract_years", "fips"]

    def summarise(g: pd.DataFrame) -> pd.Series:
        a_p = g["A_P"].sum()
        q_p = g["Q_P"].sum()
        a_m = g["A_M"].sum(min_count=1)
        q_m = g["Q_M"].sum(min_count=1)
        k = g["K"].sum(min_count=1)

        if a_p > 0 and np.isfinite(k):
            rho = np.inf if k == 0 else a_p / k
        else:
            rho = np.nan

        return pd.Series(
            {
                "A_P": a_p,
                "Q_P": q_p,
                "K": k,
                "rho": rho,
                "M_A": a_m / a_p if a_p else np.nan,
                "M_Q": q_m / q_p if q_p else np.nan,
                "unmet_A": a_p - a_m if np.isfinite(a_m) else np.nan,
                "unmet_Q": q_p - q_m if np.isfinite(q_m) else np.nan,
                "binding": int(np.isinf(rho) or (np.isfinite(rho) and rho > 1)),
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
    value: str = "M_Q",
) -> pd.DataFrame:
    """D_c = max_S(M_Q,c) - min_S(M_Q,c)."""
    keys = ["allocation_family", "scenario_id", "contract_years", "fips"]
    out = variants.groupby(keys)[value].agg(["min", "max"]).reset_index()
    out["D_structural"] = out["max"] - out["min"]
    return out
