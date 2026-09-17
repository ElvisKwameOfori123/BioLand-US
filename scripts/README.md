# Python analysis scripts

BioLand-US separates the deterministic implementation core, statistical uncertainty,
structural sensitivity, behavioural-transport robustness and manuscript reporting.

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
| `08_run_structural_sensitivity.py` | Evaluate implemented intensive-margin × land-completion alternatives |
| `09_build_spatial_outputs.py` | Create county-level spatial robustness outputs |
| `10_transport_robustness.py` | Propagate absolute-dollar, offer/rent and offer+rent transport specifications; report Crop/Pasture heterogeneity |
| `11_figure1_identity_audit.py` | Verify `b = p × s` and audit the Figure 1c aggregation |
| `12_support_bounded_extrapolation.py` | Bound out-of-support behaviour using monotonicity only |
| `13_build_figure_workbook.py` | Import audited outputs into the frozen reporting workbook and run reporting checks |
| `14_make_figures.py` | Read the final workbook and draw the five main figures plus Extended Data Figure 1; does not write to the workbook |

Reusable scientific functions live in `src/bioland_us/`.

## Scientific boundaries

- The randomized KBS monetary treatment is interpreted as an **annual land-rental offer per acre per year**, not a biomass farmgate price.
- The primary participation transport remains the frozen absolute-dollar model.
- The pure offer/rent specification is a stress test. Its proportionality restriction is rejected in the rent-matched experimental sample (`p = 0.0002`).
- The unrestricted offer+rent specification is the preferred rent-context robustness test.
- The evidence-bounded analysis leaves within-support participation unchanged and uses monotonic bounds only below US$50 and above US$300.
- T2-T4 institutional alternatives remain deferred until defensible national formulas and weights exist.
- Unsupported rent remains missing, never zero.
- Statistical, structural, transport, evidence-support, allocation-family and contract-duration sensitivities remain separate classes rather than being combined into one interval.

## Current headline robustness checks

For the national support-balanced reference (`m = 6.7088`, 5-year contract, family-balanced):

- primary deterministic `M_Q`: about 78.67%;
- unrestricted offer+rent sensitivity: about 75.91%;
- evidence-bounded monotonic interval: about 72.47% to 81.91%;
- pure offer/rent stress test: about 98.27%, reported separately because the ratio restriction is rejected.

The primary transport is hard-reconciled to frozen Stage 07G before robustness outputs are accepted.

## Reporting architecture

The scientific direction is one-way:

```text
frozen upstream outputs
        ↓
10-12 robustness / audit
        ↓
13_build_figure_workbook.py
        ↓
BioLandUS_FigureWorkbook_v7_FINAL.xlsx
        ↓
14_make_figures.py
        ↓
Figures 1-5 + Extended Data Figure 1
```

The plotting script is read-only with respect to the workbook.

The final workbook is a generated reporting artefact. It depends on the validated local seed workbook plus frozen upstream outputs, including products derived from restricted Study-A data. Those inputs are intentionally not treated as public raw data. For public release, the repository retains the builder, plotter, manuscript-facing CSV outputs, validation ledger and source provenance. Run the reporting stage with an authorized local seed using:

```bash
python scripts/13_build_figure_workbook.py --seed <validated_seed_workbook.xlsx>
python scripts/14_make_figures.py --workbook results/figures/BioLandUS_FigureWorkbook_v7_FINAL.xlsx
```
