# Stata behavioural analysis

Stata 18.5 is authoritative for the Study-A behavioural estimation.

Run from the repository root:

```stata
do stata/00_run_behaviour.do
```

| Script | Purpose |
|---|---|
| `00_run_behaviour.do` | Master behavioural runner |
| `01_prepare_behaviour.do` | Prepare the restricted Study-A analysis sample |
| `02_estimate_participation.do` | Estimate randomized-offer and smooth participation models |
| `03_reconstruct_conditional_acreage.do` | Reproduce the frozen intensive-margin architecture |
| `04_export_behaviour.do` | Export canonical restricted/public behavioural inputs |
| `05_validate_behaviour.do` | Regression-test the frozen manuscript results |

Restricted respondent-level data are not redistributed.

Expected frozen smooth transport coefficients:

| term | value |
|---|---:|
| intercept | -6.017543 |
| ln(offer) | 0.943158 |
| 10-year contract | -0.081661 |
| Pasture | 0.0214773 |
| Switchgrass | 0.746083 |

The validation stage also checks the 1,270-choice / 403-respondent extensive sample,
the smooth predictive margins at US$50, 100, 200 and 300, and the frozen
conditional-acreage architecture.
