# Results

This directory contains the small, non-disclosive manuscript-facing outputs that
are useful to readers. Large bootstrap draw files, regenerable county intermediates
and restricted behavioural files remain local.

## Headline case

The principal spatial case is the **national support-balanced rent-indexed reference**
(`m = 6.7088`), 5-year contract, family-balanced across the three independent
POLYSYS allocation families.

For the manuscript headline case:

- paired-bootstrap median biomass mobilization: **78.46%**;
- paired respondent-bootstrap 95% interval: **70.34% to 86.08%**;
- implemented intensive-margin × land-completion structural range: **63.47% to 83.81%**;
- three independent POLYSYS-family medians: **76.17% to 81.54%**;
- 10-year contract median: **76.62%**.

These classes are kept separate.

The deterministic central calculation used for transport robustness is **78.67%**.
It reconciles to frozen Stage 07G to machine precision.

## Annual land-rental offer experiment

The randomized Study-A monetary treatment is interpreted as an annual land-rental
offer per acre per year, not a biomass farmgate price.

For the 5-year family-balanced experiment-anchored cases:

| Annual land-rental offer (2012 US$/acre/year) | Median M_Q |
|---:|---:|
| 50 | 57.06% |
| 100 | 80.95% |
| 200 | 95.98% |
| 300 | 98.61% |

The corrected Figure 1 behavioural-access central series, satisfying `b = p × s`
with frozen `s = 0.863337`, is approximately 10.87%, 18.54%, 29.42% and 36.95%.

## Rent-indexed land-access offers

For the 5-year family-balanced primary cases:

| Rent multiplier | Median M_Q |
|---:|---:|
| 1.0000 | 31.42% |
| 3.3544 | 60.63% |
| 6.7088 | 78.46% |
| 13.4175 | 91.97% |
| 20.1263 | 96.08% |

The `m = 6.7088` case is a **national support-balanced reference**, not a policy,
market or land-class optimum.

At that reference, deterministic 5-year mobilization differs materially by land
class: approximately **93.2% for Crop** and **71.2% for Pasture**.

## Behavioural-transport robustness

For the national support-balanced 5-year case:

| Transport specification | Deterministic M_Q | Role |
|---|---:|---|
| Primary log-dollar | 78.67% | Primary randomized absolute-dollar transport |
| Offer + local rent | 75.91% | Rent-context sensitivity |
| Offer/rent ratio | 98.27% | Stress test only |

The pure offer/rent restriction is rejected in the rent-matched experimental sample
(`p = 0.0002`). The primary and unrestricted offer+rent specifications produce
very similar hotspot geography.

Using monotonicity only outside the randomized US$50 to US$300 range gives a
support-balanced evidence-bounded interval of **72.47% to 81.91%**.

## Spatial concentration

Under the primary deterministic transport:

- Texas accounts for about **54.9%** of unmet biomass;
- Texas, Oklahoma and New Mexico together account for about **77.3%**;
- the top decile of positive-unmet counties accounts for about **56.2%**;
- 973 counties are binding in the family-balanced support-balanced reporting layer.

The corresponding offer+rent sensitivity leaves those concentration statistics
nearly unchanged.

## Physical map accounting

Absolute Figure 4 quantities use the county-level mean across independent POLYSYS
allocation families represented in each county rather than the sum across alternative
families.

The reporting totals are approximately:

- **448.744 million dry tons** prospectively allocated;
- **91.402 million dry tons** unmet.

## Reporting boundary

The legacy gross-biomass-revenue-per-acre diagnostic is exploratory only. It is not
used as the main economic feasibility test because the KBS monetary treatment is a
land-rental offer whereas the POLYSYS biomass price values biomass output.

The authoritative scientific calculations remain the validated BioLand-US pipeline
outputs. The Excel workbook is a reporting and plotting layer.
