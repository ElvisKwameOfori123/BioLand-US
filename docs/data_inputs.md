# Data inputs

The exact source-file ledger and SHA-256 checksums are recorded in
[`data/source_registry.csv`](../data/source_registry.csv).

BioLand-US separates raw source acquisition from manuscript-facing analysis.
The clean scripts operate on documented canonical inputs rather than replaying
every vendor-specific development layout.

## Restricted behavioural inputs

Restricted Study-A microdata are not distributed in this repository.

The behavioural pipeline validates the final 1,270-choice / 403-respondent
extensive sample and the frozen intensive-margin architecture before exporting
canonical inputs for Python.

The randomized monetary treatment is an **annual land-rental offer per acre per year**
at US$50, US$100, US$200 or US$300, with 5- or 10-year contract duration.

For rent-context sensitivity, a locally held restricted rent-matched Study-A file is
used by `stata/06_export_transport_sensitivity.do`. That script exports coefficients
only; respondent-level data remain restricted.

## POLYSYS allocation

The retained perennial allocation is standardized to:

- scenario / independent allocation family;
- county FIPS;
- land type;
- feedstock;
- harvested acres;
- dry-ton production.

The clean analysis uses three independent allocation families. The `emerging` and
`mature-market high` source labels are verified as exact allocation duplicates before
one representative is retained.

The POLYSYS biomass price is an upstream biomass-market condition and is analytically
distinct from the KBS annual land-rental offer.

## Census compatible land

The central compatible-land surface uses the frozen JOINT_EQUAL completion. JOINT_OWNED
and JOINT_RENTED are alternative **disclosure-suppression completion structures**, not
owner-operated and tenant-operated tenure categories.

## Cash-rent context

The rent hierarchy is:

1. exact county, same land type, 2022;
2. same county and land type, nearest year within ±3 years;
3. official USDA/NASS state 2022 value for the same land type;
4. unsupported.

Supported rents are converted to 2012 US dollars. Unsupported cells remain missing and
are never interpreted as zero rent or zero participation.

Rent-indexed land-access offers are generated as `O = m × R`.

## Behavioural robustness outputs

`scripts/10_transport_robustness.py` requires coefficient exports from
`stata/06_export_transport_sensitivity.do` and propagates:

- primary absolute-dollar transport;
- pure offer/rent stress test;
- unrestricted offer + local-rent sensitivity.

`scripts/11_figure1_identity_audit.py` verifies the frozen `b = p × s` identity.

`scripts/12_support_bounded_extrapolation.py` uses the experiment-anchored Stage 07E
boundary probabilities to impose monotonic bounds outside US$50 to US$300 while leaving
within-support participation unchanged.

## County geometry

County geometry is used only for spatial joins and manuscript maps.

## Reporting workbook

The final reporting-layer target is:

```text
results/figures/BioLandUS_FigureWorkbook_v7_FINAL.xlsx
```

The workbook contains reconciliation checks, style information and figure-ready tables.
It is not the authoritative scientific computation layer.

Absolute Figure 4 quantities use county-level means across independent allocation
families represented in each county. Alternative upstream families must not be summed
as though they were simultaneous physical supplies.
