"""Build map-ready county implementation-exposure outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from bioland_us.spatial import county_central_summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--deterministic",
        type=Path,
        default=Path("results/deterministic/county_land_mobilization.csv"),
    )
    parser.add_argument(
        "--bootstrap-county",
        type=Path,
        default=Path("results/bootstrap/county_bootstrap.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/spatial/county_spatial_robustness.csv"),
    )
    args = parser.parse_args()

    det = pd.read_csv(args.deterministic, dtype={"fips": "string"})
    central = county_central_summary(det)

    if args.bootstrap_county.exists():
        boot = pd.read_csv(args.bootstrap_county, dtype={"fips": "string"})
        central = central.merge(
            boot,
            on=["allocation_family", "scenario_id", "contract_years", "fips"],
            how="left",
            validate="1:1",
        )

    central["pressure_class"] = np.select(
        [
            central["rho"].lt(0.5),
            central["rho"].ge(0.5) & central["rho"].lt(1),
            central["rho"].ge(1) & central["rho"].lt(2),
            central["rho"].ge(2) & np.isfinite(central["rho"]),
            np.isinf(central["rho"]),
        ],
        ["lt_05", "c05_1", "c1_2", "ge_2", "undefined"],
        default="not_allocated",
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    central.to_csv(args.output, index=False)
    print(f"PASS: spatial output written to {args.output}")


if __name__ == "__main__":
    main()
