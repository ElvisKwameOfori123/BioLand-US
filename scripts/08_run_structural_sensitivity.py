"""Run the implemented intensive-share × Census-land structural grid."""

from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path

import pandas as pd

from bioland_us.config import load_config
from bioland_us.mobilization import apply_capacity_constraint, national_summary
from bioland_us.validation import require_columns


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--access-base",
        type=Path,
        default=Path("data/frozen/public/behavioural_access.csv"),
    )
    parser.add_argument(
        "--land-dir",
        type=Path,
        default=Path("data/frozen/public/land_structures"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/structural/structural_sensitivity.csv"),
    )
    args = parser.parse_args()

    cfg = load_config()
    central_s = float(cfg["intensive"]["central_all_accept"])
    intensive = {
        "LOWER_DATA_QUALITY": float(cfg["intensive"]["lower_data_quality"]),
        "CENTRAL_PRIMARY": central_s,
        "CENTRAL_IPW_ROBUSTNESS": float(cfg["intensive"]["ipw_all_accept"]),
        "UPPER_DATA_QUALITY": float(cfg["intensive"]["upper_data_quality"]),
    }
    land_structures = ["JOINT_EQUAL", "JOINT_OWNED", "JOINT_RENTED"]

    access = pd.read_csv(args.access_base, dtype={"fips": "string"})
    require_columns(
        access,
        [
            "scenario_id",
            "allocation_family",
            "contract_years",
            "fips",
            "land_type",
            "A_P",
            "Q_P",
            "kappa",
        ],
        name="access base",
    )

    rows = []
    for (iname, s_value), land_name in product(intensive.items(), land_structures):
        land_path = args.land_dir / f"{land_name}.csv"
        if not land_path.exists():
            raise FileNotFoundError(land_path)
        land = pd.read_csv(land_path, dtype={"fips": "string"})

        x = access.copy()
        x["kappa"] = x["kappa"] * (s_value / central_s)
        x = x.merge(
            land[["fips", "land_type", "B"]],
            on=["fips", "land_type"],
            how="left",
            validate="m:1",
        )
        x["K"] = x["B"] * x["kappa"]
        constrained = apply_capacity_constraint(x)
        summary = national_summary(constrained)
        summary["intensive_representation"] = iname
        summary["land_structure"] = land_name
        rows.append(summary)

    out = pd.concat(rows, ignore_index=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(f"PASS: structural sensitivity written to {args.output}")


if __name__ == "__main__":
    main()
