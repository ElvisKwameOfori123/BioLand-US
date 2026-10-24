"""Build the canonical POLYSYS perennial allocation from the raw ORNL archive.

Input
    data/raw/AgriResdJetCropProd_wHrvYldwAnnl_0.1.zip  (pipe-delimited CSV inside)

Retained subset (decision P01)
    model POLYSYS, year 2041, offer price US$70 per dry ton, land source Crop or
    Pasture, and the seven perennial energy crops:
    Miscanthus, Switchgrass, Energy cane, Willow, Poplar, Eucalyptus, Pine.

Allocation families (decision P02)
    "emerging" and "mature-market high" are verified to be identical allocations,
    so three independent families remain; one source label represents each.

Acres (`harvest`) and dry tons (`prod`) are used exactly as published; nothing
is rebuilt from yields.

Output
    data/frozen/public/polysys_allocation.csv
"""

from __future__ import annotations

import argparse
import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from bioland_us.feedstocks import apply_feedstock_transfer
from bioland_us.geography import normalize_fips, normalize_land_type
from bioland_us.validation import require_columns, require_nonnegative, require_unique

MEMBER = "AgriResdJetCropProd_wHrvYldwAnnl_0.1.csv"
PERENNIALS = ["Miscanthus", "Switchgrass", "Energy cane", "Willow", "Poplar", "Eucalyptus", "Pine"]
FAMILY = {
    "emerging": "FAMILY_01",
    "mature-market high": "FAMILY_01",
    "mature-market low": "FAMILY_02",
    "mature-market medium": "FAMILY_03",
}
REPRESENTATIVE = {"emerging", "mature-market low", "mature-market medium"}
KEY = ["fips", "land_type", "feedstock"]


def read_raw(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        raw = archive.read(MEMBER)
    return pd.read_csv(io.BytesIO(raw), sep="|", dtype="string")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw/AgriResdJetCropProd_wHrvYldwAnnl_0.1.zip"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/frozen/public/polysys_allocation.csv"),
    )
    args = parser.parse_args()

    raw = read_raw(args.input)
    require_columns(
        raw,
        ["model_name", "scenario_name", "resource", "fips", "landsrce", "year", "prc_ofr", "harvest", "prod"],
        name="raw POLYSYS",
    )

    keep = (
        raw["model_name"].eq("POLYSYS")
        & raw["year"].eq("2041")
        & pd.to_numeric(raw["prc_ofr"], errors="coerce").eq(70)
        & raw["resource"].isin(PERENNIALS)
        & raw["landsrce"].isin(["Crop", "Pasture"])
    )
    x = raw.loc[keep].copy()

    out = pd.DataFrame(
        {
            "scenario_name": x["scenario_name"].str.strip(),
            "fips": normalize_fips(x["fips"]),
            "state_name": x["state_name"].str.strip(),
            "county": x["county"].str.strip(),
            "usdaregion": x["usdaregion"].str.strip(),
            "land_type": normalize_land_type(x["landsrce"]),
            "feedstock": x["resource"].str.strip(),
            "A_P": pd.to_numeric(x["harvest"], errors="coerce").astype(float),
            "Q_P": pd.to_numeric(x["prod"], errors="coerce").astype(float),
        }
    )
    out["allocation_family"] = out["scenario_name"].map(FAMILY)

    if out["allocation_family"].isna().any():
        raise ValueError(f"Unknown scenarios: {sorted(out.loc[out['allocation_family'].isna(), 'scenario_name'].unique())}")
    if out[["fips", "land_type"]].isna().any().any():
        raise ValueError("Retained POLYSYS rows with invalid FIPS or land source.")
    require_nonnegative(out["A_P"], name="POLYSYS harvested acres")
    require_nonnegative(out["Q_P"], name="POLYSYS production")
    require_unique(out, ["scenario_name", *KEY], name="retained POLYSYS")

    # P02: the two FAMILY_01 labels must be the same allocation.
    a = out.loc[out["scenario_name"].eq("emerging")].set_index(KEY)[["A_P", "Q_P"]].sort_index()
    b = out.loc[out["scenario_name"].eq("mature-market high")].set_index(KEY)[["A_P", "Q_P"]].sort_index()
    if not (a.index.equals(b.index) and np.allclose(a, b, rtol=0, atol=1e-9)):
        raise ValueError("'emerging' and 'mature-market high' are no longer identical allocations.")

    out = out.loc[out["scenario_name"].isin(REPRESENTATIVE)].copy()
    out = apply_feedstock_transfer(out)
    require_unique(out, ["allocation_family", *KEY], name="canonical POLYSYS")
    out = out.sort_values(["allocation_family", *KEY]).reset_index(drop=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)

    totals = out.groupby("allocation_family")[["A_P", "Q_P"]].sum()
    print(f"PASS: {len(x):,} retained source rows -> {len(out):,} canonical rows")
    print(totals.round(0).to_string())
    print(f"  output={args.output}")


if __name__ == "__main__":
    main()
