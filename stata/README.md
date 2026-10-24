# Stata behavioural pipeline (Stata 18.5)

Starts from the raw KBS archive `data/raw/knb-lter-kbs.124.2.zip`. Run from the
repository root:

```stata
do stata/00_run_behaviour.do
```

| File | Does |
|---|---|
| `01_import_kbs.do` | Unzip and import the survey, safe numeric parsing, eligibility, long choice file (B01–B05) |
| `02_estimate_participation.do` | Categorical and smooth participation logits, acreage-weighted model, leave-one-county-out (B06, B07) |
| `03_conditional_acreage.do` | Intensive classes, bounds, central and IPW shares, acreage-weighted shares (B07–B10) |
| `04_export_behaviour.do` | Restricted choice-level export for the bootstrap; public parameter table |
| `05_transport_sensitivity.do` | Ratio-only and offer+rent models on rent-matched choices (B11) |

Respondent-level outputs go to `data/restricted/`, `data/frozen/restricted/` and
`results/restricted/` (all git-ignored). Aggregate results go to `results/behaviour/`.

Current values: 1,270 choices, 403 respondents, 356 accepts, 203 exact;
ln(offer) = 0.943; s = 0.8633 (IPW 0.8595, acreage-weighted 0.8858).
