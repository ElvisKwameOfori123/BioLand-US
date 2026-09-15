# Stata behavioural analysis

Stata 18.5 is authoritative for Study-A behavioural estimation.

Run the core behavioural workflow from the repository root:

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
| `06_export_transport_sensitivity.do` | Estimate and export rent-matched offer/rent and offer+rent transport sensitivities |

Restricted respondent-level data are not redistributed.

## Primary participation transport

Expected frozen smooth coefficients:

| term | value |
|---|---:|
| intercept | -6.017543 |
| ln(offer) | 0.943158 |
| 10-year contract | -0.081661 |
| Pasture | 0.0214773 |
| Switchgrass | 0.746083 |

The primary randomized treatment is an **annual land-rental offer per acre per year**.

## Rent-context robustness

`06_export_transport_sensitivity.do` operates on the locally held rent-matched
restricted Study-A file and exports two sensitivity models:

1. `ln(offer/rent)` ratio-only stress test;
2. unrestricted `ln(offer) + ln(rent)` sensitivity.

In the audited rent-matched sample (1,157 choices, 370 respondent clusters), the
restriction required by the pure ratio model, `beta_ln_offer + beta_ln_rent = 0`,
is rejected (`p = 0.0002`). The ratio-only model is therefore retained as a stress
test rather than treated as an equally weighted primary transport specification.
