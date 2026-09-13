# Data inputs

The exact source-file ledger and SHA-256 checksums are recorded in [`data/source_registry.csv`](../data/source_registry.csv).

BioLand-US separates raw source acquisition from manuscript-facing analysis.
The clean scripts operate on documented canonical inputs rather than on every
vendor-specific raw layout used during development.

## Restricted behavioural inputs

Restricted Study-A microdata are not distributed in this repository.

Expected local files include:

```text
data/restricted/KBS_A_PerennialChoices_LONG_RESTRICTED.dta
data/restricted/KBS_A_PerennialChoices_INTENSIVE_CENTRAL_RESTRICTED.dta
```

The Stata pipeline validates the final 1,270-choice / 403-respondent extensive
sample and the frozen intensive-margin architecture before exporting canonical
behavioural inputs for Python.

## POLYSYS allocation

The Python preparation script accepts the frozen retained perennial allocation
and standardizes it to:

- `scenario_name` when available;
- `allocation_family`;
- `fips`;
- `land_type`;
- `feedstock`;
- `A_P`, harvested acres;
- `Q_P`, dry tons.

The clean analysis uses three independent allocation families. The
`emerging` and `mature-market high` source labels are verified as exact
allocation duplicates before one representative is retained.

## Census compatible land

Preferred input is the frozen joint Census land-base table containing:

- `B_crop_equal_acres`, `B_pasture_equal_acres`;
- `B_crop_owned_acres`, `B_pasture_owned_acres`;
- `B_crop_rented_acres`, `B_pasture_rented_acres`.

`JOINT_EQUAL` is the central deterministic surface. `JOINT_OWNED` and
`JOINT_RENTED` are structural sensitivities.

The difficult disclosure-suppression completion is upstream of the public
manuscript-facing calculation. The clean code does not replay failed or
superseded completion algorithms.

## Cash-rent context

The rent hierarchy is:

1. exact county, same land type, 2022;
2. same county and land type, nearest year within ±3 years;
3. official USDA/NASS state 2022 value for the same land type;
4. unsupported.

Supported rents are converted to 2012 US dollars. Unsupported cells remain
missing and are never interpreted as zero rent or zero participation.

Canonical county/state rent inputs use:

- `fips` where applicable;
- `state_ansi`;
- `land_type`;
- `year`;
- `rent_usd_per_acre`.

The CPI table uses `year` and `cpi`.

## County geometry

County geometry is used only for spatial joins and manuscript maps. The figure
script searches `data/raw/` for the 2022 county geometry and does not embed a
user-specific absolute path.

## Reporting workbook

The plotting script expects the frozen manuscript reporting workbook at:

```text
results/figures/BioLandUS_FigureData.xlsx
```

The workbook must contain its reconciliation checks, style guide and the
figure-ready tables required by `scripts/10_make_figures.py`.
