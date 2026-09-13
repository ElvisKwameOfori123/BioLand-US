# Stata behavioural analysis

Stata 18.5 is used for the manuscript behavioural estimation.

The public Stata pipeline starts from two **restricted canonical analysis files** that are not redistributed on GitHub:

```
data/restricted/KBS_A_PerennialChoices_LONG_RESTRICTED.dta
data/restricted/KBS_A_PerennialChoices_INTENSIVE_CENTRAL_RESTRICTED.dta
```

Run from the repository root:

```stata
do stata/00_master.do
```

The pipeline:

1. prepares the 1,270-choice / 403-respondent candidate sample;
2. estimates the categorical randomized-offer logit;
3. estimates the smooth log-dollar transport model;
4. verifies the frozen conditional-acreage architecture;
5. exports the restricted respondent-level bootstrap input;
6. runs regression tests against the frozen manuscript analysis.

Expected frozen smooth coefficients:

| term | value |
|---|---:|
| intercept | -6.017543 |
| ln(offer) | 0.943158 |
| 10-year contract | -0.081661 |
| Pasture | 0.0214773 |
| Switchgrass | 0.746083 |

The validation file also verifies the smooth predictive margins at US$50, 100, 200 and 300 and the central all-accept conditional acreage share of 0.863337.

Restricted respondent-level exports remain gitignored.
