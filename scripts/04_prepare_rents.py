"""Construct the county-by-land rent hierarchy in constant 2012 dollars."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from bioland_us.validation import require_columns, require_unique


def to_2012_usd(value: pd.Series, year: pd.Series, cpi: pd.DataFrame) -> pd.Series:
    idx = cpi.set_index("year")["cpi"]
    cpi_2012 = float(idx.loc[2012])
    denom = year.map(idx)
    return value * cpi_2012 / denom


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--county", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--cpi", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/frozen/public/rent_context.csv"),
    )
    args = parser.parse_args()

    county = pd.read_csv(
        args.county, dtype={"fips": "string", "state_ansi": "string"}
    )
    state = pd.read_csv(args.state, dtype={"state_ansi": "string"})
    cpi = pd.read_csv(args.cpi)

    require_columns(
        county,
        ["fips", "state_ansi", "land_type", "year", "rent_usd_per_acre"],
        name="county rents",
    )
    require_columns(
        state,
        ["state_ansi", "land_type", "year", "rent_usd_per_acre"],
        name="state rents",
    )
    require_columns(cpi, ["year", "cpi"], name="CPI")

    county["fips"] = county["fips"].astype("string").str.zfill(5)
    county["state_ansi"] = county["state_ansi"].astype("string").str.zfill(2)
    state["state_ansi"] = state["state_ansi"].astype("string").str.zfill(2)

    county = county[county["year"].between(2019, 2025)].copy()
    county["distance"] = (county["year"] - 2022).abs()
    county["earlier_tiebreak"] = county["year"]
    county = county.sort_values(
        ["fips", "land_type", "distance", "earlier_tiebreak"]
    )
    nearest = county.groupby(["fips", "land_type"], as_index=False).first()
    nearest["tier"] = np.where(nearest["year"].eq(2022), 1, 2)

    state_2022 = state[state["year"].eq(2022)].copy()
    require_unique(state_2022, ["state_ansi", "land_type"], name="state 2022 rents")

    universe = county[["fips", "state_ansi", "land_type"]].drop_duplicates()
    out = universe.merge(
        nearest[["fips", "land_type", "year", "rent_usd_per_acre", "tier"]],
        on=["fips", "land_type"],
        how="left",
        validate="1:1",
    )
    out = out.merge(
        state_2022[["state_ansi", "land_type", "rent_usd_per_acre"]].rename(
            columns={"rent_usd_per_acre": "state_rent_2022"}
        ),
        on=["state_ansi", "land_type"],
        how="left",
        validate="m:1",
    )

    use_state = out["rent_usd_per_acre"].isna() & out["state_rent_2022"].notna()
    out.loc[use_state, "rent_usd_per_acre"] = out.loc[use_state, "state_rent_2022"]
    out.loc[use_state, "year"] = 2022
    out.loc[use_state, "tier"] = 3
    out["rent_supported"] = out["rent_usd_per_acre"].notna()

    out["rent_2012usd_per_acre"] = to_2012_usd(
        out["rent_usd_per_acre"], out["year"], cpi
    )
    out.loc[~out["rent_supported"], "rent_2012usd_per_acre"] = np.nan
    out["rent_tier"] = out["tier"].map(
        {1: "COUNTY_2022", 2: "COUNTY_NEAREST_PM3", 3: "STATE_2022"}
    ).fillna("UNSUPPORTED")

    keep = [
        "fips",
        "state_ansi",
        "land_type",
        "rent_supported",
        "rent_tier",
        "year",
        "rent_2012usd_per_acre",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out[keep].to_csv(args.output, index=False)

    print("PASS: rent hierarchy constructed.")
    print(out["rent_tier"].value_counts(dropna=False).to_string())
    print(f"  output={args.output}")


if __name__ == "__main__":
    main()
