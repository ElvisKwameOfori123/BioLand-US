# Data

BioLand-US keeps the GitHub repository lean. Raw third-party archives and
restricted respondent-level records are **not** duplicated in the repository.
The clean code instead documents the exact source files, expected local names,
checksums and the small canonical tables required by the manuscript analysis.

See [source_registry.csv](source_registry.csv) for the complete source ledger.

## What is actually required

Five public source groups and one restricted behavioural source support the
identified BioLand-US analysis:

| Clean local name | Role |
|---|---|
| `polysys_biomass_allocation.zip` | POLYSYS/Billion-Ton upstream perennial allocation |
| `census_2022_quickstats.txt.gz` | 2022 Census land and suppression accounting |
| `nass_county_cash_rents.csv` | County cash-rent history |
| `nass_state_cash_rents_2022.csv` | Official 2022 state rent fallback |
| `us_county_geometry_2022.zip` | County geometry for maps |
| `kbs_bioenergy_land_use_survey_2012.zip` | Restricted Study-A behavioural evidence |

The KBS archive is not redistributable through this repository. Its metadata
states that publication of KBS data requires written permission from the lead
investigator/project director and that publications using KBS data must
acknowledge KBS LTER support.

## Local directory layout

```text
data/
├── README.md
├── source_registry.csv
├── raw/                  # public source downloads, gitignored
├── restricted/           # restricted KBS material, gitignored
├── interim/              # regenerable working tables, gitignored
└── frozen/
    ├── public/           # canonical non-disclosive model inputs/outputs
    └── restricted/       # local canonical restricted exports, never committed
```

Recommended clean local names under `data/raw/`:

```text
polysys_biomass_allocation.zip
census_2022_quickstats.txt.gz
nass_county_cash_rents.csv
nass_state_cash_rents_2022.csv
us_county_geometry_2022.zip
```

The restricted survey belongs under `data/restricted/` and should never be
committed.

## Files intentionally outside the core model

The following files may be useful for background or future extensions, but
they are **not inputs to the identified BioLand-US results**:

- the 2024 TOTAL landlord extract, because T2-T4 institutional transmission
  remains deliberately unquantified;
- the USDA Census web-map workbook, because the final land construction uses
  the Quick Stats source and frozen completion surfaces;
- the switchgrass/miscanthus break-even supplementary workbook;
- the NCCOMS/FASOMGHG figure workbook.

The file `BT23_Perennial_Model_Input_v2.csv` is a **superseded development
prototype**. It already contains added tenure and annual-renewal indicators.
It should not be treated as a clean upstream input because the final model
starts from the raw POLYSYS allocation and applies the frozen transformations
explicitly.

## Canonical frozen data

The manuscript-facing Python scripts should operate on clear frozen tables such
as:

```text
data/frozen/public/
├── polysys_allocation.csv
├── compatible_land.csv
├── rent_context.csv
└── behavioural_access.csv
```

and the structural land surfaces:

```text
data/frozen/public/land_structures/
├── JOINT_EQUAL.csv
├── JOINT_OWNED.csv
└── JOINT_RENTED.csv
```

These are derived analysis inputs, not replacements for source provenance.

## Why raw files are not committed

The 2022 Census Quick Stats archive alone is roughly 295 MB, and several source
files have independent redistribution or access conditions. Keeping them out of
GitHub avoids unnecessary duplication and prevents restricted data from being
published accidentally.

The source registry records the SHA-256 hashes of the copies used to build the
clean analysis so that local files can still be verified exactly.
