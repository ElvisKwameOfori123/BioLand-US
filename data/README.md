# BioLand-US data

BioLand-US separates bundled public inputs, large third-party public sources, restricted behavioural records and generated analytical products. The goal is to make the public repository easy to audit without redistributing data that should remain with the original provider.

## What is bundled

Small, non-disclosive frozen inputs are versioned under `data/frozen/public/`:

- `cpi_u_annual.csv`
- `behaviour_parameters_public.csv`

Manuscript-facing result tables are versioned under `results/manuscript/`, with reconciliation checks under `results/validation/`.

## What is downloaded from the original provider

Large public source files are kept under `data/raw/`, which is gitignored. Exact filenames, source pages, access status and SHA-256 checksums are recorded in `source_registry.csv`.

For the sources with stable direct file URLs, run:

```bash
python scripts/00_fetch_public_sources.py
```

The helper retrieves the exact POLYSYS archive and 2022 Census Quick Stats bulk file used by BioLand-US and verifies their checksums. It also verifies the NASS rent exports and county geometry when those files are placed under `data/raw/`.

## Restricted Study-A behavioural data

The KBS Bioenergy and Land Use Survey respondent records are not redistributed. Researchers who need to re-estimate the behavioural models should obtain the source from KBS LTER/PASTA under the applicable data-use terms.

The public national implementation instead carries the frozen non-disclosive behavioural parameters in `data/frozen/public/behaviour_parameters_public.csv` and `config/default.toml`.

## Directory policy

- `data/raw/`: downloaded third-party public files, gitignored.
- `data/restricted/`: authorized respondent-level files, gitignored.
- `data/interim/`: generated local intermediates, gitignored.
- `data/frozen/public/`: small public frozen inputs safe to version.
- `data/frozen/restricted/`: respondent-derived restricted products that should remain local.
- `data/source_registry.csv`: authoritative source/access/checksum ledger.

Disclosure-suppressed Census values are never interpreted as zero. Unsupported cash-rent cells also remain missing rather than being converted to zero capacity. These are scientific rules, not file-management conveniences.

For the complete access matrix and reviewer instructions, see [`docs/data_access.md`](../docs/data_access.md) and [`docs/reproducibility.md`](../docs/reproducibility.md).
