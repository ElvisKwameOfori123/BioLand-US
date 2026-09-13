# Python analysis scripts

The manuscript-facing Python workflow is intentionally shorter than the development pipeline.

| Script | Purpose |
|---|---|
| `00_run_core.py` | Run the deterministic core from validated canonical inputs |
| `01_validate_behaviour.py` | Validate canonical Stata behavioural exports |
| `02_prepare_polysys.py` | Standardize the retained POLYSYS perennial allocation |
| `03_prepare_land.py` | Build compatible Crop and Pasture land pools |
| `04_prepare_rents.py` | Apply the frozen county / near-year / state rent hierarchy |
| `05_build_behavioural_access.py` | Evaluate participation, conditional acreage and `b = p × s` |
| `06_run_mobilization.py` | Compute contractual capacity and biomass mobilization under T1 |
| `07_run_bootstrap.py` | Paired respondent bootstrap for statistical uncertainty |
| `08_run_structural_sensitivity.py` | Evaluate implemented structural alternatives |
| `09_build_spatial_outputs.py` | Create county-level spatial robustness outputs |
| `10_make_figures.py` | Draw manuscript figures from frozen reporting outputs |

Reusable scientific functions live in `src/bioland_us/`.

## Boundaries

- `02-04` are source-preparation utilities and require explicit source files.
- `05-06` form the deterministic implementation core.
- `07` is statistical uncertainty only.
- `08` is structural sensitivity only.
- `09` builds map-ready evidence without re-estimating behaviour.
- `10` is plotting only.
- T2-T4 remain deferred until defensible national formulas and weights exist.
- Unsupported rent remains missing, never zero.
