"""Prepare the canonical three-family POLYSYS perennial allocation.

The input should already represent the retained 2041, US$70/dry-ton perennial
allocation. This script standardizes names, verifies the known duplicate source
label, keeps one representative per independent allocation family, and attaches
the explicit Study-A treatment-class transfer.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from bioland_us.feedstocks import apply_feedstock_transfer
from bioland_us.validation import require_columns, require_nonnegative


FAMILY = {
    "emerging": "FAMILY_01",
    "mature-market high": "FAMILY_01",
    "mature-market low": "FAMILY_02",
    "mature-market medium": "FAMILY_03",
}
REPRESENTATIVE = {
    "FAMILY_01": "emerging",
    "FAMILY_02": "mature-market low",
    "FAMILY_03": "mature-market medium",
}


def normalize_text(value: object) -> str:
    return " ".join(str(value).strip().lower().replace("_", " ").split())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/frozen/public/polysys_allocation.csv"),
    )
    args = parser.parse_args()

    raw = pd.read_csv(args.input, dtype={"fips": "string"}, low_memory=False)

    # Accept either the frozen-development names or already-clean names.
    rename = {}
    candidates = {
        "scenario_name": ["scenario_name", "scenario"],
        "feedstock": ["feedstock", "resource", "resource_canonical"],
        "fips": ["fips"],
        "land_type": ["land_type", "landsrce"],
        "A_P": ["A_P", "harvest_acres", "harvest"],
        "Q_P": ["Q_P", "production_dry_tons", "prod"],
    }
    for target, names in candidates.items():
        found = next((name for name in names if name in raw.columns), None)
        if found is None and target != "scenario_name":
            raise ValueError(f"POLYSYS input lacks a recognized column for {target}.")
        if found is not None:
            rename[found] = target

    out = raw.rename(columns=rename).copy()

    if "allocation_family" not in out.columns:
        require_columns(out, ["scenario_name"], name="POLYSYS input")
        scenario_norm = out["scenario_name"].map(normalize_text)
        out["allocation_family"] = scenario_norm.map(FAMILY)
        if out["allocation_family"].isna().any():
            unknown = sorted(out.loc[out["allocation_family"].isna(), "scenario_name"].astype(str).unique())
            raise ValueError(f"Unknown POLYSYS scenario labels: {unknown}")
    else:
        out["allocation_family"] = out["allocation_family"].astype("string")

    require_columns(
        out,
        ["allocation_family", "fips", "land_type", "feedstock", "A_P", "Q_P"],
        name="POLYSYS input",
    )

    out["fips"] = (
        out["fips"].astype("string").str.replace(r"\.0$", "", regex=True).str.zfill(5)
    )
    land = out["land_type"].astype("string").str.strip().str.lower()
    out["land_type"] = land.map(
        {
            "crop": "Crop",
            "cropland": "Crop",
            "pasture": "Pasture",
            "pastureland": "Pasture",
        }
    )
    if out["land_type"].isna().any():
        raise ValueError("POLYSYS contains land classes outside Crop/Pasture.")

    out["A_P"] = pd.to_numeric(out["A_P"], errors="coerce")
    out["Q_P"] = pd.to_numeric(out["Q_P"], errors="coerce")
    require_nonnegative(out["A_P"], name="POLYSYS A_P")
    require_nonnegative(out["Q_P"], name="POLYSYS Q_P")

    out = apply_feedstock_transfer(out, feedstock_col="feedstock")

    # If the four original source labels are present, verify the known duplicate
    # before retaining one representative per independent family.
    if "scenario_name" in out.columns:
        out["_scenario_norm"] = out["scenario_name"].map(normalize_text)
        labels = set(out["_scenario_norm"].dropna())
        if {"emerging", "mature-market high"}.issubset(labels):
            key = ["fips", "land_type", "feedstock", "A_P", "Q_P"]
            a = (
                out.loc[out["_scenario_norm"].eq("emerging"), key]
                .sort_values(key[:3])
                .reset_index(drop=True)
            )
            b = (
                out.loc[out["_scenario_norm"].eq("mature-market high"), key]
                .sort_values(key[:3])
                .reset_index(drop=True)
            )
            if len(a) != len(b) or not (
                a[key[:3]].equals(b[key[:3]])
                and np.allclose(a["A_P"], b["A_P"], atol=1e-10, rtol=0)
                and np.allclose(a["Q_P"], b["Q_P"], atol=1e-10, rtol=0)
            ):
                raise ValueError(
                    "Emerging and mature-market high are not exact allocation duplicates."
                )

        rep = out["allocation_family"].map(REPRESENTATIVE)
        keep = out["_scenario_norm"].eq(rep) | ~out["_scenario_norm"].isin(set(FAMILY))
        if out["allocation_family"].isin(REPRESENTATIVE).all():
            out = out.loc[keep].copy()
        out = out.drop(columns="_scenario_norm")

    if out["allocation_family"].nunique() != 3:
        raise ValueError(
            f"Expected three independent allocation families; found {out['allocation_family'].nunique()}."
        )

    keep_cols = [
        c
        for c in [
            "scenario_name",
            "allocation_family",
            "fips",
            "land_type",
            "feedstock",
            "experimental_feedstock",
            "treatment_class",
            "directly_tested_species",
            "transfer_status",
            "A_P",
            "Q_P",
        ]
        if c in out.columns
    ]
    out = out[keep_cols].copy()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)

    print("PASS: canonical POLYSYS allocation written.")
    print(f"  rows={len(out):,}")
    print(f"  independent families={out['allocation_family'].nunique()}")
    print(f"  counties={out['fips'].nunique():,}")
    print(f"  output={args.output}")


if __name__ == "__main__":
    main()
