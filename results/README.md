# Manuscript-facing results

This directory contains clean, non-disclosive outputs retained for manuscript reporting and validation. It is not a dump of every development-stage intermediate file.

## Structure

- `manuscript/` contains compact tables used to support quoted manuscript results.
- `validation/` contains reconciliation and provenance checks for the frozen analysis.
- `figures/` documents the final reporting-workbook and plotting architecture.

## Release boundary

Restricted Study-A respondent-level data are never stored here. Large raw public-source files also remain local and are documented through the source registry rather than duplicated in GitHub.

The final figure workbook is a generated reporting artefact and depends on a validated local seed plus frozen upstream outputs. The repository therefore exposes the builder and plotting code, manuscript-facing CSV results and reconciliation ledger while keeping restricted or development-only source material outside version control.

## Frozen validation

`validation/reconciliation_checks.csv` is the compact public audit of the manuscript-facing reporting chain. The retained checks cover national accounting, support shares, spatial identifiers, structural-variant count, bootstrap completeness and treatment of undefined capacity.

Additional reporting-layer checks are implemented in `scripts/13_build_figure_workbook.py` for the Figure 1 behavioural identity, family-mean spatial accounting, transport reconciliation and evidence-bounded sensitivity.

## Interpretation

These files should be read together with the Methods and the documentation under `docs/`. They are designed to make the final reported quantities traceable without exposing restricted respondent records or implying that every historical development file is part of the public analytical package.
