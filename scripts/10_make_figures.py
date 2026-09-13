"""Generate manuscript figures from the frozen reporting workbook."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--plot-script",
        type=Path,
        default=Path("scripts/plot_main_figures.py"),
    )
    args = parser.parse_args()

    if not args.plot_script.exists():
        raise FileNotFoundError(
            f"{args.plot_script} not found. Add the frozen publication plotting "
            "script as scripts/plot_main_figures.py."
        )

    subprocess.run([sys.executable, str(args.plot_script)], check=True)


if __name__ == "__main__":
    main()
