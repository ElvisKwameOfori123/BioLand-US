# BioLand-US

**Landowner participation determines how much modelled biomass the United States can mobilize**

BioLand-US is a reproducible implementation-layer modelling framework for asking:

> Given a prospective perennial-biomass allocation, how much can actually be matched to voluntary contractual land access?

The framework links experimental landholder behaviour, county agricultural land, USDA cash-rent context, spatially explicit POLYSYS perennial-biomass allocations, contractual capacity, uncertainty, and spatial robustness.

```
modelled biomass allocation
        !=
contractually accessible land
        !=
mobilized biomass
```

## What is in this repository

The public repository contains the **clean analysis code**, not the long development history.

The development project used many forensic scripts, blocked variants, reruns, and one-off diagnostics to audit the science. Those are intentionally not reproduced one-for-one here. The public code keeps the frozen scientific decisions while removing duplicated logic, local absolute paths, temporary diagnostics, obsolete variants, and restricted data.

### Stata

Stata 18.5 is authoritative for the behavioural estimation:

```
stata/
├── 00_master.do
├── 01_prepare_restricted_behaviour.do
├── 02_estimate_behaviour.do
├── 03_freeze_intensive.do
├── 04_export_behaviour.do
└── 05_validate_behaviour.do
```

The final validation script contains regression tests against the frozen manuscript coefficients, predictive margins, sample counts, and central conditional-acreage value.

### Python

Python is authoritative for national integration, capacity accounting, uncertainty propagation, spatial outputs, and publication figures:

```
scripts/
├── 01_check_behaviour_exports.py
├── 02_prepare_polysys.py
├── 03_prepare_land.py
├── 04_prepare_rents.py
├── 05_build_behavioural_access.py
├── 06_run_mobilization.py
├── 07_run_bootstrap.py
├── 08_run_structural_sensitivity.py
├── 09_build_spatial_outputs.py
├── 10_make_figures.py
├── plot_main_figures.py
└── run_pipeline.py
```

Reusable logic lives in `src/bioland_us/` rather than being copied between stage scripts.

## Scientific guardrails

- POLYSYS allocations are fixed upstream pathways; BioLand-US does not re-optimize POLYSYS.
- Several feedstocks may draw on one county-by-land pool, so contractual capacity is defined once per pool.
- Behavioural access `b = p × s` is distinct from national acreage access.
- The current main analysis implements pooled T1 transmission only; unsupported T2-T4 weights are not invented.
- Unsupported rent evidence remains unsupported and is never silently recoded to zero.
- Statistical uncertainty and structural sensitivity remain separate.
- Zero-capacity binding cells use `rho = inf` and `lambda = 0`; no arbitrary finite pressure value is imposed.
- Maps represent spatial implementation exposure under transported experimental behaviour, not county-specific willingness.
- Plotting code reads frozen reporting outputs and never re-estimates the model.

## Data

Restricted respondent-level behavioural microdata are **not redistributed**.

Public source data and locally derived canonical inputs are documented in [data/README.md](data/README.md). Restricted behavioural inputs required by the Stata code must be obtained through the relevant data-access route and placed locally under `data/restricted/`.

The repository `.gitignore` prevents raw, restricted, interim, local-cache, and temporary files from being committed accidentally.

## Installation

The Python code targets Python 3.12.

```bash
git clone https://github.com/ElvisKwameOfori123/BioLand-US.git
cd BioLand-US

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -e .
```

Stata users should run Stata 18.5 from the repository root.

## Reproducing the behavioural estimates

After placing the restricted canonical behavioural inputs locally:

```stata
cd ".../BioLand-US"
do stata/00_master.do
```

The Stata validation stage fails if the frozen paper sample, coefficients, margins, or conditional-acreage mean are not reproduced.

## Reproducing the national analysis

Public-source preparation stages are explicit:

```bash
python scripts/02_prepare_polysys.py --input <retained_polysys_csv>
python scripts/03_prepare_land.py --input <completed_census_components_csv>
python scripts/04_prepare_rents.py --county <county_rents_csv> --state <state_rents_csv> --cpi <cpi_csv>
```

Once canonical behavioural, resource, land, and rent inputs exist:

```bash
python scripts/run_pipeline.py
```

The paired behavioural bootstrap is available separately:

```bash
python scripts/07_run_bootstrap.py
```

## Reproducing the publication figures

The final figure generator reads the frozen reporting workbook and county geometry:

```bash
python scripts/10_make_figures.py
```

It exports PDF, SVG, and high-resolution PNG figures.

## Repository structure

```
BioLand-US/
├── config/
├── data/
├── docs/
├── scripts/
├── src/bioland_us/
├── stata/
├── tests/
├── .gitignore
├── CITATION.cff
├── LICENSE
├── pyproject.toml
└── README.md
```

## Important reproducibility boundary

The clean public scripts are the manuscript-facing analytical code. They deliberately do not preserve every forensic development script. Where a difficult source-reconstruction step produced a frozen canonical input, the public repository documents that input contract and retains validation tests rather than publishing obsolete failed variants.

No restricted respondent-level data should ever be committed.

## Author

**Elvis Kwame Ofori**  
University of Galway

## Licence

The repository currently uses the licence already attached to the project. Third-party data remain subject to their original licences, access conditions, and disclosure restrictions.
