# BioLand-US

[![tests](https://github.com/ElvisKwameOfori123/BioLand-US/actions/workflows/ci.yml/badge.svg)](https://github.com/ElvisKwameOfori123/BioLand-US/actions/workflows/ci.yml)

Code, data products and reproducibility material for the study:

**Land on paper: testing US bioenergy allocations against landholder contractual capacity**

## Why this project exists

National energy and bioeconomy strategies can identify where land appears suitable for a new use and how much land a transition may require. But land does not move simply because it has been allocated in a model. Farmers and landowners still have to decide whether to participate, how much land to commit and on what terms.

BioLand-US asks a practical policy question:

> **Can the land required by a national bioenergy plan actually be secured, and can the payments needed to secure it be afforded?**

The project uses the 2023 Billion-Ton perennial-biomass allocation for 2041 at US$70 per dry ton as a national case study.

## What BioLand-US tests

BioLand-US separates implementation into two questions.

### 1. Will landholders participate?

A randomized stated-preference experiment with 403 Michigan landowners is used to estimate:

- whether a landholder accepts a contract at a given annual offer; and
- how much eligible land is committed after acceptance.

Those responses are transferred to county land and local cash-rent conditions to estimate **contractual capacity**, the land expected to be available under the stated contract.

### 2. Can the required payment be afforded?

The offer needed to recruit landholders is compared with the annual land payment that the biomass price can support after production costs.

This distinction matters because a place can have:

- too little landholder participation even when higher payments are affordable; or
- willing landholders whose required payment is too expensive for the biomass value to support.

Those are different policy problems and require different responses.

## Main findings

At the reference offer of 6.71 times local cash rent:

| Finding | Result |
|---|---:|
| Prospective biomass supported by willing landholders | 78.8% |
| 95% behavioural sampling interval | 69.4–86.7% |
| Biomass supported when behaviour is weighted by acreage controlled | 58.7% |
| Unmet requirement | about 90 million dry tons on 18.5 million acres |
| Share of unmet biomass in Texas, Oklahoma and New Mexico | 77.8% |
| Mobilized when unaffordable offers are refused | 15.3–34.6% |
| Mobilized when offers are capped at what the biomass price can fund | 39.9–67.1% |

The two constraints also have different geographies. Willingness binds mainly on low-rent pasture in the southern Great Plains, while affordability binds more strongly on cropland.

The broader implication is that landholder behaviour, contract terms and affordability should be tested **before** land-use targets, infrastructure investments and programme budgets are locked in.

## How to read this repository

If you are interested in the **policy question and headline results**, start here and then look at:

- [manuscript numbers](results/manuscript/manuscript_numbers.csv) for the values quoted in the paper;
- [figures](results/figures/) for the national and spatial results; and
- [decision log](docs/DECISIONS.md) for the main analytical choices and why they were made.

If you want to **reproduce the analysis**, see:

- [reproducibility guide](docs/reproducibility.md);
- [data access and provenance](docs/data_access.md); and
- [scripts guide](scripts/README.md).

## Analysis flow

The analysis follows the same policy sequence used in the paper:

1. Read the prospective POLYSYS biomass allocation.
2. Build compatible county cropland and pasture pools.
3. Attach local cash-rent conditions.
4. Estimate landholder participation and acreage commitment.
5. Translate those responses into county-level contractual capacity.
6. Compare contractual capacity with the land required by the allocation.
7. Test whether the proposed offers are affordable at the biomass price.
8. Report mobilized biomass, unmet requirements and spatial implementation pressure.

The upstream allocation is held fixed. BioLand-US therefore asks whether that stated plan can be delivered where it has been placed rather than reallocating production after a local shortfall appears.

## Repository structure

| Folder | Purpose |
|---|---|
| `src/bioland_us/` | Core analysis functions |
| `scripts/` | End-to-end analysis pipeline |
| `stata/` | Landholder behavioural estimation |
| `data/frozen/public/` | Non-disclosive inputs used by the model |
| `results/manuscript/` | Main manuscript tables and quoted-number ledger |
| `results/figures/` | Main and supplementary figures |
| `docs/DECISIONS.md` | Analysis choices and their rationale |
| `docs/data_access.md` | Data sources, access and provenance |
| `docs/reproducibility.md` | Instructions for reproducing the analysis |
| `tests/` | Automated tests |

## Reproducing the public analysis

```bash
git clone https://github.com/ElvisKwameOfori123/BioLand-US.git
cd BioLand-US

python -m venv .venv
.venv\Scripts\activate
# macOS / Linux: source .venv/bin/activate

pip install -e ".[dev]"

python -m pytest
python scripts/00_verify_release.py --recompute
python scripts/00_run_core.py
```

To rebuild inputs from the original public source files:

```bash
python scripts/00_run_core.py --from-raw
```

Re-estimating landholder behaviour and rerunning the bootstrap requires the respondent-level survey and Stata 18:

```bash
do stata/00_run_behaviour.do
python scripts/00_run_core.py --restricted
```

See [reproducibility](docs/reproducibility.md) for the full workflow.

## Data

Most inputs are public. The main sources are:

- U.S. Department of Energy 2023 Billion-Ton Report / POLYSYS allocation;
- USDA 2022 Census of Agriculture;
- USDA NASS county and state cash rents;
- U.S. Bureau of Labor Statistics CPI-U; and
- the 2012 Bioenergy and Land Use Survey.

The respondent-level Bioenergy and Land Use Survey is not redistributed here. It is available from the Kellogg Biological Station Long Term Ecological Research catalogue as KBS098:

[doi:10.6073/pasta/3f43b536ef860a2046db415b22ffcd6a](https://doi.org/10.6073/pasta/3f43b536ef860a2046db415b22ffcd6a)

The repository contains only non-disclosive behavioural parameters needed for the public pipeline. See [data access](docs/data_access.md) for details.

## Reproducibility and audit trail

Every manuscript-facing number is linked to the analysis outputs, and the pipeline includes automated checks for the released results. The repository also keeps an explicit decision log so that choices about land pools, rent assignment, behavioural transfer, affordability and sensitivity analysis can be inspected rather than hidden in code.

## Citation

Please cite the associated manuscript and this repository. Citation metadata are provided in [`CITATION.cff`](CITATION.cff).

## Licence

The analysis code is released under CC0 1.0. Source datasets retain the terms set by their original providers.

**Author:** Elvis Kwame Ofori  
Plant and AgriBiosciences Research Centre, Ryan Institute, University of Galway
