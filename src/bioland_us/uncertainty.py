"""Statistical uncertainty helpers for BioLand-US.

Statistical sampling uncertainty is kept separate from structural sensitivity.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def fit_weighted_logit_irls(
    X: np.ndarray,
    y: np.ndarray,
    frequency_weight: np.ndarray,
    *,
    beta0: np.ndarray | None = None,
    maxiter: int = 100,
    tolerance: float = 1e-10,
) -> tuple[np.ndarray, bool]:
    """Fit a weighted binomial logit by Newton/IRLS.

    Frequency weights are respondent-bootstrap multiplicities. The function is
    used only for point-estimate refits inside the paired bootstrap.
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    w = np.asarray(frequency_weight, dtype=float)

    beta = (
        np.zeros(X.shape[1], dtype=float)
        if beta0 is None
        else np.asarray(beta0, dtype=float).copy()
    )
    ridge = 1e-9

    for _ in range(maxiter):
        eta = X @ beta
        p = 1.0 / (1.0 + np.exp(-np.clip(eta, -700, 700)))
        variance = np.maximum(p * (1.0 - p), 1e-12)
        gradient = X.T @ (w * (y - p))
        hessian = X.T @ ((w * variance)[:, None] * X)

        try:
            step = np.linalg.solve(
                hessian + ridge * np.eye(X.shape[1]),
                gradient,
            )
        except np.linalg.LinAlgError:
            step = np.linalg.lstsq(
                hessian + ridge * np.eye(X.shape[1]),
                gradient,
                rcond=None,
            )[0]

        beta_new = beta + step
        if not np.all(np.isfinite(beta_new)):
            return beta_new, False
        if np.max(np.abs(step)) < tolerance:
            return beta_new, True
        beta = beta_new

    return beta, False


def percentile_summary(
    draws: pd.DataFrame,
    *,
    value: str,
    group_cols: list[str],
    probs: tuple[float, float, float] = (0.025, 0.5, 0.975),
) -> pd.DataFrame:
    """Return percentile summaries across bootstrap draws."""
    q = draws.groupby(group_cols)[value].quantile(list(probs)).unstack().reset_index()
    return q.rename(
        columns={
            probs[0]: "p025",
            probs[1]: "p50",
            probs[2]: "p975",
        }
    )


def family_balanced_draws(
    draws: pd.DataFrame,
    *,
    value: str,
    draw_col: str = "draw",
    family_col: str = "allocation_family",
    group_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Average the three independent allocation families within each draw."""
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
    for draw, group in draws.groupby(draw_col):
        valid = group[group[risk_col].notna()].copy()
        if valid.empty:
            continue
        n_top = max(1, int(np.ceil(0.10 * len(valid))))
        valid = valid.sort_values(risk_col, ascending=False)
        valid["top10"] = 0
        valid.iloc[:n_top, valid.columns.get_loc("top10")] = 1
        pieces.append(valid[[county_col, "top10"]].assign(**{draw_col: draw}))

    long = pd.concat(pieces, ignore_index=True)
    return (
        long.groupby(county_col, as_index=False)["top10"]
        .mean()
        .rename(columns={"top10": "P_top10"})
    )
