"""Orchestrate the clean public BioLand-US pipeline.

Behavioural estimation remains authoritative in Stata. This runner assumes the
canonical Stata exports already exist, then executes the national Python stages.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

STAGES = [
    "01_check_behaviour_exports.py",
    "05_build_behavioural_access.py",
    "06_run_mobilization.py",
    "08_run_structural_sensitivity.py",
    "09_build_spatial_outputs.py",
]


def main() -> None:
    scripts = Path(__file__).resolve().parent
    for stage in STAGES:
        command = [sys.executable, str(scripts / stage)]
        print("=" * 88)
        print("RUNNING", stage)
        print("=" * 88)
        subprocess.run(command, check=True)

    print("=" * 88)
    print("BIOLAND-US CLEAN PUBLIC PIPELINE COMPLETE")
    print("=" * 88)


if __name__ == "__main__":
    main()
