"""Construct the frozen county-by-land rent context for the POLYSYS universe.

Hierarchy
---------
1. exact county, same land type, 2022
2. same county, same land type, nearest year within ±3 years
   (ties resolved toward the earlier year)
3. official state, same land type, 2022
4. unsupported

All supported rents are converted to constant 2012 US dollars.
Unsupported cells remain missing; they are never interpreted as zero rent.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from bioland_us.validation import require_columns, require_unique


def standardize_land_type(series: pd.Series) -> pd.Series:
    x = series.astype("string").str.strip().str.lower()
    return x.map(
        {
            "crop": "Crop",
            "cropland": "Crop",
            "pasture": "Pasture",
            "pastureland": "Pasture",
        }
    )


def convert_to_2012(
    values: pd.Series,
    years: pd.Series,
    cpi: pd.DataFrame,
) -> pd.Series:
    idx = cpi.set_index("year")["cpi"]
    if 2012 not in idx.index:
        raise ValueError("CPI table must contain 2012.")
    missing_years = sorted(set(years.dropna().astype(int)) - set(idx.index.astype(int)))
    if missing_years:
        raise ValueError(f"CPI table missing years: {missing_years}")
    return values * float(idx.loc[2012]) / years.map(idx)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--universe",
        type=Path,
        default=Path("data/frozen/public/polysys_allocation.csv"),
        help="Canonical POLYSYS allocation used only to define target FIPS × land cells.",
    )
    parser.add_argument("--county", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--cpi", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/frozen/public/rent_context.csv"),
    )
    args = parser.parse_args()

    universe_raw = pd.read_csv(args.universe, dtype={"fips": "string"})
    county = pd.read_csv(
        args.county,
        dtype={"fips": "string", "state_ansi": "string"},
    )
    state = pd.read_csv(args.state, dtype={"state_ansi": "string"})
    cpi = pd.read_csv(args.cpi)

    require_columns(
        universe_raw,
        ["fips", "land_type"],
        name="POLYSYS county-land universe",
    )
    require_columns(
        county,
        ["fips", "land_type", "year", "rent_usd_per_acre"],
        name="county cash rents",
    )
    require_columns(
        state,
        ["state_ansi", "land_type", "year", "rent_usd_per_acre"],
        name="state cash rents",
    )
    require_columns(cpi, ["year", "cpi"], name="CPI")

    universe = universe_raw[["fips", "land_type"]].copy()
    universe["fips"] = (
        universe["fips"]
        .astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(5)
    )
    universe["land_type"] = standardize_land_type(universe["land_type"])
    if universe["land_type"].isna().any():
        raise ValueError("Unrecognized land type in POLYSYS universe.")
    universe = universe.drop_duplicates().reset_index(drop=True)
    universe["state_ansi"] = universe["fips"].str[:2]
    require_unique(universe, ["fips", "land_type"], name="rent target universe")

    county["fips"] = (
        county["fips"]
        .astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(5)
    )
    county["state_ansi"] = county["fips"].str[:2]
    county["land_type"] = standardize_land_type(county["land_type"])
    county["year"] = pd.to_numeric(county["year"], errors="coerce")
    county["rent_usd_per_acre"] = pd.to_numeric(
        county["rent_usd_per_acre"], errors="coerce"
    )
    county = county[
        county["land_type"].notna()
        & county["year"].between(2019, 2025)
        & county["rent_usd_per_acre"].notna()
    ].copy()

    # nearest same-county same-land observation within ±3 years;
    # sort year ascending after distance so a tie chooses the earlier year.
    county["distance_to_2022"] = (county["year"] - 2022).abs()
    county = county.sort_values(
        ["fips", "land_type", "distance_to_2022", "year"]
    )
    county_best = county.drop_duplicates(["fips", "land_type"], keep="first")
    require_unique(county_best, ["fips", "land_type"], name="best county rents")

    state["state_ansi"] = (
        state["state_ansi"]
        .astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(2)
    )
    state["land_type"] = standardize_land_type(state["land_type"])
    state["year"] = pd.to_numeric(state["year"], errors="coerce")
    state["rent_usd_per_acre"] = pd.to_numeric(
        state["rent_usd_per_acre"], errors="coerce"
    )
    state_2022 = state[
        state["year"].eq(2022)
        & state["land_type"].notna()
        & state["rent_usd_per_acre"].notna()
    ].copy()
    require_unique(
        state_2022,
        ["state_ansi", "land_type"],
        name="official state 2022 rents",
    )

    out = universe.merge(
        county_best[
            ["fips", "land_type", "year", "rent_usd_per_acre"]
        ].rename(
            columns={
                "year": "county_year",
                "rent_usd_per_acre": "county_rent_nominal",
            }
        ),
        on=["fips", "land_type"],
        how="left",
        validate="1:1",
    )

    out = out.merge(
        state_2022[
            ["state_ansi", "land_type", "rent_usd_per_acre"]
        ].rename(columns={"rent_usd_per_acre": "state_rent_2022_nominal"}),
        on=["state_ansi", "land_type"],
        how="left",
        validate="m:1",
    )

    out["rent_tier"] = "UNSUPPORTED"
    out["rent_year"] = np.nan
    out["rent_nominal_usd_per_acre"] = np.nan

    has_county = out["county_rent_nominal"].notna()
    exact_2022 = has_county & out["county_year"].eq(2022)
    near_year = has_county & ~out["county_year"].eq(2022)

    out.loc[exact_2022, "rent_tier"] = "COUNTY_2022"
    out.loc[near_year, "rent_tier"] = "COUNTY_NEAREST_PM3"
    out.loc[has_county, "rent_year"] = out.loc[has_county, "county_year"]
    out.loc[has_county, "rent_nominal_usd_per_acre"] = out.loc[
        has_county, "county_rent_nominal"
    ]

    use_state = (
        ~has_county
        & out["state_rent_2022_nominal"].notna()
    )
    out.loc[use_state, "rent_tier"] = "STATE_2022"
    out.loc[use_state, "rent_year"] = 2022
    out.loc[use_state, "rent_nominal_usd_per_acre"] = out.loc[
        use_state, "state_rent_2022_nominal"
    ]

    out["rent_supported"] = out["rent_tier"].ne("UNSUPPORTED")
    out["rent_2012usd_per_acre"] = np.nan
    supported = out["rent_supported"]
    out.loc[supported, "rent_2012usd_per_acre"] = convert_to_2012(
        out.loc[supported, "rent_nominal_usd_per_acre"],
        out.loc[supported, "rent_year"].astype(int),
        cpi,
    )

    if out.loc[~out["rent_supported"], "rent_2012usd_per_acre"].notna().any():
        raise AssertionError("Unsupported rent cells must remain missing.")

    keep = [
        "fips",
        "state_ansi",
        "land_type",
        "rent_supported",
        "rent_tier",
        "rent_year",
        "rent_nominal_usd_per_acre",
        "rent_2012usd_per_acre",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out[keep].to_csv(args.output, index=False)

    print("PASS: rent context constructed on the full POLYSYS county-land universe.")
    print(out["rent_tier"].value_counts(dropna=False).to_string())
    print(f"  target cells={len(out):,}")
    print(f"  supported={int(out['rent_supported'].sum()):,}")
    print(f"  unsupported={int((~out['rent_supported']).sum()):,}")
    print(f"  output={args.output}")


if __name__ == "__main__":
    main()
