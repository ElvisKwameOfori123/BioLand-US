"""Standardize the retained POLYSYS perennial allocation."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from bioland_us.feedstocks import apply_feedstock_transfer
from bioland_us.validation import require_columns, require_nonnegative


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/frozen/public/polysys_allocation.csv"),
    )
    parser.add_argument("--family-col", default="allocation_family")
    parser.add_argument("--fips-col", default="fips")
    parser.add_argument("--land-col", default="landsrce")
    parser.add_argument("--feedstock-col", default="feedstock")
    parser.add_argument("--acreage-col", default="harvest_acres")
    parser.add_argument("--production-col", default="production_dry_tons")
    args = parser.parse_args()

    raw = pd.read_csv(args.input, dtype={args.fips_col: "string"})
    require_columns(
        raw,
        [
            args.family_col,
            args.fips_col,
            args.land_col,
            args.feedstock_col,
            args.acreage_col,
            args.production_col,
        ],
        name="POLYSYS input",
    )

    out = raw.rename(
        columns={
            args.family_col: "allocation_family",
            args.fips_col: "fips",
            args.land_col: "land_type",
            args.feedstock_col: "feedstock",
            args.acreage_col: "A_P",
            args.production_col: "Q_P",
        }
    ).copy()

    out["fips"] = (
        out["fips"].astype("string").str.replace(r"\.0$", "", regex=True).str.zfill(5)
    )
    out["land_type"] = out["land_type"].replace(
        {"Cropland": "Crop", "crop": "Crop", "pasture": "Pasture"}
    )
    require_nonnegative(out["A_P"], name="POLYSYS A_P")
    require_nonnegative(out["Q_P"], name="POLYSYS Q_P")
    out = apply_feedstock_transfer(out)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)

    print("PASS: POLYSYS canonical allocation written.")
    print(f"  rows={len(out):,}")
    print(f"  families={out['allocation_family'].nunique():,}")
    print(f"  counties={out['fips'].nunique():,}")
    print(f"  output={args.output}")


if __name__ == "__main__":
    main()
