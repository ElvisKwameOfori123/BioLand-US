# BioLand-US

**Contractual land access and prospective U.S. perennial-biomass mobilization**

[![tests](https://github.com/ElvisKwameOfori123/BioLand-US/actions/workflows/ci.yml/badge.svg)](https://github.com/ElvisKwameOfori123/BioLand-US/actions/workflows/ci.yml)
[![license: CC0-1.0](https://img.shields.io/badge/license-CC0--1.0-lightgrey.svg)](LICENSE)

BioLand-US is the public code and reproducibility companion for the manuscript **“Contractual land access constrains prospective US biomass mobilization.”**

It asks one implementation question:

> **When a techno-economic model allocates land to perennial biomass, how much of that prospective allocation can be supported by compatible agricultural land, experimentally informed landholder behaviour and the institutional transmission of that behaviour into contractually accessible acreage?**

BioLand-US does **not** rerun or re-optimize POLYSYS. It adds a downstream implementation layer that distinguishes prospective resource allocation from contractual implementation capacity and traces the pathway from compatible land, through behavioural access and institutional transmission, to prospective biomass mobilization.

---

## Research logic

```text
prospective POLYSYS allocation
        ↓
compatible agricultural land
        ↓
behavioural land access
        ↓
institutional transmission
        ↓
contractual capacity
        ↓
prospectively mobilized biomass
```

This distinction matters because prospective biomass allocation does not itself establish the contractual land access required for implementation.

County maps therefore represent **spatial implementation exposure under nationally transported experimental behaviour**. They are not maps of observed county willingness.

---

## Reproduce the study

BioLand-US separates three reproducibility tasks because the behavioural microdata are governed by third-party access terms.

### 1. Verify the public manuscript-facing release

This route requires no respondent-level records.

```bash
git clone https://github.com/ElvisKwameOfori123/BioLand-US.git
cd BioLand-US

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev]"
python -m pytest
python scripts/00_verify_release.py
```

The verification script checks the frozen manuscript tables, figure index, reconciliation ledger, bundled public inputs, uncertainty settings and the absence of restricted respondent records.

### 2. Reproduce the public national implementation

Retrieve and verify the stable public source archives:

```bash
python scripts/00_fetch_public_sources.py
```

After the documented public spatial inputs have been prepared:

```bash
python scripts/00_run_core.py
```

See [data access](docs/data_access.md) and [reproducibility](docs/reproducibility.md) for exact source files, checksums and preparation boundaries.

### 3. Re-estimate the behavioural model

Independent re-estimation requires authorized access to the KBS Bioenergy and Land Use Survey respondent records.

```stata
do stata/00_run_behaviour.do
```

Restricted behavioural validation can then be requested explicitly:

```bash
python scripts/00_run_core.py --validate-restricted-behaviour
```

The respondent-level archive is never redistributed through GitHub.

---

## Evidence base

BioLand-US combines five evidence layers:

| Evidence | Role |
|---|---|
| 2023 Billion-Ton POLYSYS allocation | Upstream perennial-biomass allocation |
| 2022 U.S. Census of Agriculture | Compatible crop and pasture land |
| USDA NASS cash rents | Local rent context |
| KBS Bioenergy and Land Use Survey | Contract-participation behaviour |
| County geometry | Spatial matching and publication cartography |

The central POLYSYS case retains the **2041, US$70 per dry ton** allocation for seven perennial resources across Crop and Pasture land sources.

The behavioural evidence comes from a randomized stated-preference experiment in southern Michigan with **403 respondents, 1,270 experimental choices and 356 accepted choices**. Frozen non-disclosive parameters used by the public national model are versioned in the repository.

Study-A source DOI:

```text
10.6073/pasta/3f43b536ef860a2046db415b22ffcd6a
```

---

## Data access boundary

The repository distinguishes public source data, public frozen parameters and restricted respondent records.

| Input | Access | Repository treatment |
|---|---|---|
| POLYSYS / 2023 Billion-Ton allocation | Public | Download from ORNL Bioenergy KDF and checksum-verify |
| 2022 Census Quick Stats bulk file | Public | Download from USDA NASS and checksum-verify |
| County and state cash rents | Public query export | Obtain from NASS and verify the frozen export |
| CPI-U annual averages | Public | Small frozen table bundled in the repository |
| County geometry | Public | Obtain from USDA Census of Agriculture mapping resources |
| Study-A respondent records | Third-party terms apply | Never redistributed |

Exact provider links, filenames and SHA-256 values are recorded in:

- [`docs/data_access.md`](docs/data_access.md)
- [`data/source_registry.csv`](data/source_registry.csv)

This is a deliberate reproducibility boundary, not an “available on request” gap.

---

## Repository map

```text
BioLand-US/
├── .github/workflows/ci.yml
├── config/
├── data/
│   ├── README.md
│   ├── source_registry.csv
│   └── frozen/public/
├── docs/
│   ├── data_access.md
│   ├── data_inputs.md
│   └── reproducibility.md
├── results/
│   ├── manuscript/
│   ├── figures/
│   └── validation/
├── scripts/
├── src/bioland_us/
├── stata/
├── tests/
├── CITATION.cff
├── LICENSE
├── pyproject.toml
└── README.md
```

**Python** is the main national implementation and reporting environment. **Stata** is used for behavioural re-estimation from authorized Study-A records.

GitHub Actions runs the core unit tests and public release verification on pushes and pull requests to `main`.

---

## Manuscript-facing outputs

The public repository retains compact, non-disclosive outputs supporting the reported results.

The manuscript uses five main Results figures:

1. behavioural evidence;
2. national mobilization and support exposure;
3. uncertainty and evidence coverage;
4. prospective allocation and unmet biomass;
5. spatial implementation robustness.

The synchronized figure index is stored at:

```text
results/figures/figure_index.csv
```

Frozen reconciliation checks are retained under `results/validation/`.

---

## Scientific safeguards

The public implementation enforces several rules explicitly:

- no POLYSYS re-optimization;
- no double use of county-by-land capacity across feedstocks;
- no conversion of unsupported rent to zero;
- no arbitrary finite replacement for infinite implementation pressure;
- no mixing of bootstrap uncertainty with structural sensitivity;
- no claim that treatment-class transfer equals direct experimental evidence;
- no interpretation of county maps as locally estimated willingness;
- no redistribution of restricted respondent-level data.

<details>
<summary><strong>Core accounting notation</strong></summary>

For county `c` and land pool `l`:

```text
A_P    upstream POLYSYS acreage requirement
Q_P    upstream POLYSYS biomass production
B      compatible agricultural land
p      probability of contract participation
s      conditional acreage share among participants
kappa  county-by-land acreage-access rate
K      contractual land-access capacity, B × kappa

rho    = A_P / K
lambda = min(1, K / A_P)

A_M = lambda × A_P
Q_M = lambda × Q_P
```

The main national mobilization quantity is:

```text
M_Q = sum(Q_M) / sum(Q_P)
```

</details>

<details>
<summary><strong>Behavioural transport and feedstock classes</strong></summary>

The central behavioural specification uses randomized land-rental offers of US$50, US$100, US$200 and US$300 per acre per year with 5-year and 10-year contracts.

Study A directly evaluates switchgrass and poplar. National transport therefore uses an explicit treatment-class mapping:

```text
Switchgrass, Miscanthus, Energy cane
    → Switchgrass experimental archetype

Poplar, Willow, Eucalyptus, Pine
    → Poplar experimental archetype
```

This is a transport assumption, not evidence that respondents directly evaluated the untested species.

</details>

---

## Documentation

Start with these files:

- [Data access and reproducibility boundary](docs/data_access.md)
- [Reproducibility workflow](docs/reproducibility.md)
- [Source registry and checksums](data/source_registry.csv)
- [Machine-readable citation](CITATION.cff)

---

## Citation and archival status

Use [`CITATION.cff`](CITATION.cff) to cite the software repository.

The repository currently has **no GitHub Release and no Zenodo archival DOI**. A versioned release should be created first; the archival DOI can then be added to this README, `CITATION.cff` and the manuscript once Zenodo has archived the release.

---

## Author

**Elvis Kwame Ofori**  
Plant and AgriBiosciences Research Centre, Ryan Institute  
University of Galway, Galway, Ireland

Website: https://elviskwameofori123.github.io/

---

## Licence

The repository currently carries **CC0 1.0 Universal** in [`LICENSE`](LICENSE).

If a different software licence was intended, the licence file and repository metadata should be reconciled **before the first archival release**.

Third-party source datasets remain subject to the terms and attribution requirements of their original providers.
