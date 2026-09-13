"""Paired respondent bootstrap for behavioural sampling uncertainty.

The same resampled respondents determine:
1. the smooth extensive participation model; and
2. the conditional-acreage central reconstruction.

For each draw, exact accepted choices retain their observed intensive share.
The draw-specific exact-case mean is projected into each non-exact accepted
choice's frozen [lower, upper] admissible interval. This mirrors the frozen
Stage-03C central rule while propagating respondent sampling uncertainty.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from bioland_us.config import load_config
from bioland_us.validation import require_columns


def project_central_share(sample: pd.DataFrame) -> float:
    accepted = sample.loc[sample["acc"].eq(1)].copy()
    exact = accepted["share_exact_observed"].notna()

    if exact.sum() == 0:
        raise RuntimeError("Bootstrap draw contains no exact accepted intensive cases.")

    mu_exact = float(accepted.loc[exact, "share_exact_observed"].mean())

    central = accepted["share_exact_observed"].astype(float).copy()
    nonexact = ~exact

    lo = accepted.loc[nonexact, "share_lower_frozen"].astype(float)
    hi = accepted.loc[nonexact, "share_upper_frozen"].astype(float)

    # Missing numerator / residual cases may have broad [0,1] bounds upstream.
    # The public export must retain those frozen bounds explicitly.
    if lo.isna().any() or hi.isna().any():
        raise RuntimeError(
            "Non-exact accepted choices contain missing frozen lower/upper bounds."
        )

    central.loc[nonexact] = np.minimum(
        hi.to_numpy(),
        np.maximum(lo.to_numpy(), mu_exact),
    )

    if ((central < 0) | (central > 1)).any():
        raise RuntimeError("Projected conditional shares leave [0,1].")

    return float(central.mean())


def fit_draw(sample: pd.DataFrame) -> dict[str, float]:
    x = pd.DataFrame(
        {
            "ln_offer": np.log(sample["offer"].astype(float)),
            "contract10": sample["contract_years"].eq(10).astype(float),
            "pasture": (
                sample["land_type"].astype(str).str.strip().str.lower().eq("pasture")
            ).astype(float),
            "switchgrass": (
                sample["experimental_feedstock"]
                .astype(str)
                .str.strip()
                .str.lower()
                .eq("switchgrass")
            ).astype(float),
        }
    )
    x = sm.add_constant(x, has_constant="add")
    y = sample["acc"].astype(float)

    result = sm.Logit(y, x).fit(disp=False, maxiter=200)

    return {
        "intercept": float(result.params["const"]),
        "ln_offer": float(result.params["ln_offer"]),
        "contract_10yr": float(result.params["contract10"]),
        "pasture": float(result.params["pasture"]),
        "switchgrass": float(result.params["switchgrass"]),
        "conditional_share": project_central_share(sample),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/frozen/restricted/behaviour_bootstrap_input.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/bootstrap/behaviour_parameter_draws.csv"),
    )
    parser.add_argument("--seed", type=int, default=20260912)
    args = parser.parse_args()

    cfg = load_config()
    n_draws = int(cfg["uncertainty"]["bootstrap_draws"])
    df = pd.read_csv(args.input)

    require_columns(
        df,
        [
            "id",
            "acc",
            "offer",
            "contract_years",
            "land_type",
            "experimental_feedstock",
            "intensive_status",
            "share_exact_observed",
            "share_lower_frozen",
            "share_upper_frozen",
            "share_central",
        ],
        name="bootstrap input",
    )

    respondents = pd.Index(df["id"].drop_duplicates())
    rng = np.random.default_rng(args.seed)
    results: list[dict[str, float]] = []
    failures: list[dict[str, object]] = []

    for draw in range(1, n_draws + 1):
        sampled_ids = rng.choice(
            respondents.to_numpy(),
            size=len(respondents),
            replace=True,
        )

        pieces = []
        for boot_cluster, respondent_id in enumerate(sampled_ids):
            g = df[df["id"].eq(respondent_id)].copy()
            g["boot_cluster"] = boot_cluster
            pieces.append(g)

        sample = pd.concat(pieces, ignore_index=True)

        try:
            fitted = fit_draw(sample)
            fitted["draw"] = draw
            results.append(fitted)
        except Exception as exc:
            failures.append({"draw": draw, "error": repr(exc)})

    if failures:
        fail_path = args.output.with_name(args.output.stem + "_failures.csv")
        fail_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(failures).to_csv(fail_path, index=False)
        raise RuntimeError(
            f"{len(failures)} of {n_draws} bootstrap draws failed; see {fail_path}"
        )

    out = pd.DataFrame(results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)

    print(
        f"PASS: {len(out)} paired respondent bootstrap draws written to {args.output}"
    )


if __name__ == "__main__":
    main()
