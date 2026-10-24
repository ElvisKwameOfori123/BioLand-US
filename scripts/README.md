# Python scripts

Run from the repository root. `python scripts/00_run_core.py` runs them in order.
Reusable logic lives in `src/bioland_us/`; scripts only read, call and write.

| Script | Does | Reads | Writes |
|---|---|---|---|
| `00_fetch_public_sources.py` | Download / checksum raw public sources | provider URLs | `data/raw/` |
| `00_run_core.py` | Run the pipeline (`--from-raw`, `--restricted`) | | |
| `00_verify_release.py` | Ledger, privacy and (`--recompute`) reproduction checks | committed tables | |
| `01_validate_behaviour.py` | Stata export agrees with public parameters | restricted export | |
| `02_prepare_polysys.py` | POLYSYS perennial allocation (P01, P02, T01) | raw POLYSYS zip | `polysys_allocation.csv` |
| `03_prepare_land.py` | Census Crop / Pasture land with suppression completion (L01–L04) | raw Quick Stats | `compatible_land.csv`, `land_structures/` |
| `04_prepare_rents.py` | Rent context, national 2022 and Study-A 2012 (R01, R02) | raw NASS exports, CPI | `rent_context.csv`, `studyA_rent_context.csv` |
| `05_build_behavioural_access.py` | p, T1 pooling, κ = s·p for every scenario (C01, T02) | 02, 04, public parameters | `behavioural_access.csv` |
| `06_run_mobilization.py` | Central capacity and mobilization | 05, 03 | `results/deterministic/` |
| `07_run_bootstrap.py` | Paired respondent bootstrap, draw-0 gate (restricted) | Stata export, 02–06 | `results/bootstrap/` |
| `08_run_structural_sensitivity.py` | 10 structural variants, institutional ledger (S02) | 05, land structures | `results/structural/` |
| `09_build_spatial_outputs.py` | County robustness (S01) | 08, 07 | `results/spatial/` |
| `10_transport_robustness.py` | Ratio / offer+rent transports, evidence bounds (B12), regional rent fallback (R03), leave-one-county-out, affordability (E01), capped offers (E02), gate geography and deficit concentration (E03) | 02–06, Stata 05, cost budget | `results/robustness/` |
| `11_build_manuscript_tables.py` | Tables 2–3, land-class table, quoted-numbers ledger, reconciliation ledger | 06–10 | `results/manuscript/`, `results/validation/` |
| `12_make_figures.py` | Main Figs 1–4 and supplementary Figs S1–S6 (numbered as in the paper), read-only from result CSVs (`--skip-maps` without geometry) | `results/`, county geometry | `results/figures/main`, `results/figures/supplementary` |
| `13_build_review_document.py` | Word review file with main figures, draft captions and Tables 1–3 | `results/` | `results/manuscript/BioLandUS_FiguresTables_Review.docx` |
