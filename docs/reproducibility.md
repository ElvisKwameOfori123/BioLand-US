# BioLand-US reproducibility

BioLand-US separates source acquisition, scientific calculation, restricted behavioural re-estimation and reporting so that presentation changes cannot silently alter frozen results.

## Reviewer verification

A reviewer who wants to verify the public release without obtaining respondent-level data can run:

```bash
pip install -e ".[dev]"
python -m pytest
python scripts/00_verify_release.py
```

The verification script checks the public manuscript tables, five-figure index, reconciliation ledger, frozen CPI and behavioural-parameter hashes, uncertainty settings and absence of restricted respondent files from the working tree.

## Public source acquisition

Stable public source archives can be retrieved and checksum-verified with:

```bash
python scripts/00_fetch_public_sources.py
```

The exact provider links, query-export filenames, access conditions and SHA-256 values are documented in [`data_access.md`](data_access.md) and [`../data/source_registry.csv`](../data/source_registry.csv).

## Reproducibility layers

The public repository contains:

1. clean Python and Stata analysis scripts;
2. reusable package functions under `src/bioland_us/`;
3. unit tests for behavioural response, feedstock transfer, mobilization and validation rules;
4. public-source access metadata and SHA-256 checksums;
5. small bundled public frozen inputs, including CPI anchors and behavioural parameters;
6. non-disclosive manuscript-facing outputs;
7. reconciliation checks for the frozen reporting results;
8. an automated GitHub Actions workflow that runs the core unit-test suite on pushes and pull requests to `main`.

Restricted respondent-level Study-A microdata are not redistributed.

## Two distinct reproduction goals

### Public national-model reproduction

The deterministic national model uses the frozen non-disclosive behavioural parameters in `config/default.toml` and `data/frozen/public/behaviour_parameters_public.csv`. It does not require respondent-level KBS records merely to evaluate national contractual access and mobilization.

After the documented public spatial inputs have been prepared, run:

```bash
python scripts/00_run_core.py
```

### Behavioural re-estimation

Independent re-estimation of the Study-A behavioural models requires the respondent-level KBS source under the applicable data-use terms. After placing authorized inputs locally, run:

```stata
do stata/00_run_behaviour.do
```

Restricted behavioural validation can then be added to the national runner explicitly:

```bash
python scripts/00_run_core.py --validate-restricted-behaviour
```

This distinction prevents a third-party data-use restriction from being confused with the reproducibility of the public national implementation.

## Analytical execution order

```text
public source acquisition and canonical preparation
        ↓
restricted behavioural estimation, when independently re-estimating coefficients
        ↓
frozen behavioural parameters
        ↓
deterministic national core
        ↓
bootstrap + structural sensitivity
        ↓
spatial robustness
        ↓
transport and evidence-support robustness
        ↓
reporting workbook builder
        ↓
read-only plotting script
```

## Frozen reporting checks

`results/validation/reconciliation_checks.csv` records manuscript-facing checks including:

- family-balanced experiment reconciliation;
- support shares summing to 100%;
- county-to-national mobilization reconciliation;
- mobilized plus unmet biomass equalling upstream biomass;
- five-character county FIPS handling;
- explicit undefined-capacity display class;
- exactly 12 implemented structural variants;
- negligible intensive lower/upper gap;
- exactly 1,000 bootstrap draws.

The reporting builder adds checks for the Figure 1 behavioural identity, family-mean spatial accounting, primary transport reconciliation and evidence-bounded interval.

## Data boundaries

Large public third-party files remain under the original provider's authority and are kept locally under `data/raw/`. Small frozen public inputs are versioned under `data/frozen/public/`. Restricted Study-A respondent records must never be committed. Unsupported rent cells remain missing rather than being recoded to zero.

## Reporting workbook

Authorized users with the validated seed workbook and frozen upstream outputs can regenerate the reporting layer with:

```bash
python scripts/13_build_figure_workbook.py --seed <validated_seed_workbook.xlsx>
python scripts/14_make_figures.py --workbook results/figures/BioLandUS_FigureWorkbook_v7_FINAL.xlsx
```

The workbook builder performs reporting arithmetic and checks. The plotting script is read-only and must not alter scientific calculations.

## Release principle

The public repository is the clean manuscript-facing implementation, not a dump of every historical development artefact. Failed, duplicate, obsolete, restricted and forensic-only files are excluded when they are not part of the frozen scientific chain. Every retained manuscript result is instead traceable to a documented source, model stage and validation check.
