# BioLand-US

**Behavioural and contractual land access shape prospective U.S. perennial-biomass mobilization**

BioLand-US is a spatially explicit, behaviourally and institutionally constrained implementation model. It asks whether a prospective biomass allocation can be supported by the land, landholder participation and contractual access required to deliver it.

```text
techno-economic allocation
        ↓
compatible land
        ↓
behavioural access
        ↓
contractual capacity
        ↓
mobilized biomass
        ↓
spatial robustness
```

The central distinction is:

```text
land can be technically suitable
!= economically allocated
!= contractually accessible
```

## Repository purpose

This repository contains the **clean manuscript-facing analysis**, not the full development history. Forensic scripts, failed variants, temporary audits and local-path debugging code were used during model construction but are not required to reproduce the paper once the scientific rules were frozen.

The public workflow keeps the final calculations and validation gates while excluding obsolete development clutter.

## Code structure

### Stata: behavioural estimation

```text
stata/
├── 00_run_behaviour.do
├── 01_prepare_behaviour.do
├── 02_estimate_participation.do
├── 03_reconstruct_conditional_acreage.do
├── 04_export_behaviour.do
└── 05_validate_behaviour.do
```

Stata 18.5 is authoritative for the Study-A behavioural estimation and restricted-data reconstruction.

### Python: national implementation model

```text
scripts/
├── 00_run_core.py
├── 01_validate_behaviour.py
├── 02_prepare_polysys.py
├── 03_prepare_land.py
├── 04_prepare_rents.py
├── 05_build_behavioural_access.py
├── 06_run_mobilization.py
├── 07_run_bootstrap.py
├── 08_run_structural_sensitivity.py
├── 09_build_spatial_outputs.py
└── 10_make_figures.py
```

Reusable scientific functions live in `src/bioland_us/`.

## Frozen analytical architecture

The retained POLYSYS pathway uses 2041, a US$70 per dry ton biomass-price case, Crop and Pasture land, and seven perennial resources. Duplicate upstream scenario labels are retained for provenance but robustness summaries use three independent allocation families.

Study-A behavioural transport uses the frozen smooth log-dollar model:

```text
logit(p) =
    -6.017543
    + 0.943158 ln(offer)
    - 0.081661 I(10-year)
    + 0.0214773 I(Pasture)
    + 0.746083 I(Switchgrass)
```

Conditional acreage is not made compensation-responsive. The central all-accept representation is 0.863337, with pre-specified lower, IPW and upper representations retained as separate sensitivities.

The explicit feedstock transfer is:

```text
Switchgrass, Miscanthus, Energy cane -> experimental Switchgrass archetype
Poplar, Willow, Eucalyptus, Pine      -> experimental Poplar archetype
```

The active institutional specification is `T1_POOLED_BEHAVIOURAL_TRANSMISSION`. T2-T4 remain explicitly deferred rather than being assigned unsupported national weights.

## Scientific guardrails

- POLYSYS is fixed upstream; BioLand-US does not re-optimize it.
- Several feedstocks may draw on one county-by-land contractual-capacity pool.
- `b = p × s` is a landholder-level behavioural response, not automatically national accessible acreage.
- Unsupported rent cells remain unsupported and are never recoded to zero.
- Zero contractual capacity with positive upstream acreage gives `rho = inf` and `lambda = 0`.
- Statistical bootstrap uncertainty and structural sensitivity remain separate.
- Maps describe spatial implementation exposure under transported experimental behaviour, not observed county willingness.
- Plotting code does not re-estimate the model.

## Data boundary

Restricted KBS respondent-level data are not redistributed. Public and restricted input contracts are documented under `data/` and `docs/`. No restricted microdata should ever be committed.

## Installation

```bash
git clone https://github.com/ElvisKwameOfori123/BioLand-US.git
cd BioLand-US
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

## Reproduction

Behavioural analysis:

```stata
do stata/00_run_behaviour.do
```

Public-source preparation, when rebuilding canonical inputs:

```bash
python scripts/02_prepare_polysys.py --input <retained_polysys_csv>
python scripts/03_prepare_land.py --input <completed_census_components_csv>
python scripts/04_prepare_rents.py --county <county_rents_csv> --state <state_rents_csv> --cpi <cpi_csv>
```

Deterministic core:

```bash
python scripts/00_run_core.py
```

Uncertainty, robustness and figures:

```bash
python scripts/07_run_bootstrap.py
python scripts/08_run_structural_sensitivity.py
python scripts/09_build_spatial_outputs.py
python scripts/10_make_figures.py
```

## Author

**Elvis Kwame Ofori**  
University of Galway
