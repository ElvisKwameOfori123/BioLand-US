"""Build cash-rent context from the raw NASS exports.

Inputs
    data/raw/9A9F55D7-E267-38C6-ACB9-DF106291B5A7.csv   county cash rents (wide export)
    data/raw/73DE05FF-2AD9-384C-AFB1-E47106AFC525.csv   2022 state cash rents
    data/frozen/public/cpi_u_annual.csv                 CPI-U annual averages

Land-type mapping (decision R01)
    Crop    = RENT, CASH, CROPLAND, NON-IRRIGATED  (irrigated rent is excluded)
    Pasture = RENT, CASH, PASTURELAND

Outputs (hierarchy in bioland_us.rents, decision R02)
    data/frozen/public/rent_context.csv          POLYSYS cells, reference year 2022,
                                                 state 2022 fallback
    data/frozen/public/studyA_rent_context.csv   Study-A survey counties, reference
                                                 year 2012, Michigan 2012 state
                                                 pasture rent as fallback
                                                 (data/frozen/public/michigan_state_rent_2012.csv)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from bioland_us.geography import normalize_fips
from bioland_us.rents import rent_context

COUNTY_COLUMNS = {
    "RENT, CASH, CROPLAND, NON-IRRIGATED - EXPENSE, MEASURED IN $ / ACRE  -  <b>VALUE</b>": "Crop",
    "RENT, CASH, PASTURELAND - EXPENSE, MEASURED IN $ / ACRE  -  <b>VALUE</b>": "Pasture",
}
STATE_ITEMS = {
    "RENT, CASH, CROPLAND, NON-IRRIGATED - EXPENSE, MEASURED IN $ / ACRE": "Crop",
    "RENT, CASH, PASTURELAND - EXPENSE, MEASURED IN $ / ACRE": "Pasture",
}
STUDY_A_FIPS = ["26005", "26015", "26023", "26067", "26073", "26091",
                "26093", "26123", "26145", "26151", "26157", "26159"]


def to_number(values: pd.Series) -> pd.Series:
    """NASS values: numbers with commas; "(D)", "(NA)" and blanks become missing."""
    return pd.to_numeric(values.astype("string").str.replace(",", "", regex=False).str.strip(),
                         errors="coerce").astype(float)


def county_panel(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, dtype="string")
    # "OTHER (COMBINED) COUNTIES" rows carry no county code and are not county rents.
    raw = raw.loc[raw["Geo Level"].eq("COUNTY") & raw["Period"].eq("YEAR") & raw["County ANSI"].notna()]
    fips = normalize_fips(raw["State ANSI"].str.zfill(2) + raw["County ANSI"].str.zfill(3))
    parts = [
        pd.DataFrame({"fips": fips, "land_type": land,
                      "year": pd.to_numeric(raw["Year"]).astype(int),
                      "rent_nominal": to_number(raw[col])})
        for col, land in COUNTY_COLUMNS.items()
    ]
    panel = pd.concat(parts, ignore_index=True)
    panel = panel.loc[panel["fips"].notna() & panel["rent_nominal"].notna()]
    if panel.duplicated(["fips", "land_type", "year"]).any():
        raise ValueError("County rent panel is not unique by fips x land x year.")
    return panel


def state_table(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, dtype="string")
    raw = raw.loc[raw["Geo Level"].eq("STATE") & raw["Data Item"].isin(STATE_ITEMS)]
    out = pd.DataFrame({
        "state_fips": raw["State ANSI"].str.zfill(2),
        "land_type": raw["Data Item"].map(STATE_ITEMS),
        "year": pd.to_numeric(raw["Year"]).astype(int),
        "rent_nominal": to_number(raw["Value"]),
    })
    if out.duplicated(["state_fips", "land_type", "year"]).any():
        raise ValueError("State rent table is not unique by state x land x year.")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--county", type=Path, default=Path("data/raw/9A9F55D7-E267-38C6-ACB9-DF106291B5A7.csv"))
    parser.add_argument("--state", type=Path, default=Path("data/raw/73DE05FF-2AD9-384C-AFB1-E47106AFC525.csv"))
    parser.add_argument("--cpi", type=Path, default=Path("data/frozen/public/cpi_u_annual.csv"))
    parser.add_argument("--universe", type=Path, default=Path("data/frozen/public/polysys_allocation.csv"))
    parser.add_argument("--michigan-state", type=Path, default=Path("data/frozen/public/michigan_state_rent_2012.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/frozen/public/rent_context.csv"))
    parser.add_argument("--output-study-a", type=Path, default=Path("data/frozen/public/studyA_rent_context.csv"))
    args = parser.parse_args()

    county = county_panel(args.county)
    state = state_table(args.state)
    cpi = pd.read_csv(args.cpi).set_index("year")["cpi_u_annual_average"]

    universe = pd.read_csv(args.universe, dtype={"fips": "string"})
    national = rent_context(universe, county, state, cpi, reference_year=2022)
    national.to_csv(args.output, index=False)

    study_a = pd.DataFrame(
        [(f, land) for f in STUDY_A_FIPS for land in ("Crop", "Pasture")],
        columns=["fips", "land_type"],
    )
    mi = pd.read_csv(args.michigan_state, dtype={"state_ansi": "string"})
    mi_state = pd.DataFrame({
        "state_fips": mi["state_ansi"].str.zfill(2),
        "land_type": mi["land_type"],
        "year": mi["year"].astype(int),
        "rent_nominal": mi["rent_nominal_usd_per_acre"].astype(float),
    })
    study = rent_context(study_a, county, mi_state, cpi, reference_year=2012)
    if not study["rent_supported"].all():
        raise ValueError("Every Study-A survey county needs a 2012 county rent context.")
    study.to_csv(args.output_study_a, index=False)

    print("PASS: rent context written.")
    print(national["rent_tier"].value_counts().to_string())
    print(f"  national cells={len(national):,}  unsupported={int((~national['rent_supported']).sum())}")
    print(f"  Study-A cells={len(study)}  tiers={study['rent_tier'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
