"""County cash-rent context in constant 2012 dollars.

Hierarchy (decision R02), for each county x land type and a reference year Y:
    COUNTY_EXACT    same county and land type in year Y
    COUNTY_NEAREST  same county and land type, nearest year within +/- window
                    (ties go to the earlier year)
    STATE           official state rent for the same land type in year Y
    UNSUPPORTED     none of the above; rent stays missing, never zero
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def to_2012_dollars(nominal: pd.Series, years: pd.Series, cpi: pd.Series) -> pd.Series:
    """Deflate nominal values with an annual CPI-U series indexed by year."""
    missing = sorted(set(years.dropna().astype(int)) - set(cpi.index.astype(int)))
    if missing:
        raise ValueError(f"CPI table lacks years {missing}.")
    return nominal * float(cpi.loc[2012]) / years.map(cpi).astype(float)


def rent_context(
    targets: pd.DataFrame,
    county: pd.DataFrame,
    state: pd.DataFrame | None,
    cpi: pd.Series,
    *,
    reference_year: int,
    window: int = 3,
) -> pd.DataFrame:
    """Attach a rent to every target (fips, land_type) cell.

    county : fips, land_type, year, rent_nominal
    state  : state_fips, land_type, year, rent_nominal (or None)
    """
    t = targets[["fips", "land_type"]].drop_duplicates().copy()
    t["state_fips"] = t["fips"].str[:2]

    c = county.loc[county["rent_nominal"].notna()].copy()
    c["gap"] = (c["year"] - reference_year).abs()
    c = c.loc[c["gap"] <= window].sort_values(["fips", "land_type", "gap", "year"])
    best = c.drop_duplicates(["fips", "land_type"])[["fips", "land_type", "year", "rent_nominal"]]

    out = t.merge(best, on=["fips", "land_type"], how="left", validate="1:1")
    out["rent_tier"] = np.where(
        out["year"].eq(reference_year),
        "COUNTY_EXACT",
        np.where(out["year"].notna(), "COUNTY_NEAREST", "UNSUPPORTED"),
    )

    if state is not None:
        s = state.loc[state["year"].eq(reference_year) & state["rent_nominal"].notna()]
        s = s[["state_fips", "land_type", "rent_nominal"]].rename(columns={"rent_nominal": "_state_rent"})
        out = out.merge(s, on=["state_fips", "land_type"], how="left", validate="m:1")
        use = out["rent_tier"].eq("UNSUPPORTED") & out["_state_rent"].notna()
        out.loc[use, "rent_nominal"] = out.loc[use, "_state_rent"]
        out.loc[use, "year"] = reference_year
        out.loc[use, "rent_tier"] = "STATE"
        out = out.drop(columns="_state_rent")

    out["rent_supported"] = out["rent_tier"].ne("UNSUPPORTED")
    out["rent_2012usd_per_acre"] = np.nan
    ok = out["rent_supported"]
    out.loc[ok, "rent_2012usd_per_acre"] = to_2012_dollars(
        out.loc[ok, "rent_nominal"], out.loc[ok, "year"].astype(int), cpi
    )
    return out.rename(columns={"year": "rent_year"})
