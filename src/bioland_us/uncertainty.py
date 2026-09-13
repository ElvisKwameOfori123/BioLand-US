"""Uncertainty summaries kept separate from structural sensitivity."""

from __future__ import annotations

import numpy as np
import pandas as pd


def percentile_summary(
    draws: pd.DataFrame,
    *,
    value: str,
    group_cols: list[str],
    probs: tuple[float, float, float] = (0.025, 0.5, 0.975),
) -> pd.DataFrame:
    """Return percentile summaries across bootstrap draws."""
    q = (
        draws.groupby(group_cols)[value]
        .quantile(list(probs))
        .unstack()
        .reset_index()
    )
    return q.rename(columns={probs[0]: "p025", probs[1]: "p50", probs[2]: "p975"})


def family_balanced_draws(
    draws: pd.DataFrame,
    *,
    value: str,
    draw_col: str = "draw",
    family_col: str = "allocation_family",
    group_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Average independent allocation families within each draw."""
    group_cols = group_cols or []
    keys = [draw_col, *group_cols]

    n_family = (
        draws.groupby(keys)[family_col]
        .nunique()
        .rename("n_families")
        .reset_index()
    )
    return (
        draws.groupby(keys, as_index=False)[value]
        .mean()
        .merge(n_family, on=keys, validate="1:1")
    )


def county_binding_probability(
    draws: pd.DataFrame,
    *,
    county_col: str = "fips",
    binding_col: str = "binding",
) -> pd.DataFrame:
    """Compute county P(binding) from bootstrap draws."""
    return (
        draws.groupby(county_col, as_index=False)[binding_col]
        .mean()
        .rename(columns={binding_col: "P_bind"})
    )


def county_top_decile_probability(
    draws: pd.DataFrame,
    *,
    draw_col: str = "draw",
    county_col: str = "fips",
    risk_col: str = "rho",
) -> pd.DataFrame:
    """Probability each county belongs to the highest-risk decile."""
    pieces = []
    for draw, g in draws.groupby(draw_col):
        finite = g[np.isfinite(g[risk_col])].copy()
        if finite.empty:
            continue
        cutoff = finite[risk_col].quantile(0.90)
        finite["top10"] = (finite[risk_col] >= cutoff).astype(int)
        pieces.append(finite[[county_col, "top10"]].assign(**{draw_col: draw}))

    long = pd.concat(pieces, ignore_index=True)
    return (
        long.groupby(county_col, as_index=False)["top10"]
        .mean()
        .rename(columns={"top10": "P_top10"})
    )
