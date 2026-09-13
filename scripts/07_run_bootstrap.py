"""Paired respondent bootstrap for behavioural sampling uncertainty."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from bioland_us.config import load_config
from bioland_us.validation import require_columns


def fit_draw(sample: pd.DataFrame) -> dict[str, float]:
    x = pd.DataFrame(
        {
            "ln_offer": np.log(sample["offer"].astype(float)),
            "contract10": sample["contract_years"].eq(10).astype(float),
            "pasture": sample["land_type"]
            .astype(str)
            .str.lower()
            .eq("pasture")
            .astype(float),
            "switchgrass": sample["experimental_feedstock"]
            .astype(str)
            .str.lower()
            .eq("switchgrass")
            .astype(float),
        }
    )
    x = sm.add_constant(x, has_constant="add")
    y = sample["acc"].astype(float)

    result = sm.Logit(y, x).fit(disp=False, maxiter=200)

    accepted = sample.loc[sample["acc"].eq(1), "share_central"].dropna()
    if accepted.empty:
        raise RuntimeError(
            "Bootstrap draw contains no accepted conditional-share observations."
        )

    return {
        "intercept": float(result.params["const"]),
        "ln_offer": float(result.params["ln_offer"]),
        "contract_10yr": float(result.params["contract10"]),
        "pasture": float(result.params["pasture"]),
        "switchgrass": float(result.params["switchgrass"]),
        "conditional_share": float(accepted.mean()),
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
            "share_central",
        ],
        name="bootstrap input",
    )

    respondents = pd.Index(df["id"].drop_duplicates())
    rng = np.random.default_rng(args.seed)
    results = []
    failures = []

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
