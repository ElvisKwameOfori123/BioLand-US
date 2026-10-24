"""Fail-fast check of the public BioLand-US release.

    python scripts/00_verify_release.py              file, ledger and privacy checks
    python scripts/00_verify_release.py --recompute  also rerun 05 and 06 from the
                                                     committed tables and compare
                                                     with the committed national results

Restricted Study-A files may exist locally; the check is that none is tracked by git.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "data/source_registry.csv",
    "data/frozen/public/behaviour_parameters_public.csv",
    "data/frozen/public/cpi_u_annual.csv",
    "data/frozen/public/polysys_allocation.csv",
    "data/frozen/public/compatible_land.csv",
    "data/frozen/public/rent_context.csv",
    "results/deterministic/national_mobilization.csv",
    "results/manuscript/headline_results.csv",
    "results/validation/reconciliation_checks.csv",
]
RESTRICTED_MARKERS = ("data/restricted/", "data/frozen/restricted/", "results/restricted/")


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recompute", action="store_true")
    args = parser.parse_args()

    for rel in REQUIRED:
        if not (ROOT / rel).exists():
            fail(f"required file missing: {rel}")

    ledger = pd.read_csv(ROOT / "results/validation/reconciliation_checks.csv")
    if ledger["status"].ne("PASS").any():
        fail(f"{int(ledger['status'].ne('PASS').sum())} reconciliation checks are not PASS")

    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    leaked = [f for f in tracked.splitlines()
              if f.startswith(RESTRICTED_MARKERS) and not f.endswith(".gitkeep")]
    if leaked:
        fail(f"restricted files are tracked by git: {leaked[:5]}")

    if args.recompute:
        with tempfile.TemporaryDirectory() as tmp:
            access = Path(tmp) / "access.csv"
            summary = Path(tmp) / "national.csv"
            run = [sys.executable, "-u"]
            subprocess.run([*run, "scripts/05_build_behavioural_access.py", "--output", str(access),
                            "--output-scenarios", str(Path(tmp) / "scen.csv")], cwd=ROOT, check=True)
            subprocess.run([*run, "scripts/06_run_mobilization.py", "--access", str(access),
                            "--output-detail", str(Path(tmp) / "detail.csv"), "--output-summary", str(summary)],
                           cwd=ROOT, check=True)
            new = pd.read_csv(summary)
            old = pd.read_csv(ROOT / "results/deterministic/national_mobilization.csv")
            keys = ["track", "scenario_id", "contract_years", "allocation_family"]
            both = old.merge(new, on=keys, suffixes=("_old", "_new"), validate="1:1")
            if len(both) != len(old) or not np.allclose(both["M_Q_full_lower_old"], both["M_Q_full_lower_new"],
                                                        rtol=0, atol=1e-10):
                fail("recomputed national mobilization differs from the committed results")
        print("  recompute: 05 -> 06 reproduces the committed national results")

    print(f"PASS: release synchronized ({len(ledger)} reconciliation checks PASS, no restricted files tracked).")


if __name__ == "__main__":
    main()
