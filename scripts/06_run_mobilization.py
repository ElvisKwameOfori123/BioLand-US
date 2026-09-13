"""Run deterministic contractual capacity and biomass mobilization."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from bioland_us.mobilization import apply_capacity_constraint, national_summary
from bioland_us.validation import require_columns, require_unique


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--access",
        type=Path,
        default=Path("data/frozen/public/behavioural_access.csv"),
    )
    parser.add_argument(
        "--land",
        type=Path,
        default=Path("data/frozen/public/compatible_land.csv"),
    )
    parser.add_argument(
        "--output-detail",
        type=Path,
        default=Path("results/deterministic/county_land_mobilization.csv"),
    )
    parser.add_argument(
        "--output-summary",
        type=Path,
        default=Path("results/deterministic/national_mobilization.csv"),
    )
    args = parser.parse_args()

    access = pd.read_csv(args.access, dtype={"fips": "string"})
    land = pd.read_csv(args.land, dtype={"fips": "string"})

    require_columns(
        access,
        [
            "scenario_id",
            "allocation_family",
            "contract_years",
            "fips",
            "land_type",
            "A_P",
            "Q_P",
            "kappa",
        ],
        name="behavioural access",
    )
    require_columns(land, ["fips", "land_type", "B"], name="compatible land")
    require_unique(land, ["fips", "land_type"], name="compatible land")

    x = access.merge(
        land,
        on=["fips", "land_type"],
        how="left",
        validate="m:1",
    )
    if x["B"].isna().any():
        raise ValueError("Some resource pools have no compatible-land denominator.")

    x["K"] = x["B"] * x["kappa"]
    out = apply_capacity_constraint(x)
    summary = national_summary(out)

    args.output_detail.parent.mkdir(parents=True, exist_ok=True)
    args.output_summary.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_detail, index=False)
    summary.to_csv(args.output_summary, index=False)

    print("PASS: deterministic capacity and mobilization complete.")
    print(f"  detail={args.output_detail}")
    print(f"  summary={args.output_summary}")


if __name__ == "__main__":
    main()
