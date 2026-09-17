# BioLand-US

**Contractual land access and prospective U.S. perennial-biomass mobilization**

BioLand-US is the public code and reproducibility companion for the manuscript **“Contractual land access constrains prospective US biomass mobilization.”**

The model asks a simple implementation question: when a techno-economic model allocates land to perennial biomass, how much of that prospective allocation can also be supported by compatible agricultural land and voluntary contractual participation?

BioLand-US does not rerun or re-optimize POLYSYS. It adds an explicit downstream implementation layer.

## Start here for reviewers

A reviewer can inspect the frozen manuscript-facing evidence without obtaining respondent-level behavioural data:

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

The release check verifies the public manuscript tables, reconciliation ledger, five-figure index, bundled frozen inputs, uncertainty settings and absence of restricted respondent records.

For exact data access instructions, provider links and SHA-256 checksums, see:

- [`docs/data_access.md`](docs/data_access.md)
- [`data/source_registry.csv`](data/source_registry.csv)
- [`docs/reproducibility.md`](docs/reproducibility.md)

## Scientific framework

BioLand-US keeps four quantities distinct:

```text
POLYSYS techno-economic biomass allocation
        ↓
compatible agricultural land
        ↓
contractually accessible land
        ↓
prospectively mobilized biomass
```

For county `c` and land pool `l`:

```text
A_P    upstream POLYSYS acreage requirement
Q_P    upstream POLYSYS biomass production
B      compatible agricultural land
p      probability of contract participation
s      conditional acreage share among participants
b      landholder-level behavioural access, p × s
kappa  county-by-land acreage-access rate under the transmission rule
K      contractual land-access capacity, B × kappa
```

The composition-preserving matching rule is:

```text
rho    = A_P / K
lambda = min(1, K / A_P)

A_M = lambda × A_P
Q_M = lambda × Q_P
```

The main national outcome is:

```text
M_Q = sum(Q_M) / sum(Q_P)
```

County maps therefore represent **spatial implementation exposure under nationally transported experimental behaviour**. They are not maps of observed county willingness.

## Evidence used

### POLYSYS

The upstream resource layer retains the 2023 Billion-Ton POLYSYS allocation for:

- year: **2041**;
- biomass price case: **US$70 per dry ton**;
- land sources: **Crop** and **Pasture**;
- seven perennial resources: switchgrass, miscanthus, energy cane, poplar, willow, eucalyptus and pine.

Four original scenario labels are preserved for provenance. Two are exact row-level duplicates in the retained perennial allocation, so robustness summaries use **three independent allocation families** rather than counting the duplicate twice.

POLYSYS `harvest` acreage and `prod` dry tons are treated as source quantities. BioLand-US does not reconstruct acreage from reported yield fields.

### Study-A behavioural experiment

The behavioural evidence comes from the KBS Bioenergy and Land Use Survey, a randomized stated-preference experiment on perennial-biomass contracts in southern Michigan.

The final extensive-margin sample contains:

- **403 respondents**;
- **1,270 experimental choices**;
- **356 accepted choices**.

Randomized annual land-rental offers were **US$50, US$100, US$200 and US$300 per acre per year**, with **5-year** and **10-year** contract durations.

The smooth log-dollar transport specification is:

```text
logit(p) =
    -6.017543
    + 0.943158 ln(offer)
    - 0.081661 I(10-year)
    + 0.0214773 I(Pasture)
    + 0.746083 I(Switchgrass)
```

The central conditional-acreage representation is:

```text
s = 0.863337
```

These frozen non-disclosive parameters are versioned in both `config/default.toml` and `data/frozen/public/behaviour_parameters_public.csv`.

### Feedstock transfer

Study A directly evaluates switchgrass and poplar. National transport therefore uses an explicit treatment-class mapping:

```text
Switchgrass, Miscanthus, Energy cane
    → Switchgrass experimental archetype

Poplar, Willow, Eucalyptus, Pine
    → Poplar experimental archetype
```

This is a modelling assumption for transport. It is not evidence that respondents directly evaluated the untested species.

### Compatible land

The central land base is derived from the 2022 Census of Agriculture:

```text
Crop = total cropland - cropland pastured only

Pasture = cropland pastured only
        + pastureland excluding cropland and woodland
```

Disclosure-suppressed Census values are not treated as zero. The completed land layer retains `JOINT_EQUAL`, `JOINT_OWNED` and `JOINT_RENTED` structural surfaces, with `JOINT_EQUAL` as the central reference.

### Rent context

The frozen rent hierarchy is:

1. county, same land type, 2022;
2. nearest same-county observation within ±3 years;
3. official same-land state estimate for 2022;
4. unsupported.

Supported values are converted to **2012 U.S. dollars** before behavioural transport. Unsupported cells remain explicit and are not converted to zero rent or zero behavioural access.

