"""Build compatible county Crop and Pasture land from the raw 2022 Census of Agriculture.

Input
    data/raw/qs.census2022.txt.gz   (USDA NASS Quick Stats bulk file)

Census items (SOURCE CENSUS, YEAR 2022, DOMAIN TOTAL), decision L01
    CROP_TOTAL     AG LAND, CROPLAND - ACRES
    CROP_PASTURED  AG LAND, CROPLAND, PASTURED ONLY - ACRES
    PASTURE_PERM   AG LAND, PASTURELAND, (EXCL CROPLAND & WOODLAND) - ACRES
    OWNED, RENTED  AG LAND, OWNED / RENTED FROM OTHERS, IN FARMS - ACRES (weights only)

Compatible land (decision L02)
    B_Crop    = CROP_TOTAL - CROP_PASTURED
    B_Pasture = CROP_PASTURED + PASTURE_PERM

Suppression completion (decision L03)
    A county row absent from Quick Stats is zero acres (state totals close exactly
    under that reading in every state without suppression). "(D)" cells share the
    exact state residual (bioland_us.landbase.allocate_residual):
      FARMLAND  [central]     weights = county land in farms (owned + rented)
      EQUAL     [sensitivity] equal weights
    OWNED and RENTED are themselves completed with equal weights.
    Nesting CROP_PASTURED <= CROP_TOTAL is enforced: CROP_TOTAL is completed with
    disclosed CROP_PASTURED as lower bound, then CROP_PASTURED with the completed
    CROP_TOTAL as upper bound.
    Alaska is excluded: POLYSYS allocates nothing there and its Census areas are
    not standard county FIPS.
    Where the state total itself is suppressed (CROP_PASTURED in Arizona and Rhode
    Island) the suppressed counties stay unresolved (decision L04); the national
    model carries them as lower/upper bounds.

Outputs
    data/frozen/public/compatible_land.csv              central (FARMLAND)
    data/frozen/public/land_structures/<SURFACE>.csv    every surface
    data/frozen/public/census_completion_ledger.csv     county x item provenance
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from bioland_us.landbase import allocate_residual

ITEMS = {
    "AG LAND, CROPLAND - ACRES": "CROP_TOTAL",
    "AG LAND, CROPLAND, PASTURED ONLY - ACRES": "CROP_PASTURED",
    "AG LAND, PASTURELAND, (EXCL CROPLAND & WOODLAND) - ACRES": "PASTURE_PERM",
    "AG LAND, OWNED, IN FARMS - ACRES": "OWNED",
    "AG LAND, RENTED FROM OTHERS, IN FARMS - ACRES": "RENTED",
}
COLUMNS = ["SOURCE_DESC", "YEAR", "DOMAIN_DESC", "SHORT_DESC", "AGG_LEVEL_DESC",
           "STATE_FIPS_CODE", "COUNTY_CODE", "COUNTY_NAME", "VALUE"]
SURFACES = ["FARMLAND", "EQUAL"]
EXCLUDED_STATES = {"02"}
NOISE = 1e-6


def extract_items(census: Path, cache: Path) -> pd.DataFrame:
    """Stream the Quick Stats bulk file once and cache the five land items."""
    if cache.exists() and cache.stat().st_mtime > census.stat().st_mtime:
        return pd.read_csv(cache, dtype="string")
    parts = []
    reader = pd.read_csv(census, sep="\t", dtype="string", usecols=COLUMNS,
                         chunksize=500_000, compression="gzip")
    for chunk in reader:
        keep = (
            chunk["SOURCE_DESC"].eq("CENSUS")
            & chunk["YEAR"].eq("2022")
            & chunk["DOMAIN_DESC"].eq("TOTAL")
            & chunk["SHORT_DESC"].isin(ITEMS)
            & chunk["AGG_LEVEL_DESC"].isin(["COUNTY", "STATE"])
        )
        parts.append(chunk.loc[keep])
    out = pd.concat(parts, ignore_index=True)
    cache.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(cache, index=False)
    return out


def tidy(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Return county values (wide, NaN = suppressed) and state totals."""
    x = raw.copy()
    x["item"] = x["SHORT_DESC"].map(ITEMS)
    x["state"] = x["STATE_FIPS_CODE"].str.zfill(2)
    text = x["VALUE"].str.strip()
    x["acres"] = pd.to_numeric(text.str.replace(",", "", regex=False), errors="coerce").astype(float)
    bad = x["acres"].isna() & ~text.eq("(D)")
    if bad.any():
        raise ValueError(f"Unexpected Census value codes: {sorted(text[bad].unique())}")
    x = x.loc[~x["state"].isin(EXCLUDED_STATES)]

    # A suppressed state total leaves its suppressed counties unresolved (L04).
    state = x.loc[x["AGG_LEVEL_DESC"].eq("STATE")].set_index(["state", "item"])["acres"]

    county = x.loc[x["AGG_LEVEL_DESC"].eq("COUNTY")].copy()
    county["fips"] = county["state"] + county["COUNTY_CODE"].str.zfill(3)
    names = county.drop_duplicates("fips").set_index("fips")["COUNTY_NAME"]
    items = list(ITEMS.values())
    suppressed = (
        county.assign(d=county["acres"].isna())
        .pivot(index="fips", columns="item", values="d")
        .reindex(columns=items)
        .fillna(False)
        .astype(bool)
    )
    # Absent rows are zero acres; suppressed cells stay NaN.
    wide = (
        county.pivot(index="fips", columns="item", values="acres")
        .reindex(columns=items)
        .astype(float)
        .fillna(0.0)
        .mask(suppressed)
    )
    wide.insert(0, "county_name", names)
    wide.insert(0, "state", wide.index.str[:2])
    return wide, state


