"""Validate the canonical behavioural exports before national modelling."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from bioland_us.validation import require_columns, require_unit_interval


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--parameters",
        type=Path,
        default=Path("data/frozen/restricted/behaviour_parameters.csv"),
    )
    parser.add_argument(
        "--bootstrap-input",
        type=Path,
        default=Path("data/frozen/restricted/behaviour_bootstrap_input.csv"),
    )
    args = parser.parse_args()

    parameters = pd.read_csv(args.parameters)
    bootstrap = pd.read_csv(args.bootstrap_input)

    require_columns(parameters, ["parameter", "value"], name="behaviour parameters")
    require_columns(
        bootstrap,
        [
            "id",
            "acc",
            "offer",
            "contract_years",
            "land_type",
            "experimental_feedstock",
            "share_central",
        ],
        name="behaviour bootstrap input",
    )
    require_unit_interval(bootstrap["acc"], name="acc")
    require_unit_interval(
        bootstrap["share_central"], name="share_central", allow_missing=True
    )

    if bootstrap["id"].isna().any():
        raise ValueError("Respondent id contains missing values.")

    print("PASS: canonical behavioural inputs validated.")
    print(f"  rows={len(bootstrap):,}")
    print(f"  respondents={bootstrap['id'].nunique():,}")
    print(f"  accepted={int(bootstrap['acc'].sum()):,}")


if __name__ == "__main__":
    main()
