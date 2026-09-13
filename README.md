# BioLand-US

**Landowner participation determines how much modelled biomass the United States can mobilize**

BioLand-US is a reproducible implementation-layer modelling framework for asking a simple question:

> Given a prospective perennial-biomass allocation, how much can actually be matched to voluntary contractual land access?

The framework links a randomized landholder contracting experiment to county agricultural land accounts, USDA cash-rent context, spatially explicit POLYSYS perennial-biomass allocations, contractual-capacity calculations, statistical uncertainty, structural sensitivity, and county-level spatial robustness.

The key analytical distinction is:

```
modelled biomass allocation
        !=
contractually accessible land
        !=
mobilized biomass
```

## Repository purpose

This repository is the code companion to the BioLand-US manuscript.

The validated scientific analysis was developed through a longer audit pipeline. The public repository intentionally does **not** reproduce that development history one script at a time. Instead, it is being reduced to a smaller, documented, reusable workflow that preserves the frozen scientific logic while removing:

- exploratory one-off scripts;
- duplicated audit code;
- local absolute paths;
- temporary diagnostics;
- obsolete stage variants;
- intermediate files that can be regenerated;
- private or restricted microdata.

The goal is that another researcher can understand the model architecture, obtain the permitted inputs, run the clean pipeline, and reproduce the reported tables and figures.

## Clean workflow

```
01  Prepare behavioural inputs
02  Prepare POLYSYS allocation
03  Build compatible county land
04  Build national rent context
05  Construct behavioural access
06  Compute contractual capacity and mobilization
07  Propagate paired-bootstrap uncertainty
08  Evaluate structural sensitivity
09  Build county spatial-robustness outputs
10  Generate publication tables and figures
```

The clean scripts will call reusable functions from `src/bioland_us/` rather than duplicating scientific logic across stage files.

## Scientific guardrails

The repository preserves the following modelling rules.

- POLYSYS allocations are fixed upstream pathways; BioLand-US does not re-optimize POLYSYS.
- Several feedstocks may draw on one county-by-land pool, so contractual capacity is defined once per land pool.
- Behavioural access `b = p * s` is distinct from nationally accessible acreage.
- The current main analysis implements the pooled T1 transmission assumption and does not invent unsupported T2-T4 weights.
- Unsupported rent evidence remains unsupported; it is never silently set to zero.
- Statistical uncertainty and structural sensitivity remain separate.
- Zero-capacity binding cells are explicitly identified rather than assigned arbitrary large pressure values.
- County maps represent spatial implementation exposure under transported experimental behaviour, not county-specific willingness.
- Plotting scripts read frozen reporting outputs and do not re-estimate the model.

## Data

Data are separated by access status.

- **Restricted behavioural microdata:** not redistributed in this repository.
- **Public source data:** documented with source and retrieval instructions.
- **Derived reproducibility outputs:** included only where redistribution is permitted and where they are needed to reproduce published results.

See [data/README.md](data/README.md).

## Installation

The clean repository targets Python 3.12.

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

## Reproducing the analysis

Once the documented source files are available in the expected folders:

```bash
python scripts/run_pipeline.py
```

Publication figures can then be regenerated separately:

```bash
python scripts/10_make_figures.py
```

The pipeline will fail loudly if required source files or frozen validation conditions are missing.

## Repository layout

```
BioLand-US/
├── config/
│   └── default.toml
├── data/
│   └── README.md
├── docs/
│   └── reproducibility.md
├── scripts/
│   └── README.md
├── src/
│   └── bioland_us/
│       ├── __init__.py
│       ├── paths.py
│       └── validation.py
├── tests/
├── .gitignore
├── pyproject.toml
├── CITATION.cff
└── README.md
```

## Reproducibility status

The repository scaffold is now established. The next step is to import the **validated local analysis scripts** and refactor them into the clean stages above without changing frozen scientific results.

## Author

**Elvis Kwame Ofori**  
University of Galway

## Licence

The repository currently uses the licence already attached to the project. Source datasets remain subject to their original licences, access restrictions, and disclosure conditions.
