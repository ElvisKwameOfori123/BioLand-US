"""County implementation pressure built from the county x land capacity results.

Capacity is constrained separately in each land pool (Crop, Pasture); spare
pasture capacity cannot serve a crop allocation. County summaries therefore
derive from the pool results instead of summing capacity across pools:

    binding  = 1 if any land pool with upstream acreage binds
    rho      = the largest pool pressure A_P / K (the most constrained pool)
    M_Q      = county mobilized biomass / county upstream biomass
"""

from __future__ import annotations

import numpy as np
import pandas as pd

COUNTY_KEYS = ["allocation_family", "scenario_id", "contract_years", "fips"]


def county_central_summary(constrained: pd.DataFrame, keys: list[str] | None = None) -> pd.DataFrame:
    """Aggregate pool results to counties while preserving unresolved bounds."""
    keys = keys or [k for k in COUNTY_KEYS if k in constrained.columns]
    x = constrained.copy()
    active = x["A_P"] > 0
    x["_unresolved"] = active & x["lambda"].isna()
    x["_bind"] = active & (x["binding"] == 1)
    x["_rho"] = np.where(active, x["rho"], np.nan)

    g = x.groupby(keys, dropna=False)
    out = g.agg(
        A_P=("A_P", "sum"),
        Q_P=("Q_P", "sum"),
        K=("K", lambda k: k.sum(min_count=1)),
        A_M_full_lower=("A_M_full_lower", "sum"),
        A_M_full_upper=("A_M_full_upper", "sum"),
        Q_M_full_lower=("Q_M_full_lower", "sum"),
        Q_M_full_upper=("Q_M_full_upper", "sum"),
        unresolved_land_cells=("_unresolved", "sum"),
        binding_land_cells=("_bind", "sum"),
        rho=("_rho", "max"),
    ).reset_index()

    resolved = out["unresolved_land_cells"].eq(0)
    out.loc[~resolved, "rho"] = np.nan
    out["binding"] = np.where(resolved | out["binding_land_cells"].gt(0),
                              out["binding_land_cells"].gt(0).astype(float), np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        for m in ("A", "Q"):
            for b in ("lower", "upper"):
                out[f"M_{m}_full_{b}"] = np.where(
                    out[f"{m}_P"] > 0, out[f"{m}_M_full_{b}"] / out[f"{m}_P"], np.nan
                )
    out["unmet_Q_full_lower"] = out["Q_P"] - out["Q_M_full_upper"]
    out["unmet_Q_full_upper"] = out["Q_P"] - out["Q_M_full_lower"]
    out["unmet_A_full_lower"] = out["A_P"] - out["A_M_full_upper"]
    out["unmet_A_full_upper"] = out["A_P"] - out["A_M_full_lower"]
    return out


def structural_disagreement(
    variants: pd.DataFrame,
    *,
    value: str = "M_Q_full_lower",
) -> pd.DataFrame:
    """D_c = max_S(M_Q,c) - min_S(M_Q,c), reported separately from bootstrap."""
    keys = [k for k in COUNTY_KEYS if k in variants.columns]
    out = variants.groupby(keys)[value].agg(["min", "max"]).reset_index()
    out["D_structural"] = out["max"] - out["min"]
    return out
