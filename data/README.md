# Data architecture

BioLand-US separates data by source, access status, and reproducibility role.

## Important rule

Do **not** commit raw or restricted source data directly to this repository unless redistribution rights have been verified.

The clean code expects the data to be placed locally under the documented folder structure.

## Source groups

| Source | Role in BioLand-US | Access / repository treatment |
|---|---|---|
| KBS Landowner Mail Survey on Bioenergy and Land Use | Randomized contract participation and conditional-acreage evidence | Restricted microdata. Not redistributed here. |
| POLYSYS / 2023 Billion-Ton Report perennial allocation | Prospective county-by-land-by-feedstock acreage and biomass allocation | Public source. Retrieval metadata will be documented; raw archive is not duplicated unnecessarily. |
| 2022 Census of Agriculture Quick Stats | Compatible county agricultural land and land-accounting structure | Public source. |
| USDA/NASS cash rents | County/state agricultural rent context | Public source. |
| US county geometry | Spatial joins and publication maps | Public source. |

## Local folder structure

```
data/
├── raw/          # downloaded public source files; gitignored
├── restricted/   # restricted behavioural microdata; gitignored
├── interim/      # regenerable intermediate files; gitignored
└── frozen/       # small publication/reproducibility outputs that may be versioned
```

## Restricted behavioural data

The repository will provide:

- expected filenames;
- required variables;
- validation checks;
- code that transforms the data after authorized users place the files locally.

It will **not** provide the restricted respondent-level data themselves.

## Reproducibility outputs

Small derived outputs may be committed where they are non-disclosive and redistribution is permitted. These are intended to allow readers to reproduce manuscript tables and figures even when they cannot access the restricted behavioural microdata.

## Provenance

Every cleaned stage should record:

- input filenames;
- input hashes where practical;
- row counts;
- key validation checks;
- output paths;
- model version / configuration;
- stage status.

The development pipeline used PASS / BLOCKED / REQUIRES_DECISION gates. The public pipeline retains the same fail-fast principle in a cleaner form.
