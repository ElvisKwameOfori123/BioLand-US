"""Run the BioLand-US national pipeline in order.

    python scripts/00_run_core.py                 public model from committed derived tables
    python scripts/00_run_core.py --from-raw      also rebuild 02-04 from data/raw
    python scripts/00_run_core.py --restricted    also validate Study-A exports and run
                                                  the paired bootstrap (needs the Stata
                                                  outputs in data/frozen/restricted)

Run stata/00_run_behaviour.do first whenever the behavioural estimates change.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PREPARE = ["02_prepare_polysys.py", "03_prepare_land.py", "04_prepare_rents.py"]
MODEL = ["05_build_behavioural_access.py", "06_run_mobilization.py", "08_run_structural_sensitivity.py",
         "10_transport_robustness.py"]
RESTRICTED = ["01_validate_behaviour.py", "07_run_bootstrap.py"]
SPATIAL = ["09_build_spatial_outputs.py", "11_build_manuscript_tables.py", "12_make_figures.py"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-raw", action="store_true", help="rebuild POLYSYS, land and rents from data/raw")
    parser.add_argument("--restricted", action="store_true", help="validate Study-A exports and run the bootstrap")
    args = parser.parse_args()

    stages = (PREPARE if args.from_raw else []) + MODEL + (RESTRICTED if args.restricted else []) + SPATIAL
    scripts = Path(__file__).resolve().parent
    for stage in stages:
        print("=" * 88, f"\nRUNNING {stage}\n" + "=" * 88, flush=True)
        subprocess.run([sys.executable, str(scripts / stage)], check=True)
    print("=" * 88, "\nBIOLAND-US PIPELINE COMPLETE\n" + "=" * 88)


if __name__ == "__main__":
    main()
