"""Deterministic contractual capacity and biomass mobilization (central case).

Central case: PER_CHOICE behaviour, CENTRAL_PRIMARY conditional acreage, the
FARMLAND Census completion surface and T1 pooled transmission.

    K = B * kappa,  lambda = min(1, K / A_P),  Q_M = lambda * Q_P

Unresolved cells (no rent context or unresolved land) stay in the denominator
as full-denominator lower / upper bounds.

Outputs
    results/deterministic/county_land_mobilization.csv
    results/deterministic/national_mobilization.csv   by family + FAMILY_BALANCED mean
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from bioland_us.mobilization import apply_capacity_constraint, national_summary
from bioland_us.validation import require_columns, require_unique


def family_balanced(summary: pd.DataFrame) -> pd.DataFrame:
    """Mean of the three independent allocation families."""
    keys = ["track", "scenario_id", "rent_multiplier", "contract_years"]
    metrics = [c for c in summary.columns if c.startswith(("M_A_", "M_Q_", "identified_"))]
    out = summary.groupby(keys, dropna=False, as_index=False)[metrics].mean()
    out["allocation_family"] = "FAMILY_BALANCED"
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--access", type=Path, default=Path("data/frozen/public/behavioural_access.csv"))
    parser.add_argument("--land", type=Path, default=Path("data/frozen/public/compatible_land.csv"))
    parser.add_argument("--output-detail", type=Path,
                        default=Path("results/deterministic/county_land_mobilization.csv"))
    parser.add_argument("--output-summary", type=Path,
                        default=Path("results/deterministic/national_mobilization.csv"))
    args = parser.parse_args()

    access = pd.read_csv(args.access, dtype={"fips": "string"})
    land = pd.read_csv(args.land, dtype={"fips": "string"})
    require_columns(access, ["behaviour_weighting", "scenario_id", "allocation_family", "contract_years",
                             "fips", "land_type", "A_P", "Q_P", "kappa"], name="behavioural access")
    require_columns(land, ["fips", "land_type", "B"], name="compatible land")
    require_unique(land, ["fips", "land_type"], name="compatible land")

    x = access.loc[access["behaviour_weighting"].eq("PER_CHOICE")].drop(columns="behaviour_weighting")
    x = x.merge(land, on=["fips", "land_type"], how="left", validate="m:1")
    x["K"] = x["B"] * x["kappa"]

    out = apply_capacity_constraint(x)
    summary = national_summary(out)
    summary = pd.concat([summary, family_balanced(summary)], ignore_index=True)

    args.output_detail.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_detail, index=False)
    summary.to_csv(args.output_summary, index=False)

    head = summary.loc[summary["allocation_family"].eq("FAMILY_BALANCED")]
    cols = ["track", "scenario_id", "contract_years", "M_Q_full_lower", "M_Q_full_upper"]
    print("PASS: deterministic capacity and mobilization complete (family-balanced M_Q):")
    print(head[cols].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
