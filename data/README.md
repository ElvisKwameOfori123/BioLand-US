# BioLand-US data directory

BioLand-US separates public-source provenance, restricted behavioural evidence and generated analytical products so that the public repository remains reproducible without redistributing data that should not be published.

## Directory policy

- `data/raw/` is for local third-party downloads and is gitignored.
- `data/restricted/` is for authorized Study-A respondent-level files and is gitignored.
- `data/interim/` is for generated local intermediates and is gitignored.
- `data/frozen/` contains documentation for frozen analytical products; restricted frozen files remain local.
- `data/source_registry.csv` records canonical filenames, roles, repository treatment and SHA-256 checksums.

## Public data

Public inputs should be downloaded from their original providers, stored locally and checked against the SHA-256 values in `source_registry.csv` before use. The repository does not duplicate large third-party archives simply because they are public.

## Restricted data

The Study-A Bioenergy and Land Use Survey is used under its repository terms and required permissions. Respondent-level records must never be committed to GitHub. Only non-disclosive analytical exports and frozen coefficients needed for the public manuscript-facing implementation are retained.

## Missing data and suppression

Disclosure-suppressed Census values are not interpreted as zeros. Unsupported cash-rent cells also remain missing rather than being converted to zero capacity. These rules are part of the scientific model and are enforced in the clean workflow.

## Reporting artefacts

The final figure workbook is generated locally from a validated seed plus audited upstream outputs. Because parts of that upstream chain derive from restricted behavioural data, the workbook is treated as a reporting artefact rather than a public raw input. Public result tables and reconciliation checks are stored under `results/`.

See `docs/data_inputs.md` and `docs/reproducibility.md` for the full execution and provenance architecture.
