# Reproducibility design

This document explains how the public BioLand-US repository differs from the longer development pipeline used to build and audit the model.

## Development code versus public reproducibility code

The development project intentionally used many small stage scripts and diagnostic gates. That was useful for forensic reconstruction, source auditing, and freezing scientific decisions. It is not the best interface for other researchers.

The public repository therefore follows two rules:

1. **Preserve the frozen scientific decisions.**
2. **Remove development redundancy.**

The clean workflow should reproduce the frozen outputs without requiring users to understand every exploratory stage that preceded them.

## Clean stage boundaries

### 01 Behaviour

Prepare the experimental choice data and reproduce the frozen extensive- and intensive-margin quantities.

### 02 POLYSYS

Prepare the retained 2041 perennial allocation at US$70 per dry ton and identify the three independent allocation families.

### 03 Land

Construct the compatible county Crop and Pasture pools and apply the frozen Census completion rules.

### 04 Rent

Build the county-by-land 2012-dollar rent context using the frozen evidence hierarchy.

### 05 Behavioural access

Evaluate participation at the relevant offers and combine it with the frozen conditional-acreage representation:

```
b = p * s
```

Behavioural access is not yet national acreage access.

### 06 Capacity and mobilization

Apply the implemented transmission assumption, compute contractual capacity once per county-by-land pool, and compare it with the upstream acreage requirement.

```
K = B * kappa
rho = A_polysys / K
lambda = min(1, K / A_polysys)
A_mobilized = lambda * A_polysys
Q_mobilized = lambda * Q_polysys
```

Zero-capacity cells are explicitly retained as binding.

### 07 Statistical uncertainty

Use paired respondent-level bootstrap draws so the same resampled respondents determine the extensive and intensive margins.

### 08 Structural sensitivity

Evaluate structural alternatives separately from statistical resampling.

### 09 Spatial robustness

Create county-level implementation pressure, probability of binding, top-risk probability, and hotspot-consensus outputs.

### 10 Figures

Read frozen reporting outputs only. Plotting code must not re-estimate the scientific model.

## Fail-fast validations

Every clean stage should fail rather than silently continue when:

- required columns are absent;
- expected identifiers are duplicated;
- bounded probabilities or shares leave [0, 1];
- unsupported rent cells are converted to zero;
- mobilized acreage or biomass exceeds the upstream allocation;
- zero-capacity rules are violated;
- allocation-family independence is miscounted;
- bootstrap draw counts are incomplete;
- structural and statistical uncertainty are accidentally combined.

## Reproducible paths

No script should contain a user-specific absolute path.

Project paths are resolved relative to the repository root and may be overridden by a local, gitignored configuration file.

## Public release strategy

The repository should be made public only after confirming:

- no restricted survey microdata are present;
- no temporary files contain respondent-level information;
- third-party data licences permit any redistributed extracts;
- the manuscript and repository terminology agree;
- the public scripts reproduce the archived results and figures from a clean environment.
