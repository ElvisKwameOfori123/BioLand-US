"""Run the deterministic public BioLand-US national core.

The public default uses the frozen, non-disclosive behavioural parameters in
``config/default.toml``. It therefore does not require respondent-level KBS
records merely to reproduce the deterministic national transport and
mobilization calculation.

Public-source preparation remains explicit because the large third-party files
are retrieved from their authoritative providers. Use ``00_fetch_public_sources.py``
and the documented preparation stages first.

Behavioural re-estimation/validation from Study-A respondent records is a
separate restricted-data stage and can be requested with
``--validate-restricted-behaviour``.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PUBLIC_STAGES = [
    "05_build_behavioural_access.py",
    "06_run_mobilization.py",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--validate-restricted-behaviour",
        action="store_true",
        help=(
            "Run 01_validate_behaviour.py first. This requires authorized local "
            "respondent-derived behavioural inputs and is not needed for the "
            "public deterministic national rerun."
        ),
    )
    args = parser.parse_args()

    stages = list(PUBLIC_STAGES)
    if args.validate_restricted_behaviour:
        stages.insert(0, "01_validate_behaviour.py")

    scripts = Path(__file__).resolve().parent
    for stage in stages:
        path = scripts / stage
        if not path.exists():
            raise FileNotFoundError(path)
        print("=" * 88)
        print(f"RUNNING {stage}")
        print("=" * 88)
        subprocess.run([sys.executable, str(path)], check=True)

    print("=" * 88)
    print("BIOLAND-US DETERMINISTIC PUBLIC CORE COMPLETE")
    print("Run scripts 07-12 explicitly for uncertainty and robustness stages.")
    print("=" * 88)


if __name__ == "__main__":
    main()
