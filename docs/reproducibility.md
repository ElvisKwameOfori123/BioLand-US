# Reproducing BioLand-US

## 1. Check the release (no data needed beyond the clone)

```bash
pip install -e ".[dev]"
python -m pytest
python scripts/00_verify_release.py --recompute
```

`--recompute` reruns scripts 05 and 06 from the committed tables and requires an
exact match with `results/deterministic/national_mobilization.csv`.

## 2. Rebuild everything from raw sources

1. Put the raw files in `data/raw/` (see `data/README.md`); checksums are in
   `data/source_registry.csv`.
2. Behaviour (needs the KBS archive and Stata 18):
   `do stata/00_run_behaviour.do`
3. National model:
   `python scripts/00_run_core.py --from-raw --restricted`

Without the KBS archive, skip step 2 and drop `--restricted`: the public
parameters in `data/frozen/public/behaviour_parameters_public.csv` drive the
model, and only the bootstrap is unavailable.

## Built-in gates

- Each stage stops on broken keys, negative acreage, shares outside [0, 1] or
  unclosed state totals.
- Script 05 recomputes the rent multipliers from the data and stops if they
  differ from `config/default.toml`.
- Script 07 refuses to resample unless draw 0 reproduces the Stata coefficients,
  s and every national result of 06.
- Script 10 requires the primary transport to reproduce 06.
- Script 11 writes the reconciliation ledger and stops on any FAIL.

Scientific rules are listed in `docs/DECISIONS.md`.
