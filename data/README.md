# BioLand-US data

| Folder | In git? | Content |
|---|---|---|
| `data/raw/` | no | Original provider files, unchanged. Names and SHA-256 in `source_registry.csv`. |
| `data/restricted/` | no | Study-A respondent records extracted by Stata. Never commit. |
| `data/frozen/restricted/` | no | Respondent-level Stata exports used by the bootstrap. Never commit. |
| `data/interim/` | no | Caches (for example the Census land-item extract). |
| `data/frozen/public/` | yes | Small derived tables, see its README. |

## Raw sources

Place these in `data/raw/` with their original names (or run
`python scripts/00_fetch_public_sources.py` for the ones with stable URLs):

- `AgriResdJetCropProd_wHrvYldwAnnl_0.1.zip`: POLYSYS / Billion-Ton 2023
- `qs.census2022.txt.gz`: USDA NASS Quick Stats, 2022 Census of Agriculture
- `9A9F55D7-E267-38C6-ACB9-DF106291B5A7.csv`: NASS county cash rents
- `73DE05FF-2AD9-384C-AFB1-E47106AFC525.csv`: NASS 2022 state cash rents
- `CoUSAKHI_LAEA_2022.zip`: county geometry (maps)
- `knb-lter-kbs.124.2.zip`: KBS Study-A survey (third-party terms; not redistributed)

Suppressed Census values and missing rents are never read as zero; see
`docs/DECISIONS.md` (L03, L04, R02).