## Data access

BioLand-US does **not** hide missing source information behind vague “available on request” language. Each input is assigned a clear access class.

| Input | Access | Repository treatment |
|---|---|---|
| POLYSYS / 2023 Billion-Ton allocation | Public | Download from ORNL Bioenergy KDF and verify checksum |
| 2022 Census Quick Stats bulk file | Public | Download from USDA NASS and verify checksum |
| County cash rents | Public NASS query export | Obtain from NASS Quick Stats and verify exact frozen export |
| 2022 state cash rents | Public NASS query export | Obtain from NASS Quick Stats and verify exact frozen export |
| CPI-U annual averages | Public | Small frozen table bundled in this repository |
| County geometry | Public | Obtain from USDA 2022 Census Ag Atlas / Web Maps |
| Study-A respondent records | Third-party terms apply | Never redistributed; obtain from KBS LTER/PASTA |

The two stable large public archives can be downloaded automatically:

```bash
python scripts/00_fetch_public_sources.py
```

The helper verifies exact SHA-256 values and also checks the rent exports and geometry when they are placed under `data/raw/`.

The Study-A DOI is:

```text
10.6073/pasta/3f43b536ef860a2046db415b22ffcd6a
```

Respondent-level records are not included in GitHub. This restriction applies to behavioural re-estimation, not to inspection of the public frozen coefficients or manuscript-facing national results.

## Public versus restricted reproduction

BioLand-US separates two tasks that are often conflated.

### Public national-model reproduction

The deterministic national implementation uses the frozen behavioural parameters and does not require respondent-level KBS records merely to evaluate contractual access and biomass mobilization.

After the documented public spatial inputs have been prepared:

```bash
python scripts/00_run_core.py
```

### Behavioural re-estimation

Researchers who obtain authorized Study-A respondent data can independently re-estimate and validate the behavioural stage:

```stata
do stata/00_run_behaviour.do
```

and can request the restricted validation gate explicitly:

```bash
python scripts/00_run_core.py --validate-restricted-behaviour
```

## Land-rental scenarios

Two scenario families are retained.

Experiment-anchored offers:

```text
US$50
US$100
US$200
US$300 per acre per year
```

Rent-indexed offers:

```text
offer = m × county cash rent
```

with:

```text
m = 1.0000
m = 3.3544
m = 6.7088
m = 13.4175
m = 20.1263
```

The `m = 6.7088` case is the **national support-balanced reference**. It is an evidential reference, not an equilibrium price or policy optimum.

## Institutional transmission

The identified quantitative analysis implements:

```text
T1_POOLED_BEHAVIOURAL_TRANSMISSION
```

Potential T2-T4 role-differentiated alternatives remain unquantified because defensible national role-control formulas and weights have not been frozen. The repository does not assign arbitrary values to them.

## Repository structure

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

## Manuscript-facing outputs

Compact, non-disclosive tables supporting the reported results are retained under `results/manuscript/`. The frozen audit trail is under `results/validation/`.

The manuscript uses five main Results figures:

1. behavioural evidence;
2. national mobilization and support exposure;
3. uncertainty and evidence coverage;
4. prospective allocation and unmet biomass;
5. spatial implementation robustness.

The synchronized panel index is stored in `results/figures/figure_index.csv`.

## Reporting workbook and figures

The final workbook is a generated reporting artefact. It is produced from the validated reporting seed and audited upstream outputs:

```bash
python scripts/13_build_figure_workbook.py --seed <validated_seed_workbook.xlsx>
python scripts/14_make_figures.py --workbook results/figures/BioLandUS_FigureWorkbook_v7_FINAL.xlsx
```

The workbook builder owns reporting arithmetic and reconciliation checks. The plotting script is read-only and performs no scientific re-estimation.

## Scientific safeguards

The clean workflow enforces the following rules:

- no POLYSYS re-optimization;
- no double use of county-by-land capacity across feedstocks;
- no conversion of unsupported rent to zero;
- no arbitrary finite replacement for infinite implementation pressure;
- no mixing of statistical bootstrap uncertainty with structural sensitivity;
- no claim that treatment-class transfer equals direct experimental evidence;
- no quantitative T2-T4 institutional scenarios without defensible national parameters;
- no interpretation of county maps as locally estimated willingness;
- no redistribution of restricted respondent-level data.

## Tests and release verification

Core unit tests run locally with:

```bash
python -m pytest
```

and automatically in GitHub Actions on pushes and pull requests to `main`.

The manuscript-facing public release can be checked with:

```bash
python scripts/00_verify_release.py
```

## Citation

Use [`CITATION.cff`](CITATION.cff) to cite the software repository. A manuscript DOI can be added after publication.

## Author

**Elvis Kwame Ofori**  
University of Galway
