# BioLand-US

[![tests](https://github.com/ElvisKwameOfori123/BioLand-US/actions/workflows/ci.yml/badge.svg)](https://github.com/ElvisKwameOfori123/BioLand-US/actions/workflows/ci.yml)

Code and results for the paper **"Who will supply the land? Contractual capacity and the feasibility of US
perennial biomass allocations"** (submitted to *Land Use Policy*).

## What it does

National plans allocate land to perennial biomass, but the land is only delivered if the farmers and landowners
who control it sign contracts. BioLand-US takes the 2023 Billion-Ton (POLYSYS) allocation for 2041 at US$70 per dry
ton and tests it at two gates:

1. **Willingness**: would landholders accept the contract and commit land? Estimated from a randomized
   stated-preference experiment (403 Michigan landowners, 1,270 choices) and applied to every county and land class.
2. **Affordability**: can the biomass price pay the offer? The offer is compared with the largest land payment the
   price can fund after production costs (Dumortier et al., 2017 budget).

## Main results

At an offer of 6.71 times local cash rent (the reference):

| Result | Value |
|---|---|
| Prospective biomass supported by willing landholders | 78.8% (95% interval 69.4–86.7%) |
| ... with behaviour weighted by acreage | 58.7% |
| Unmet requirement | about 90 million dry tons on 18.5 million acres |
| Share of the unmet biomass in Texas, Oklahoma and New Mexico | 77.8% |
| Mobilized when unaffordable offers are refused | 15.3–34.6% |
| Mobilized when offers are capped at what the price can fund | 39.9–67.1% |

Affordability ranges run from the high-cost to the low-cost budget. Every number quoted in the paper is in
[`results/manuscript/manuscript_numbers.csv`](results/manuscript/manuscript_numbers.csv).

## Run it

```bash
git clone https://github.com/ElvisKwameOfori123/BioLand-US.git
cd BioLand-US
python -m venv .venv
.venv\Scripts\activate            # macOS / Linux: source .venv/bin/activate
pip install -e ".[dev]"

python -m pytest                                # unit tests
python scripts/00_verify_release.py --recompute # check the committed results
python scripts/00_run_core.py                   # rerun the model, tables and figures
```

`python scripts/00_run_core.py --from-raw` also rebuilds the inputs from the raw public files placed in `data/raw/`
(sources and checksums in [`data/source_registry.csv`](data/source_registry.csv)). Re-estimating the behaviour and
running the bootstrap needs the survey data and Stata 18: run `do stata/00_run_behaviour.do`, then add `--restricted`.
Details: [reproducibility](docs/reproducibility.md).

## What is where

| Folder | Contents |
|---|---|
| `src/bioland_us/` | model code: behaviour, land, rents, capacity matching, affordability |
| `scripts/` | the pipeline, numbered in run order ([guide](scripts/README.md)) |
| `stata/` | behavioural estimation from the raw survey |
| `data/frozen/public/` | small derived inputs the model reads |
| `results/manuscript/` | Tables 2–3, Table S4 and the ledger of quoted numbers |
| `results/figures/` | Figs. 1–4 and S1–S6, numbered as in the paper |
| `docs/DECISIONS.md` | every analysis choice and its reason (Table S5 of the paper) |

## Data

All inputs are public except the survey. The 2012 Bioenergy and Land Use Survey (KBS LTER, KBS098,
[doi:10.6073/pasta/3f43b536ef860a2046db415b22ffcd6a](https://doi.org/10.6073/pasta/3f43b536ef860a2046db415b22ffcd6a))
is available from its provider and is not redistributed here; the model uses only the non-disclosive parameters in
`data/frozen/public/behaviour_parameters_public.csv`. See [data access](docs/data_access.md).

## Citation and licence

Cite the paper and this repository ([`CITATION.cff`](CITATION.cff)). The code is released under CC0 1.0
([`LICENSE`](LICENSE)); source datasets keep their providers' terms.

Elvis Kwame Ofori, Plant and AgriBiosciences Research Centre, Ryan Institute, University of Galway.
