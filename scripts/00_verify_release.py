"""Fail-fast reviewer check for the public BioLand-US release."""

from __future__ import annotations

import hashlib
import sys
import tomllib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    ROOT / "README.md",
    ROOT / "docs" / "data_access.md",
    ROOT / "data" / "source_registry.csv",
    ROOT / "data" / "frozen" / "public" / "cpi_u_annual.csv",
    ROOT / "data" / "frozen" / "public" / "behaviour_parameters_public.csv",
    ROOT / "results" / "manuscript" / "headline_results.csv",
    ROOT / "results" / "manuscript" / "experiment_mobilization.csv",
    ROOT / "results" / "manuscript" / "rent_indexed_mobilization.csv",
    ROOT / "results" / "manuscript" / "uncertainty_summary.csv",
    ROOT / "results" / "validation" / "reconciliation_checks.csv",
    ROOT / "results" / "validation" / "provenance.csv",
    ROOT / "results" / "figures" / "figure_index.csv",
]

EXPECTED_CPI_SHA256 = "4fe551b34e2ac852bbd0cd228252ff2c2320127b4a35fbede30e82c6b08549a7"
EXPECTED_BEHAVIOUR_SHA256 = "b642e3d66b343a352a6b4f8ac79bf2ab449777c1617e8069138d694a430db0ad"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> None:
    for path in REQUIRED:
        if not path.exists():
            fail(f"required public-release file missing: {path.relative_to(ROOT)}")

    checks = pd.read_csv(ROOT / "results" / "validation" / "reconciliation_checks.csv")
    if "status" not in checks.columns:
        fail("reconciliation_checks.csv has no status column")
    bad = checks.loc[~checks["status"].astype("string").str.upper().eq("PASS")]
    if len(bad):
        fail(f"{len(bad)} frozen reconciliation checks are not PASS")

    headline = pd.read_csv(ROOT / "results" / "manuscript" / "headline_results.csv")
    if headline.empty:
        fail("headline_results.csv is empty")

    figures = pd.read_csv(ROOT / "results" / "figures" / "figure_index.csv")
    if "figure" not in figures.columns:
        fail("figure_index.csv has no figure column")
    expected_figures = {"Figure 1", "Figure 2", "Figure 3", "Figure 4", "Figure 5"}
    observed_figures = set(figures["figure"].dropna().astype(str))
    if observed_figures != expected_figures:
        fail(
            "figure index is not synchronized with the five main manuscript figures: "
            f"observed={sorted(observed_figures)}"
        )

    cpi_path = ROOT / "data" / "frozen" / "public" / "cpi_u_annual.csv"
    if sha256_file(cpi_path) != EXPECTED_CPI_SHA256:
        fail("bundled CPI-U table does not match the frozen release hash")

    behaviour_path = ROOT / "data" / "frozen" / "public" / "behaviour_parameters_public.csv"
    if sha256_file(behaviour_path) != EXPECTED_BEHAVIOUR_SHA256:
        fail("bundled behavioural parameter table does not match the frozen release hash")

    with (ROOT / "config" / "default.toml").open("rb") as handle:
        cfg = tomllib.load(handle)
    if int(cfg["uncertainty"]["bootstrap_draws"]) != 1000:
        fail("bootstrap draw count differs from the frozen 1,000-draw analysis")
    if int(cfg["uncertainty"]["implemented_structural_variants"]) != 12:
        fail("structural-variant count differs from the frozen 12-variant analysis")

    restricted_candidates = []
    for folder in [ROOT / "data" / "restricted", ROOT / "data" / "frozen" / "restricted"]:
        if folder.exists():
            restricted_candidates.extend(
                p for p in folder.rglob("*") if p.is_file() and p.name != ".gitkeep"
            )
    if restricted_candidates:
        fail("restricted respondent-level files are present in the public working tree")

    print("PASS: BioLand-US public release is internally synchronized.")
    print(f"  reconciliation checks: {len(checks)} PASS")
    print(f"  manuscript headline rows: {len(headline)}")
    print("  main figure index: Figures 1-5 present")
    print("  bundled CPI and behavioural parameters: hash verified")
    print("  restricted respondent files: absent")


if __name__ == "__main__":
    main()
