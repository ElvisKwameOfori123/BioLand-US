# Figure outputs

The manuscript now uses five main Results figures:

1. **Behavioural evidence**: participation by annual land-rental offer, conditional acreage among accepters, and identity-consistent behavioural land access.
2. **National mobilization**: experiment-anchored rental offers, rent-indexed land-access offers, experimental-support exposure, and unmet-biomass concentration.
3. **Uncertainty and robustness**: structural, statistical, evidence-bounded, rent-context, allocation-family and contract-duration sensitivity, plus feedstock evidence coverage.
4. **Physical geography**: prospective biomass allocation and unmet prospective biomass, using county means across represented independent POLYSYS allocation families.
5. **Spatial robustness**: implementation pressure, probability of binding, top-risk probability and cross-family hotspot consensus.

The main manuscript remains at five figures plus one table. Crop/Pasture heterogeneity
and the full behavioural-transport comparison are supplementary/Extended Data outputs.

## Current reporting workbook

The frozen reporting workbook is:

```text
results/figures/BioLandUS_FigureWorkbook_v7_FINAL.xlsx
```

The workbook is a reporting layer. Scientific calculations are generated upstream
and imported with reconciliation checks.

Key additions in v7 are:

- audited Stage 03B conditional-acreage-by-offer margins;
- Figure 1c `b = p × s` identity correction;
- evidence-bounded extrapolation and rent-context transport rows in Figure 3;
- Crop/Pasture frontier and support-exposure tables;
- transport-robustness and support-bounded supplementary tables;
- family-mean absolute-quantity fields for Figure 4.

The historical `scripts/10_make_figures.py` entrypoint predates the final five-figure
architecture and is retained only as a legacy reference until the final submission
plotter is synchronized.
