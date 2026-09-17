# BioLand-US reproducibility

BioLand-US separates scientific calculation from reporting so that presentation changes cannot silently alter frozen results.

## Reproducibility layers

The public repository contains:

1. clean Python and Stata analysis scripts;
2. reusable package functions under `src/bioland_us/`;
3. unit tests for behavioural response, feedstock transfer, mobilization and validation rules;
4. public-source provenance and SHA-256 checksums;
5. non-disclosive manuscript-facing outputs;
6. reconciliation checks for the frozen reporting results;
7. an automated GitHub Actions workflow that runs the core unit-test suite on pushes and pull requests to `main`.

Restricted respondent-level Study-A microdata are not redistributed. The final reporting workbook is also treated as a generated local artefact because its seed and several upstream products depend on the authorized restricted-data workflow. This does not change the frozen scientific values retained in the public manuscript-facing tables and validation ledger.

## Core execution order

```text
restricted behavioural estimation (Stata)
        ↓
public-source preparation
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

## Tests

Install development dependencies and run:

```bash
pip install -e ".[dev]"
python -m pytest
```

The same test suite is configured in `.github/workflows/ci.yml`.

## Frozen reporting checks

`results/validation/reconciliation_checks.csv` records the manuscript-facing checks, including:

- family-balanced experiment reconciliation;
- support shares summing to 100%;
- county-to-national mobilization reconciliation;
- mobilized plus unmet biomass equalling upstream biomass;
- five-character county FIPS handling;
- explicit undefined-capacity display class;
- exactly 12 implemented structural variants;
- negligible intensive lower/upper gap;
- exactly 1,000 bootstrap draws.

The reporting builder adds further checks for the Figure 1 identity, family-mean spatial accounting, the primary transport reconciliation and evidence-bounded interval.

## Data boundaries

Raw public third-party data remain local and are documented in `data/source_registry.csv`. Restricted Study-A respondent records must never be committed. Unsupported rent cells remain missing rather than being recoded to zero.

## Reporting workbook

Authorized users with the validated seed workbook and frozen upstream outputs can regenerate the reporting layer with:

```bash
python scripts/13_build_figure_workbook.py --seed <validated_seed_workbook.xlsx>
python scripts/14_make_figures.py --workbook results/figures/BioLandUS_FigureWorkbook_v7_FINAL.xlsx
```

The workbook builder performs reporting arithmetic and checks. The plotting script is read-only and must not be used to alter scientific calculations.

## Release principle

The public repository is the clean manuscript-facing implementation, not a dump of every development artifact. Development-only, failed, duplicate, restricted or forensic files are intentionally excluded. The release criterion is that every retained scientific stage is documented, versioned, and traceable to the frozen result rather than that every historical file be published.
