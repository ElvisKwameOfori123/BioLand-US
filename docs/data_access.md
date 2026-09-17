# Data access and reproducibility boundary

BioLand-US combines public U.S. agricultural data with a third-party behavioural survey whose respondent-level records are subject to KBS LTER data-use terms. This page tells a reviewer exactly what is bundled, what is downloaded from the original provider, and what requires separate authorization.

## Reviewer fast path

To inspect the manuscript-facing evidence without obtaining restricted microdata:

```bash
git clone https://github.com/ElvisKwameOfori123/BioLand-US.git
cd BioLand-US
pip install -e ".[dev]"
python -m pytest
python scripts/00_verify_release.py
```

The public repository contains the frozen model parameters, manuscript-facing result tables and reconciliation checks needed to verify the reported quantities. Re-estimating the behavioural coefficients from respondent-level Study-A records is a separate restricted-data stage.

## Source access matrix

| Input | Status | Authoritative source | Exact frozen file / identifier | Repository treatment |
|---|---|---|---|---|
| POLYSYS / 2023 Billion-Ton perennial allocation | Public | ORNL Bioenergy KDF | `AgriResdJetCropProd_wHrvYldwAnnl_0.1.zip`; DOI `10.23720/BT2023/2350581` | Download from provider; checksum-verify |
| 2022 Census of Agriculture Quick Stats bulk file | Public | USDA NASS | `qs.census2022.txt.gz` | Download from provider; checksum-verify |
| County cash rents | Public query export | USDA NASS Quick Stats / Cash Rents by County | `9A9F55D7-E267-38C6-ACB9-DF106291B5A7.csv` | Obtain from NASS; checksum-verify |
| 2022 state cash-rent fallback | Public query export | USDA NASS Quick Stats | `73DE05FF-2AD9-384C-AFB1-E47106AFC525.csv` | Obtain from NASS; checksum-verify |
| CPI-U annual averages | Public | U.S. Bureau of Labor Statistics | annual averages used for 2012-dollar conversion | Small frozen table bundled in `data/frozen/public/` |
| County geometry | Public | USDA NASS 2022 Census Ag Atlas / Web Maps | `CoUSAKHI_LAEA_2022.zip` | Obtain from USDA; checksum-verify |
| Study-A Bioenergy and Land Use Survey | Third-party, terms apply | KBS LTER / PASTA | `knb-lter-kbs.124.2.zip`; DOI `10.6073/pasta/3f43b536ef860a2046db415b22ffcd6a` | Respondent records are never redistributed |

Exact SHA-256 values are stored in [`data/source_registry.csv`](../data/source_registry.csv).

## One-command public-source helper

The two large sources with stable direct file URLs can be retrieved and verified automatically:

```bash
python scripts/00_fetch_public_sources.py
```

The helper downloads:

- the exact Bioenergy KDF POLYSYS archive used by BioLand-US;
- the exact 2022 Census of Agriculture Quick Stats bulk file.

It also checks whether the exact NASS county-rent export, state-rent export and county-geometry archive have been placed under `data/raw/`, and verifies them against the frozen checksums. These query-generated or download-page products are not silently replaced by newer files.

## Public files bundled in the repository

Small, non-disclosive inputs are versioned directly:

```text
data/frozen/public/cpi_u_annual.csv
data/frozen/public/behaviour_parameters_public.csv
```

The behavioural parameter table contains the frozen coefficients and conditional-acreage representations used by the public national implementation. These quantities are sufficient to run the national behavioural transport once the public spatial inputs have been constructed. They do not expose respondent-level records.

## Restricted Study-A data

The behavioural experiment is archived by KBS LTER/PASTA. BioLand-US does not redistribute the respondent-level archive. Researchers who need to independently re-estimate the behavioural models should obtain the source from KBS LTER/PASTA and comply with the applicable repository terms and permissions.

The public repository therefore separates two reproducibility goals:

1. **Manuscript-result verification and national-model reproduction:** use the frozen non-disclosive behavioural parameters, public agricultural inputs, public result tables and versioned model code.
2. **Behavioural re-estimation:** obtain the Study-A respondent data from KBS LTER/PASTA and run the Stata behavioural pipeline locally.

This separation is intentional. Absence of respondent records from GitHub should not be interpreted as missing provenance or as permission to reconstruct or redistribute those records.

## Public-source landing pages

- POLYSYS / Bioenergy KDF: https://bioenergykdf.ornl.gov/document/customized-dataset-yield-agricultural-resources-modeled-polysys
- USDA NASS large datasets: https://www.nass.usda.gov/datasets/
- USDA NASS Quick Stats: https://quickstats.nass.usda.gov/
- USDA NASS Cash Rents by County: https://www.nass.usda.gov/Surveys/Guide_to_NASS_Surveys/Cash_Rents_by_County/
- USDA 2022 Census Ag Atlas / Web Maps downloads: https://www.nass.usda.gov/Publications/AgCensus/2022/Online_Resources/Ag_Census_Web_Maps/Data_download/index.php
- BLS CPI data: https://www.bls.gov/cpi/data.htm
- KBS Study-A DOI: https://doi.org/10.6073/pasta/3f43b536ef860a2046db415b22ffcd6a

## Why the raw archives are not copied into GitHub

Large third-party archives are kept at their authoritative source rather than duplicated. This avoids stale mirrors and makes provenance explicit. BioLand-US records the exact filenames and checksums so that a reviewer can verify that the same source files are being used.

Restricted respondent-level material is excluded for a different reason: it is governed by the source repository's data-use terms.
