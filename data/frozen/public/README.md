# Bundled public frozen inputs

This directory contains small, non-disclosive inputs that can be safely versioned with BioLand-US.

Included here:

- `cpi_u_annual.csv`: CPI-U annual-average anchors used to convert supported land rents to 2012 dollars.
- `behaviour_parameters_public.csv`: frozen non-disclosive behavioural coefficients, conditional-acreage representations and uncertainty settings used by the manuscript-facing implementation.

Large third-party public datasets are not duplicated in GitHub. They are retrieved from their authoritative providers and verified against `data/source_registry.csv`. Use:

```bash
python scripts/00_fetch_public_sources.py
```

The KBS Study-A respondent-level survey is not redistributed. It must be obtained from KBS LTER/PASTA under the applicable data-use terms if behavioural re-estimation is required.

The public national model uses the frozen behavioural coefficients. Re-estimating those coefficients from respondent-level records is a separate restricted-data validation stage.
