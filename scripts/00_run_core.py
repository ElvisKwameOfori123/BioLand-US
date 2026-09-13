"""Run the clean deterministic BioLand-US core.

Public-source preparation is kept in scripts 02-04 because those stages require
explicit source-file arguments. This runner assumes canonical inputs already exist.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

STAGES = [
    "01_validate_behaviour.py",
    "05_build_behavioural_access.py",
    "06_run_mobilization.py",
]


def main() -> None:
    scripts = Path(__file__).resolve().parent
    for stage in STAGES:
        path = scripts / stage
        if not path.exists():
            raise FileNotFoundError(path)
        print("=" * 88)
        print(f"RUNNING {stage}")
        print("=" * 88)
        subprocess.run([sys.executable, str(path)], check=True)

    print("=" * 88)
    print("BIOLAND-US DETERMINISTIC CORE COMPLETE")
    print("Run scripts 07-10 explicitly for uncertainty, robustness and figures.")
    print("=" * 88)


if __name__ == "__main__":
    main()