def complete_item(wide, state, item, weights, lower=None, upper=None):
    """Fill suppressed cells of one item, state by state."""
    out = wide[item].copy()
    for st, g in wide.groupby("state"):
        miss = g.index[g[item].isna()]
        total = state.get((st, item), np.nan)
        if len(miss) == 0 or np.isnan(total):
            continue
        residual = float(total - g[item].sum(skipna=True))
        lo = None if lower is None else lower.loc[miss].fillna(0.0).to_numpy()
        hi = None if upper is None else upper.loc[miss].to_numpy()
        w = np.ones(len(miss)) if weights is None else weights.loc[miss].to_numpy()
        out.loc[miss] = allocate_residual(residual, w, lo, hi)
    return out


def build_surface(wide: pd.DataFrame, state: pd.Series, surface: str) -> pd.DataFrame:
    done = wide.copy()
    done["OWNED"] = complete_item(wide, state, "OWNED", None)
    done["RENTED"] = complete_item(wide, state, "RENTED", None)
    weights = None if surface == "EQUAL" else done["OWNED"] + done["RENTED"]

    done["CROP_TOTAL"] = complete_item(wide, state, "CROP_TOTAL", weights, lower=wide["CROP_PASTURED"])
    done["CROP_PASTURED"] = complete_item(wide, state, "CROP_PASTURED", weights, upper=done["CROP_TOTAL"])
    done["PASTURE_PERM"] = complete_item(wide, state, "PASTURE_PERM", weights)

    for item in ITEMS.values():
        totals = state.xs(item, level="item").dropna()
        closure = done.groupby("state")[item].sum(min_count=1).reindex(totals.index) - totals
        if closure.dropna().abs().max() > 1e-6 * max(1.0, totals.max()):
            raise AssertionError(f"{surface}: {item} does not close to state totals.")
    if (done["CROP_PASTURED"] > done["CROP_TOTAL"] + NOISE).any():
        raise AssertionError(f"{surface}: cropland pastured exceeds total cropland.")

    b_crop = done["CROP_TOTAL"] - done["CROP_PASTURED"]
    b_pasture = done["CROP_PASTURED"] + done["PASTURE_PERM"]
    long = pd.concat(
        [
            pd.DataFrame({"fips": done.index, "land_type": "Crop", "B": b_crop.to_numpy()}),
            pd.DataFrame({"fips": done.index, "land_type": "Pasture", "B": b_pasture.to_numpy()}),
        ],
        ignore_index=True,
    )
    if (long["B"] < -NOISE).any():
        raise AssertionError(f"{surface}: negative compatible land beyond rounding.")
    long["B"] = long["B"].clip(lower=0.0)
    long["landbase_structure"] = surface
    return long


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--census", type=Path, default=Path("data/raw/qs.census2022.txt.gz"))
    parser.add_argument("--cache", type=Path, default=Path("data/interim/census_land_items.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/frozen/public/compatible_land.csv"))
    parser.add_argument("--structures-dir", type=Path, default=Path("data/frozen/public/land_structures"))
    parser.add_argument("--ledger", type=Path, default=Path("data/frozen/public/census_completion_ledger.csv"))
    args = parser.parse_args()

    wide, state = tidy(extract_items(args.census, args.cache))

    args.structures_dir.mkdir(parents=True, exist_ok=True)
    surfaces = {}
    for surface in SURFACES:
        surfaces[surface] = build_surface(wide, state, surface)
        surfaces[surface].to_csv(args.structures_dir / f"{surface}.csv", index=False)
    surfaces["FARMLAND"].drop(columns="landbase_structure").to_csv(args.output, index=False)

    ledger = wide[["state", "county_name"]].copy()
    for item in ITEMS.values():
        unresolved = wide["state"].map(lambda s, i=item: np.isnan(state.get((s, i), np.nan)))
        ledger[f"{item}_status"] = np.select(
            [~wide[item].isna(), unresolved], ["DISCLOSED", "UNRESOLVED_STATE_TOTAL"], "COMPLETED"
        )
    ledger.reset_index().to_csv(args.ledger, index=False)

    n_completed = int(wide[list(ITEMS.values())].isna().sum().sum())
    totals = pd.concat(surfaces.values()).groupby(["landbase_structure", "land_type"])["B"].sum()
    print(f"PASS: {len(wide):,} counties, {n_completed} suppressed cells completed per surface.")
    print((totals / 1e6).round(2).rename("million acres").to_string())
    print(f"  central={args.output}")


if __name__ == "__main__":
    main()
