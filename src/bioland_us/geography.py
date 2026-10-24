"""County identifiers and land-type labels shared by every preparation stage."""

from __future__ import annotations

import pandas as pd

LAND_TYPES = {
    "crop": "Crop",
    "cropland": "Crop",
    "pasture": "Pasture",
    "pastureland": "Pasture",
}


def normalize_fips(values: pd.Series) -> pd.Series:
    """Return five-character county FIPS strings; non-numeric codes become missing."""
    x = values.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    x = x.where(x.str.fullmatch(r"\d{1,5}"), pd.NA)
    return x.str.zfill(5)


def normalize_land_type(values: pd.Series) -> pd.Series:
    """Map source land labels to Crop / Pasture; anything else becomes missing."""
    return values.astype("string").str.strip().str.lower().map(LAND_TYPES)
