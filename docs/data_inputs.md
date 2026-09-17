# BioLand-US data inputs

BioLand-US combines public agricultural-resource data with third-party experimental behavioural evidence. The public repository separates raw-source acquisition, canonical transformations, restricted behavioural re-estimation and manuscript-result verification.

For exact provider links, filenames, checksums and access conditions, see [`data_access.md`](data_access.md) and [`../data/source_registry.csv`](../data/source_registry.csv).

## Public source inputs

The identified analysis uses:

- the retained 2041 / US$70 per dry ton POLYSYS perennial-biomass allocation from the 2023 Billion-Ton resource package;
- the 2022 Census of Agriculture for compatible county Crop and Pasture land;
- USDA NASS county cash-rent history;
- official 2022 state cash rents for unsupported county-by-land cells;
- CPI-U annual averages used to express supported rents in 2012 dollars;
- USDA county geometry for spatial joins and manuscript maps.

The exact POLYSYS and Census source archives can be downloaded and checksum-verified with:

```bash
python scripts/00_fetch_public_sources.py
```

The NASS rent exports and geometry are public provider products whose exact frozen filenames and SHA-256 values are recorded in the source registry. The helper verifies them when placed under `data/raw/`.

## Bundled public frozen inputs

The repository directly versions small non-disclosive inputs:

```text
data/frozen/public/cpi_u_annual.csv
data/frozen/public/behaviour_parameters_public.csv
```

The behavioural parameter file contains the frozen coefficients and conditional-acreage representations used by the public national implementation. This allows national behavioural transport to remain separate from respondent-level re-estimation.

## Restricted behavioural input

Study-A respondent-level data are archived by KBS LTER/PASTA and are not redistributed here. Researchers who need to independently re-estimate the behavioural models should obtain the source under the applicable KBS data-use terms and run the documented Stata pipeline locally.

The public repository retains only non-disclosive parameters, model code, manuscript-facing summaries and validation outputs.

## Canonical transformations

The clean analytical architecture constructs:

- standardized POLYSYS county-by-land-by-feedstock allocation;
- compatible Census land pools with suppression-aware completion;
- county-by-land rent context following the frozen hierarchy;
- behavioural-access tables based on `b = p × s`;
- county-by-land contractual capacity and mobilization outputs;
- statistical and structural uncertainty summaries;
- transport and evidence-support robustness outputs.

Unsupported rent remains missing. Missing evidence is not recoded as zero capacity.

## Reporting layer

The final reporting workbook is generated only after analytical outputs are frozen. Its target name is:

```text
results/figures/BioLandUS_FigureWorkbook_v7_FINAL.xlsx
```

The workbook is a reporting artefact rather than a raw analytical input. The repository versions the workbook builder, read-only plotting code, manuscript-facing result tables, figure index and reconciliation ledger.

Authorized users with the validated reporting seed can regenerate it using:

```bash
python scripts/13_build_figure_workbook.py --seed <validated_seed_workbook.xlsx>
python scripts/14_make_figures.py --workbook results/figures/BioLandUS_FigureWorkbook_v7_FINAL.xlsx
```

## Reproducibility principle

Every retained input belongs to one of four transparent classes:

1. a publicly retrievable source with provider provenance and checksum;
2. a small public frozen input versioned directly in the repository;
3. a third-party restricted input documented by provenance but not redistributed; or
4. a deterministic derivative produced by versioned analysis code.

Development-only prototypes, literature reference files and superseded combined inputs are not canonical model inputs.
