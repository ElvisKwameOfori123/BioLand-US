# Python analysis scripts

The public Python workflow is intentionally shorter than the development pipeline.

| Script | Purpose |
|---|---|
| `01_check_behaviour_exports.py` | Validate restricted Stata exports before national modelling |
| `02_prepare_polysys.py` | Standardize the retained perennial allocation and attach the explicit treatment-class transfer |
| `03_prepare_land.py` | Construct mutually interpretable Crop and Pasture pools from completed Census components |
| `04_prepare_rents.py` | Apply the frozen county / near-year / state rent hierarchy and convert to 2012 dollars |
| `05_build_behavioural_access.py` | Evaluate participation, conditional acreage, and behavioural access |
| `06_run_mobilization.py` | Compute contractual capacity, pressure, lambda, mobilized acreage and biomass |
| `07_run_bootstrap.py` | Paired respondent bootstrap of behavioural parameters |
| `08_run_structural_sensitivity.py` | Four intensive representations × three Census land structures |
| `09_build_spatial_outputs.py` | Build map-ready county implementation-exposure outputs |
| `10_make_figures.py` | Run the publication plotting entry point |
| `plot_main_figures.py` | Draw the four manuscript figures from the frozen reporting workbook |
| `run_pipeline.py` | Orchestrate the deterministic public national pipeline |

Reusable scientific functions belong under `src/bioland_us/`.

The scripts fail loudly on missing required inputs. They do not silently create zeros, cap pressure values, invent institutional parameters, or combine statistical and structural uncertainty.
