# Data architecture

BioLand-US separates data by source, access status and reproducibility role.

## Rule

Do **not** commit restricted respondent-level microdata or raw third-party files
unless redistribution rights explicitly permit it.

```text
data/
├── raw/          # locally downloaded public source files, gitignored
├── restricted/   # restricted behavioural microdata, gitignored
├── interim/      # regenerable intermediate tables, gitignored
└── frozen/       # non-disclosive canonical inputs/outputs when permitted
```

## Source groups

| Source | Role | Repository treatment |
|---|---|---|
| KBS Study-A landholder survey | Randomized participation and conditional-acreage evidence | Restricted microdata, never redistributed |
| POLYSYS / Billion-Ton allocation | Prospective county-by-land-by-feedstock acreage and biomass | Public source; canonical retained allocation documented |
| 2022 Census of Agriculture | Compatible agricultural land | Public source; frozen completion surface used by clean code |
| USDA/NASS cash rents | County/state rent context | Public source |
| U.S. county geometry | Spatial joins and maps | Public source |

## Reproducibility outputs

Small derived outputs may be versioned when they are non-disclosive and
redistribution is permitted. This allows manuscript tables and figures to be
reproduced without publishing restricted respondent-level records.

## Provenance

The clean workflow retains the development project's fail-fast principle:
required inputs are checked, unsupported evidence remains explicit, and
scientific assumptions are named in the output rather than hidden in file
versions such as `FINAL`, `v2` or `CORRECTED`.

See [../docs/data_inputs.md](../docs/data_inputs.md) for the canonical input
contracts.
