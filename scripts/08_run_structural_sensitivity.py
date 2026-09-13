"""Run implemented structural sensitivity while keeping it separate from bootstrap uncertainty.

Implemented structural dimensions
--------------------------------
- four frozen intensive representations;
- three Census completion structures: JOINT_EQUAL, JOINT_OWNED, JOINT_RENTED.

Contract duration, compensation scenario and the three independent POLYSYS
allocation families are retained as scenario dimensions, not collapsed into a
single uncertainty interval.

T2-T4 institutional alternatives remain unquantified.
"""

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
        "--resource",
        type=Path,
        default=Path("data/frozen/public/polysys_allocation.csv"),
    )
    parser.add_argument(
        "--land-dir",
        type=Path,
        default=Path("data/frozen/public/land_structures"),
    )
    parser.add_argument(
        "--output-national",
        type=Path,
        default=Path("results/structural/national_structural_sensitivity.csv"),
    )
    parser.add_argument(
        "--output-county-land",
        type=Path,
        default=Path("results/structural/county_land_structural_variants.csv"),
    )
    parser.add_argument(
        "--output-feedstock-coverage",
        type=Path,
        default=Path("results/structural/feedstock_transfer_coverage.csv"),
    )
    parser.add_argument(
        "--output-institutional-ledger",
        type=Path,
        default=Path("results/structural/institutional_readiness.csv"),
    )
    args = parser.parse_args()

    cfg = load_config()
    central_s = float(cfg["intensive"]["central_all_accept"])
    intensive = {
        "LOWER_DATA_QUALITY": float(cfg["intensive"]["lower_data_quality"]),
        "CENTRAL_IPW_ROBUSTNESS": float(cfg["intensive"]["ipw_all_accept"]),
        "CENTRAL_PRIMARY": central_s,
        "UPPER_DATA_QUALITY": float(cfg["intensive"]["upper_data_quality"]),
    }
    land_structures = ["JOINT_EQUAL", "JOINT_OWNED", "JOINT_RENTED"]

    access = pd.read_csv(args.access_base, dtype={"fips": "string"})
    require_columns(
        access,
        [
            "track",
            "scenario_id",
            "allocation_family",
            "contract_years",
            "fips",
            "land_type",
            "A_P",
            "Q_P",
            "kappa",
        ],
        name="behavioural access",
    )

    national_rows = []
    county_land_rows = []

    for (representation, s_value), land_name in product(
        intensive.items(),
        land_structures,
    ):
        land_path = args.land_dir / f"{land_name}.csv"
        if not land_path.exists():
            raise FileNotFoundError(
                f"{land_path} is required for structural sensitivity."
            )

        land = pd.read_csv(land_path, dtype={"fips": "string"})
        require_columns(land, ["fips", "land_type", "B"], name=land_name)

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
        constrained["behaviour_representation"] = representation
        constrained["landbase_structure"] = land_name
        county_land_rows.append(constrained)

        summary = national_summary(constrained)
        summary["behaviour_representation"] = representation
        summary["landbase_structure"] = land_name
        national_rows.append(summary)

    county_land = pd.concat(county_land_rows, ignore_index=True)
    national = pd.concat(national_rows, ignore_index=True)

    args.output_county_land.parent.mkdir(parents=True, exist_ok=True)
    county_land.to_csv(args.output_county_land, index=False)

    grouping = [
        "scenario_id",
        "allocation_family",
        "contract_years",
    ]
    rows = []
    for key, group in national.groupby(grouping, dropna=False):
        record = dict(zip(grouping, key))
        q_lower = pd.to_numeric(group["M_Q_full_lower"], errors="coerce")
        q_upper = pd.to_numeric(group["M_Q_full_upper"], errors="coerce")
        a_lower = pd.to_numeric(group["M_A_full_lower"], errors="coerce")
        a_upper = pd.to_numeric(group["M_A_full_upper"], errors="coerce")

        central = group.loc[
            group["behaviour_representation"].eq("CENTRAL_PRIMARY")
            & group["landbase_structure"].eq("JOINT_EQUAL")
        ]

        record.update(
            {
                "implemented_structural_variants": len(group),
                "M_Q_struct_min": float(q_lower.min()),
                "M_Q_struct_max": float(q_upper.max()),
                "M_Q_struct_range": float(q_upper.max() - q_lower.min()),
                "M_A_struct_min": float(a_lower.min()),
                "M_A_struct_max": float(a_upper.max()),
                "M_A_struct_range": float(a_upper.max() - a_lower.min()),
                "M_Q_central": (
                    float(central["M_Q_full_lower"].iloc[0])
                    if len(central) == 1
                    else float("nan")
                ),
                "dimensions_in_range": (
                    "intensive representation × Census completion structure"
                ),
            }
        )
        rows.append(record)

    pd.DataFrame(rows).to_csv(args.output_national, index=False)

    resource = pd.read_csv(args.resource)
    require_columns(
        resource,
        [
            "allocation_family",
            "feedstock",
            "A_P",
            "Q_P",
            "transfer_status",
        ],
        name="POLYSYS resource",
    )
    resource["directly_tested_species"] = resource["transfer_status"].eq(
        "DIRECT_EXPERIMENTAL_SPECIES"
    )

    coverage_rows = []
    for family, group in resource.groupby("allocation_family"):
        a_total = float(group["A_P"].sum())
        q_total = float(group["Q_P"].sum())
        direct = group["directly_tested_species"]
        coverage_rows.append(
            {
                "allocation_family": family,
                "tested_species_harvest_share": (
                    float(group.loc[direct, "A_P"].sum()) / a_total if a_total else float("nan")
                ),
                "tested_species_production_share": (
                    float(group.loc[direct, "Q_P"].sum()) / q_total if q_total else float("nan")
                ),
                "interpretation": (
                    "Share of the POLYSYS allocation directly represented by species "
                    "tested in Study A; untested species are not assigned zero."
                ),
            }
        )
    pd.DataFrame(coverage_rows).to_csv(
        args.output_feedstock_coverage,
        index=False,
    )

    ledger = pd.DataFrame(
        [
            {
                "transmission_id": "T1_POOLED_BEHAVIOURAL_TRANSMISSION",
                "status": "IMPLEMENTED_CORE",
                "quantitative": True,
                "reason": "Explicit reference transmission used in the core model.",
            },
            {
                "transmission_id": "T2_ROLE_DIFFERENTIATED_TRANSMISSION",
                "status": "DEFERRED_REQUIRES_NATIONAL_ROLE_WEIGHTS",
                "quantitative": False,
                "reason": (
                    "No defensible national bridge has been frozen between prior "
                    "agricultural lessor experience and parcel-level role weights."
                ),
            },
            {
                "transmission_id": "T3_PROPORTIONAL_OVERLAP_REPRESENTATION",
                "status": "DEFERRED_REQUIRES_FORMULA_FREEZE",
                "quantitative": False,
                "reason": "No empirically identified national overlap parameter is frozen.",
            },
            {
                "transmission_id": "T4_OPTIMISTIC_OWNER_AVAILABILITY_BENCHMARK",
                "status": "DEFERRED_REQUIRES_FORMULA_FREEZE",
                "quantitative": False,
                "reason": (
                    "Operator-owned acreage cannot be interpreted as universal "
                    "landlord availability without additional evidence."
                ),
            },
        ]
    )
    ledger.to_csv(args.output_institutional_ledger, index=False)

    print("PASS: implemented structural sensitivity complete.")
    print("Statistical uncertainty was not mixed into the structural range.")
    print(f"  national={args.output_national}")
    print(f"  county-land={args.output_county_land}")


if __name__ == "__main__":
    main()
