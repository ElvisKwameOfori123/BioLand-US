# BioLand-US data inputs

BioLand-US combines public agricultural-resource data with restricted experimental behavioural evidence. This document records the clean input architecture used by the reproducibility repository.

## Public-source inputs

Canonical public inputs are registered in `data/source_registry.csv`, including their clean local names, source filenames, analytical roles, repository treatment and SHA-256 checksums.

The identified analysis uses:

- the retained 2041 / US$70 per dry ton POLYSYS perennial-biomass allocation from the 2023 Billion-Ton resource package;
- the 2022 Census of Agriculture for compatible county Crop and Pasture land;
- USDA NASS county cash-rent history;
- official 2022 state cash rents for unsupported county-by-land cells;
- the U.S. CPI used to express supported rents in 2012 dollars;
- county geometry for spatial joins and manuscript maps.

Raw third-party downloads remain local under `data/raw/` and are excluded from Git. The source registry provides enough provenance to retrieve and verify the same files where public access remains available.

## Restricted behavioural input

Study-A respondent-level data are restricted and must never be committed. Authorized local users should place the source archive or approved extracts under the gitignored restricted-data area and run the documented Stata pipeline.

The public repository retains only non-disclosive exports, frozen model constants and manuscript-facing summaries that do not redistribute respondent-level records.

## Derived canonical inputs

The clean workflow builds explicit derived inputs rather than relying on opaque manual edits. These include:

- standardized POLYSYS county-by-land-by-feedstock allocation;
- compatible Census land pools with suppression-aware completion;
- county-by-land rent context following the frozen hierarchy;
- behavioural-access tables based on `b = p × s`;
- county-by-land contractual capacity and mobilization outputs;
- statistical and structural uncertainty summaries;
- transport and evidence-support robustness outputs.

Unsupported rent remains missing. Missing evidence is not recoded as zero capacity.

## Reporting layer

The final reporting workbook is generated after the analytical outputs have been frozen. Its target name is:

```text
results/figures/BioLandUS_FigureWorkbook_v7_FINAL.xlsx
```

The workbook is a reporting artefact rather than a raw analytical input. Its validated seed workbook and several upstream products depend on the authorized restricted-data workflow, so the binary workbook is not required to be redistributed as public raw data. The repository instead versions the workbook builder, the read-only plotting script, manuscript-facing result tables and the reconciliation ledger.

Authorized users with the frozen seed can regenerate the reporting workbook using:

```bash
python scripts/13_build_figure_workbook.py --seed <validated_seed_workbook.xlsx>
```

The plotting stage then reads that workbook without changing scientific calculations:

```bash
python scripts/14_make_figures.py --workbook results/figures/BioLandUS_FigureWorkbook_v7_FINAL.xlsx
```

## Reproducibility principle

Every retained input must be either:

1. publicly retrievable and checksum-verifiable;
2. an authorized restricted input documented by provenance but not redistributed; or
3. a deterministic derivative of one of those inputs produced by versioned code.

Development-only prototypes, literature reference files and superseded combined inputs are not treated as canonical model inputs.
