# Frozen canonical data

This directory separates small public inputs that are safe to version from larger generated or restricted analytical products.

## Bundled now

`public/` contains:

```text
cpi_u_annual.csv
behaviour_parameters_public.csv
README.md
```

These are non-disclosive and are part of the public reproducibility package.

## Generated locally

County-level canonical tables derived from large USDA/ORNL sources are generated locally and are not assumed to exist in a fresh clone. Typical outputs include the cleaned POLYSYS allocation, compatible Census land surfaces, rent context and behavioural-access tables. Their source files and checksums are documented in `../source_registry.csv`, and source acquisition is described in `../../docs/data_access.md`.

Restricted respondent-level or respondent-derived tables must remain under `frozen/restricted/` locally and must never be committed.

Do not place raw vendor/provider downloads, literature supplements, obsolete prototype tables or KBS respondent-level records in this directory.
