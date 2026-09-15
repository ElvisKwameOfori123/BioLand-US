# BioLand-US

**A reproducible framework for evaluating contractual land-access constraints on prospective U.S. perennial-biomass mobilization**

> **Manuscript status:** in preparation. This README is repository documentation written specifically for the software and reproducibility package. It is not the manuscript abstract, and its wording is intentionally kept separate from the paper.

## Project overview

BioLand-US is a spatially explicit ex ante implementation model that links a fixed upstream perennial-biomass allocation to county agricultural land, annual land-rental offers, experimentally estimated landholder responses and an explicit institutional transmission rule.

The model asks whether biomass acreage that is economically allocated in POLYSYS can also be supported by the land and voluntary contractual participation required for implementation.

BioLand-US therefore keeps four quantities separate:

```text
techno-economic biomass allocation
        ↓
compatible agricultural land
        ↓
contractually accessible land
        ↓
prospectively mobilized biomass
```

This repository contains the clean manuscript-facing code, data contracts, validation tests and non-disclosive results required to reproduce the identified analysis. It does not reproduce every forensic or failed development script used while the model was being built.

## Research question

> Given a fixed perennial-biomass allocation from POLYSYS, how much of that allocation can be matched to experimentally informed contractual land-access capacity, where do capacity constraints occur, and how robust are the conclusions to statistical and structural uncertainty?

BioLand-US does not rerun or re-optimize POLYSYS. It operates as a downstream implementation layer.

## Analytical framework

```text
POLYSYS allocation
        ↓
compatible county land
        ↓
contract offer
        ↓
participation probability, p
        ↓
conditional acreage share, s
        ↓
behavioural land access, b = p × s
        ↓
institutional transmission, b → kappa
        ↓
contractual capacity, K = B × kappa
        ↓
capacity matching
        ↓
mobilized acreage and biomass
        ↓
spatial robustness
```

For county `c` and land pool `l`:

```text
A_P    upstream POLYSYS acreage requirement
Q_P    upstream POLYSYS biomass production
B      compatible agricultural land
p      probability of contract participation
s      conditional acreage share among participants
b      landholder-level behavioural access response
kappa  county-by-land acreage-access rate under the transmission rule
K      contractual land-access capacity
```

The composition-preserving matching rule is:

```text
rho    = A_P / K
lambda = min(1, K / A_P)

A_M = lambda × A_P
Q_M = lambda × Q_P
```

The main national outcome is:

```text
M_Q = sum(Q_M) / sum(Q_P)
```

## Evidence used by the model

### POLYSYS

The retained upstream resource allocation uses:

- year: **2041**;
- biomass price case: **US$70 per dry ton**;
- land sources: **Crop** and **Pasture**;
- seven perennial resources: switchgrass, miscanthus, energy cane, poplar, willow, eucalyptus and pine.

Four source scenario labels are retained for provenance. Two of those labels are exact row-level duplicates in the selected perennial allocation, so robustness summaries use **three independent allocation families** rather than counting the duplicate twice.

POLYSYS `harvest` acreage and `prod` dry tons are treated as source quantities. BioLand-US does not rebuild acreage from reported yields.

### Study-A behavioural experiment

The behavioural component uses a randomized stated-preference experiment on perennial-biomass contracts. The final extensive-margin sample contains:

- **403 respondents**;
- **1,270 experimental choices**;
- **356 accepted choices**.

Randomized annual land-rental offers were **US$50, US$100, US$200 and US$300 per acre per year**, with **5-year** and **10-year** contract durations. These rental offers are analytically distinct from the POLYSYS biomass farmgate price.

The primary experimental model treats compensation categorically. A separate smooth log-dollar specification is used for national transport:

```text
logit(p) =
    -6.017543
    + 0.943158 ln(offer)
    - 0.081661 I(10-year)
    + 0.0214773 I(Pasture)
    + 0.746083 I(Switchgrass)
```

Experimental identification and national transport are treated as separate inferential steps.

### Conditional acreage

The central all-accept conditional acreage representation is:

```text
s = 0.863337
```

Lower, IPW and upper representations are retained as structural sensitivities. No additional national compensation response is imposed on the intensive margin.

### Feedstock transfer

Study A directly evaluates switchgrass and poplar. The national model therefore uses an explicit treatment-class transfer:

```text
Switchgrass, Miscanthus, Energy cane
    → Switchgrass experimental archetype

Poplar, Willow, Eucalyptus, Pine
    → Poplar experimental archetype
```

This is a modelling assumption for transport. It is not evidence that respondents directly evaluated the untested species.

### Compatible land

The central county land base is derived from the 2022 Census of Agriculture:

```text
Crop =
    total cropland
    - cropland pastured only

Pasture =
    cropland pastured only
    + pastureland excluding cropland and woodland
```

Disclosure-suppressed values are not treated as zero. The final completion layer carries `JOINT_EQUAL`, `JOINT_OWNED` and `JOINT_RENTED` surfaces, with `JOINT_EQUAL` as the central deterministic case.

### Rent context

Cash-rent context follows a fixed evidence hierarchy:

1. county, same land type, 2022;
2. nearest same-county observation within ±3 years;
3. official same-land state estimate for 2022;
4. unsupported.

Supported values are converted to **2012 U.S. dollars** before behavioural transport. Unsupported cells remain missing.

## Land-rental offer scenarios

