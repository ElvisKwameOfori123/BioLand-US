"""Retrieve or verify the public third-party sources used by BioLand-US.

This helper deliberately downloads only sources with stable public file URLs.
Quick Stats query exports and the county geometry are documented and checksum-
verified when placed locally. Restricted KBS respondent data are never fetched
or redistributed by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

AUTO_SOURCES = {
    "polysys": {
        "filename": "AgriResdJetCropProd_wHrvYldwAnnl_0.1.zip",
        "url": "https://bioenergykdf.ornl.gov/system/files/4829/AgriResdJetCropProd_wHrvYldwAnnl_0.1.zip",
        "sha256": "9974df899c155a865da4275adaa011029dca35021763256e197747f59b7c8406",
        "landing": "https://bioenergykdf.ornl.gov/document/customized-dataset-yield-agricultural-resources-modeled-polysys",
    },
    "census": {
        "filename": "qs.census2022.txt.gz",
        "url": "https://www.nass.usda.gov/datasets/qs.census2022.txt.gz",
        "sha256": "eca0f82dea58e1b128b82ac15f54e8bfc70cfb097e3e87710b74e7e93877dbbd",
        "landing": "https://www.nass.usda.gov/datasets/",
    },
}

MANUAL_SOURCES = {
    "county_rents": {
        "canonical": "nass_county_cash_rents.csv",
        "aliases": ["9A9F55D7-E267-38C6-ACB9-DF106291B5A7.csv"],
        "sha256": "03751be35e7ca64637528633576bdcc69075b5fdccffdb6516da59e22048c780",
        "source": "USDA NASS Quick Stats / Cash Rents by County",
        "url": "https://www.nass.usda.gov/Surveys/Guide_to_NASS_Surveys/Cash_Rents_by_County/",
    },
    "state_rents": {
        "canonical": "nass_state_cash_rents_2022.csv",
        "aliases": ["73DE05FF-2AD9-384C-AFB1-E47106AFC525.csv"],
        "sha256": "14904e432da3e229b4e697ecbbcf703660dde543dbcf32fcba521e3bcfa6202d",
        "source": "USDA NASS Quick Stats, 2022 state cash-rent export",
        "url": "https://quickstats.nass.usda.gov/",
    },
    "geometry": {
        "canonical": "us_county_geometry_2022.zip",
        "aliases": ["CoUSAKHI_LAEA_2022.zip", "CoUSAKHI_LAEA_2022(2).zip"],
        "sha256": "ef6e8e4e1afb71c2401f909e1e3f7f6995f534e897cdb4a69b617820ef886c2c",
        "source": "USDA NASS 2022 Census Ag Atlas / Web Maps county geometry",
        "url": "https://www.nass.usda.gov/Publications/AgCensus/2022/Online_Resources/Ag_Census_Web_Maps/Data_download/index.php",
    },
}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(chunk_size)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def verify(path: Path, expected: str) -> bool:
    observed = sha256_file(path)
    ok = observed.lower() == expected.lower()
    print(f"{'PASS' if ok else 'FAIL'}  {path.name}")
    if not ok:
        print(f"      expected: {expected}")
        print(f"      observed: {observed}")
    return ok


def download(name: str, spec: dict[str, str], *, force: bool, verify_only: bool) -> bool:
    path = RAW / spec["filename"]
    if path.exists() and not force:
        return verify(path, spec["sha256"])

    if verify_only:
        print(f"MISSING {path.name}")
        return False

    tmp = path.with_suffix(path.suffix + ".part")
    print(f"DOWNLOAD {name}: {spec['url']}")
    request = urllib.request.Request(
        spec["url"],
        headers={"User-Agent": "BioLand-US reproducibility helper"},
    )
    with urllib.request.urlopen(request) as response, tmp.open("wb") as out:
        shutil.copyfileobj(response, out)

    if not verify(tmp, spec["sha256"]):
        tmp.unlink(missing_ok=True)
        return False
    tmp.replace(path)
    return True


def find_manual(spec: dict[str, object]) -> Path | None:
    names = [str(spec["canonical"]), *[str(x) for x in spec["aliases"]]]
    for name in names:
        path = RAW / name
        if path.exists():
            return path
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        nargs="*",
        choices=sorted(AUTO_SOURCES),
        default=sorted(AUTO_SOURCES),
        help="Stable public sources to retrieve. Default: POLYSYS and 2022 Census.",
    )
    parser.add_argument("--force", action="store_true", help="Redownload stable sources.")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Do not download; only check files already under data/raw.",
    )
    args = parser.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    ok = True

    print("=" * 78)
    print("BioLand-US public-source acquisition and verification")
    print("=" * 78)
    for name in args.source:
        ok = download(
            name,
            AUTO_SOURCES[name],
            force=args.force,
            verify_only=args.verify_only,
        ) and ok

    print("\nManual/public query exports")
    print("-" * 78)
    for name, spec in MANUAL_SOURCES.items():
        path = find_manual(spec)
        if path is None:
            print(f"MISSING {name}: place {spec['canonical']} under data/raw/")
            print(f"        source: {spec['url']}")
            ok = False
        else:
            file_ok = verify(path, str(spec["sha256"]))
            ok = file_ok and ok
            canonical = RAW / str(spec["canonical"])
            if file_ok and path != canonical and not canonical.exists():
                shutil.copy2(path, canonical)
                print(f"      copied to canonical local name: {canonical.name}")

    print("\nRestricted behavioural source")
    print("-" * 78)
    print("KBS Study-A respondent records are intentionally NOT downloaded by this helper.")
    print("Obtain them from KBS LTER/PASTA under the applicable data-use terms:")
    print("https://doi.org/10.6073/pasta/3f43b536ef860a2046db415b22ffcd6a")

    print("\nSee docs/data_access.md and data/source_registry.csv for full provenance.")
    if not ok:
        print("\nOne or more public inputs are missing or failed checksum verification.")
        raise SystemExit(1)
    print("\nPASS: all public inputs available to this helper match the frozen checksums.")


if __name__ == "__main__":
    main()
