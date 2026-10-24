# Public frozen tables

Small, non-disclosive tables that are versioned so a fresh clone can rerun the
national model without the large raw sources. Each is produced by a script;
the only hand-entered inputs are the two marked "bundled".

| File | Made by | Content |
|---|---|---|
| `behaviour_parameters_public.csv` | `stata/04_export_behaviour.do` | Participation coefficients and conditional-acreage shares (aggregates only) |
| `polysys_allocation.csv` | `scripts/02_prepare_polysys.py` | POLYSYS 2041 / $70 perennial allocation, three families |
| `compatible_land.csv` | `scripts/03_prepare_land.py` | Census 2022 Crop / Pasture land, FARMLAND completion (central) |
| `land_structures/*.csv` | `scripts/03_prepare_land.py` | Every Census completion surface |
| `census_completion_ledger.csv` | `scripts/03_prepare_land.py` | Disclosed / completed / unresolved status per county and item |
| `rent_context.csv` | `scripts/04_prepare_rents.py` | 2022 rent context for POLYSYS cells (2012 $) |
| `studyA_rent_context.csv` | `scripts/04_prepare_rents.py` | 2012 rent context for the Study-A survey counties |
| `cpi_u_annual.csv` | bundled | BLS CPI-U annual averages |
| `michigan_state_rent_2012.csv` | bundled | NASS 2012 Michigan state pasture rent (Study-A fallback) |
| `perennial_cost_budget.csv` | bundled | Switchgrass / miscanthus production budget (low, high), Energy Economics supplement, PII S0140988317302906 (E01) |

`behavioural_access.csv` is also written here by script 05 but is large and
git-ignored; `scripts/00_run_core.py` rebuilds it.