Two scenario families are reported.

### Experiment-anchored

```text
US$50
US$100
US$200
US$300 per acre per year
```

### Rent-indexed

```text
offer = m × county cash rent
```

with:

```text
m = 1.0000
m = 3.3544
m = 6.7088
m = 13.4175
m = 20.1263
```

The `m = 6.7088` case is the **national support-balanced reference**. It balances experimental monetary support across the combined production allocation and is not interpreted as an equilibrium price, policy optimum or land-class-specific optimum.

## Institutional transmission

The identified quantitative analysis implements:

```text
T1_POOLED_BEHAVIOURAL_TRANSMISSION
```

Potential T2-T4 role-differentiated alternatives remain explicitly unquantified because defensible national role-control formulas and weights have not been frozen. The repository does not assign arbitrary values to them.

## Spatial interpretation

County maps describe **spatial implementation exposure under nationally transported experimental behaviour**. They are not maps of observed county willingness.

Spatial outputs include:

- implementation pressure;
- probability of contractual capacity binding;
- probability of top-decile implementation risk;
- unmet biomass;
- structural disagreement;
- cross-family hotspot stability.

## Repository structure

```text
BioLand-US/
├── config/
├── data/
│   ├── README.md
│   ├── source_registry.csv
│   └── frozen/
├── docs/
├── results/
│   ├── manuscript/
│   ├── figures/
│   └── validation/
├── scripts/
│   ├── 00_run_core.py
│   ├── 01_validate_behaviour.py
│   ├── 02_prepare_polysys.py
│   ├── 03_prepare_land.py
│   ├── 04_prepare_rents.py
│   ├── 05_build_behavioural_access.py
│   ├── 06_run_mobilization.py
│   ├── 07_run_bootstrap.py
│   ├── 08_run_structural_sensitivity.py
│   ├── 09_build_spatial_outputs.py
│   ├── 10_transport_robustness.py
│   ├── 11_figure1_identity_audit.py
│   ├── 12_support_bounded_extrapolation.py
│   ├── 13_build_figure_workbook.py
│   └── 14_make_figures.py
├── src/bioland_us/
├── stata/
│   ├── 00_run_behaviour.do
│   ├── 01_prepare_behaviour.do
│   ├── 02_estimate_participation.do
│   ├── 03_reconstruct_conditional_acreage.do
│   ├── 04_export_behaviour.do
│   ├── 05_validate_behaviour.do
│   └── 06_export_transport_sensitivity.do
├── tests/
├── CITATION.cff
├── LICENSE
├── pyproject.toml
└── README.md
```

## Data and access

The repository does not redistribute restricted Study-A respondent-level microdata.

Public-source provenance, clean local names and SHA-256 checksums are recorded in [`data/source_registry.csv`](data/source_registry.csv). Raw third-party downloads remain local and are gitignored.

See:

- [`data/README.md`](data/README.md)
- [`docs/data_inputs.md`](docs/data_inputs.md)
- [`docs/reproducibility.md`](docs/reproducibility.md)

## Reproducing the analysis

### Installation

```bash
git clone https://github.com/ElvisKwameOfori123/BioLand-US.git
cd BioLand-US

python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -e .
```

### Behavioural estimation

After placing authorized restricted behavioural inputs locally:

```stata
do stata/00_run_behaviour.do
```

### Public-source preparation

```bash
python scripts/02_prepare_polysys.py --input <retained_polysys_csv>
python scripts/03_prepare_land.py --input <completed_census_land_csv>
python scripts/04_prepare_rents.py --county <county_rents_csv> --state <state_rents_csv> --cpi <cpi_csv>
```

### Deterministic national core

```bash
python scripts/00_run_core.py
```

### Statistical uncertainty

```bash
python scripts/07_run_bootstrap.py
```

### Structural sensitivity

```bash
python scripts/08_run_structural_sensitivity.py
```

### Spatial robustness

```bash
python scripts/09_build_spatial_outputs.py
```

### Behavioural transport and evidence-support robustness

After the restricted rent-matched Study-A file is available locally:

```stata
do stata/06_export_transport_sensitivity.do
```

Then run:

```bash
python scripts/10_transport_robustness.py
python scripts/11_figure1_identity_audit.py
python scripts/12_support_bounded_extrapolation.py
```

### Reporting workbook and figures

```bash
python scripts/13_build_figure_workbook.py
python scripts/14_make_figures.py
```

The workbook builder owns the reporting layer. The plotting script is read-only.

## Scientific safeguards

The clean workflow enforces the following rules:

- no POLYSYS re-optimization;
- no double use of county-by-land capacity across feedstocks;
- no conversion of unsupported rent to zero;
- no arbitrary finite replacement for infinite implementation pressure;
- no mixing of statistical bootstrap uncertainty with structural sensitivity;
- no claim that treatment-class transfer equals direct experimental evidence;
- no quantitative T2-T4 institutional scenarios without defensible national parameters;
- no interpretation of county maps as locally estimated willingness;
- no redistribution of restricted respondent-level data.

## Manuscript and citation

The associated manuscript is **in preparation**. A manuscript citation and DOI will be added after public release.

Until then, cite the software repository using [`CITATION.cff`](CITATION.cff).

Repository documentation is intentionally written separately from the manuscript and may use different wording from the final paper.

## Author

**Elvis Kwame Ofori**  
University of Galway
