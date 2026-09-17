# Figure outputs

The manuscript uses five main Results figures:

1. **Behavioural evidence**: participation by annual land-rental offer, conditional acreage among accepters, and identity-consistent behavioural land access.
2. **National mobilization**: experiment-anchored rental offers, rent-indexed land-access offers, experimental-support exposure, and unmet-biomass concentration.
3. **Uncertainty and robustness**: structural, statistical, evidence-bounded, rent-context, allocation-family and contract-duration sensitivity, plus feedstock evidence coverage.
4. **Physical geography**: prospective biomass allocation and unmet prospective biomass, using county means across represented independent POLYSYS allocation families.
5. **Spatial robustness**: implementation pressure, probability of binding, top-risk probability and cross-family hotspot consensus.

The main manuscript remains at five figures plus one table. Crop/Pasture heterogeneity
and the full behavioural-transport comparison are supplementary/Extended Data outputs.

## Final reporting workflow

```text
validated local seed workbook + audited upstream outputs
        ↓
scripts/13_build_figure_workbook.py
        ↓
results/figures/BioLandUS_FigureWorkbook_v7_FINAL.xlsx
        ↓
scripts/14_make_figures.py
        ↓
results/figures/main/
```

The builder imports audited upstream outputs and writes the reporting workbook.
The plotter is read-only and performs no scientific model calculation.

The final workbook is a generated local reporting artefact. The validated seed workbook and restricted-data-derived upstream products are not redistributed as public raw inputs. Public reproducibility is therefore supported through the versioned builder and plotting scripts, the source registry, manuscript-facing result tables and reconciliation checks. Authorized users with the frozen seed can regenerate the final workbook with:

```bash
python scripts/13_build_figure_workbook.py --seed <validated_seed_workbook.xlsx>
```

Key additions in the final reporting layer are:

- audited Stage 03B conditional-acreage-by-offer margins;
- Figure 1c `b = p × s` identity correction;
- evidence-bounded extrapolation and rent-context transport rows in Figure 3;
- Crop/Pasture frontier and support-exposure tables;
- transport-robustness and support-bounded supplementary tables;
- family-mean absolute-quantity fields for Figure 4.

Absolute Figure 4 quantities are county means across independent allocation families
represented in each county. Alternative upstream allocation families are not summed as
though they were simultaneous physical supplies.
