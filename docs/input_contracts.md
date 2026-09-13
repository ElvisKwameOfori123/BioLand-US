# Canonical input contracts

The public analysis code uses canonical intermediate tables so that scientific logic is not tied to one vendor-specific raw-file layout.

## Restricted behavioural inputs

### KBS_A_PerennialChoices_LONG_RESTRICTED.dta

Required fields used by the public Stata code:

- `id`
- `sample_c`
- `acc`
- `offer`
- `contract`
- `land_f`
- `feedstock_f`

### KBS_A_PerennialChoices_INTENSIVE_CENTRAL_RESTRICTED.dta

Required fields:

- `id`
- `feedstock_f`
- `land_f`
- `intensive_status`
- `share_exact_observed`
- `share_lower_frozen`
- `share_upper_frozen`
- `share_central_primary`
- `share_central_ipw`

These respondent-level files are restricted and are not included in the repository.

## POLYSYS canonical allocation

The standardized Python table contains:

- `allocation_family`
- `fips`
- `land_type`
- `feedstock`
- `A_P` harvested acres
- `Q_P` dry tons

The explicit experimental treatment transfer then adds:

- `experimental_feedstock`
- `treatment_class`
- `transfer_status`

## Completed Census land components

The transparent compatible-land calculation requires one row per county with:

- `fips`
- `cropland_total`
- `cropland_pastured_only`
- `pasture_excluding_cropland_and_woodland`

The difficult disclosure-suppression completion must be performed and validated before this table is used.

## Rent tables

County and state rent tables use:

- `fips` where applicable
- `state_ansi`
- `land_type`
- `year`
- `rent_usd_per_acre`

The CPI table uses:

- `year`
- `cpi`

Unsupported county-land cells remain missing after the hierarchy is exhausted.

## Reporting workbook

The plotting script expects:

```
results/figures/BioLandUS_FigureWorkbook_v3_FINAL.xlsx
```

and uses the workbook's own reconciliation checks, style guide, colours, labels, and map-ready tables.
