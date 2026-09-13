"""Build map-ready county spatial robustness outputs.

The headline spatial case is the support-balanced rent-indexed reference.
Statistical metrics from the paired bootstrap are kept distinct from structural
ranges across the implemented intensive × land-completion variants.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from bioland_us.spatial import county_central_summary


def add_top10_flag(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["top10_struct"] = 0
    for _, index in out.groupby(
        ["allocation_family", "contract_years", "behaviour_representation", "landbase_structure"],
        dropna=False,
    ).groups.items():
        idx = list(index)
        valid = out.loc[idx, "rho"].notna()
        ranked = out.loc[np.array(idx)[valid.to_numpy()]].sort_values(
            "rho",
            ascending=False,
        )
        n_top = max(1, int(np.ceil(0.10 * len(ranked)))) if len(ranked) else 0
        out.loc[ranked.head(n_top).index, "top10_struct"] = 1
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--structural-county-land",
        type=Path,
        default=Path("results/structural/county_land_structural_variants.csv"),
    )
    parser.add_argument(
        "--bootstrap-county",
        type=Path,
        default=Path("results/bootstrap/support_balanced_county_bootstrap.csv"),
    )
    parser.add_argument(
        "--scenario-id",
        default="SUPPORT_BALANCED_REFERENCE",
        help="Support-balanced scenario id in the deterministic clean pipeline.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/spatial/county_spatial_robustness.csv"),
    )
    parser.add_argument(
        "--output-rank",
        type=Path,
        default=Path("results/spatial/rank_stability.csv"),
    )
    args = parser.parse_args()

    variants = pd.read_csv(
        args.structural_county_land,
        dtype={"fips": "string"},
        low_memory=False,
    )
    require = {
        "scenario_id",
        "allocation_family",
        "contract_years",
        "fips",
        "behaviour_representation",
        "landbase_structure",
    }
    missing = sorted(require - set(variants.columns))
    if missing:
        raise ValueError(f"structural county-land output missing columns: {missing}")

    variants = variants.loc[variants["scenario_id"].eq(args.scenario_id)].copy()
    if variants.empty:
        # The bootstrap uses the descriptive frozen name, while the deterministic
        # clean script may use the numeric identifier. Accept the descriptive name
        # if it is present.
        descriptive = "SUPPORT_BALANCED_REFERENCE"
        variants = pd.read_csv(
            args.structural_county_land,
            dtype={"fips": "string"},
            low_memory=False,
        )
        variants = variants.loc[variants["scenario_id"].eq(descriptive)].copy()

    if variants.empty:
        raise ValueError("Support-balanced structural variants were not found.")

    county_parts = []
    group_cols = ["behaviour_representation", "landbase_structure"]
    for key, group in variants.groupby(group_cols, dropna=False):
        county = county_central_summary(group)
        county["behaviour_representation"] = key[0]
        county["landbase_structure"] = key[1]
        county_parts.append(county)

    counties = pd.concat(county_parts, ignore_index=True)
    counties = add_top10_flag(counties)

    central = counties.loc[
        counties["behaviour_representation"].eq("CENTRAL_PRIMARY")
        & counties["landbase_structure"].eq("JOINT_EQUAL")
    ].copy()
    central = central.rename(
        columns={
            "rho": "rho_central",
            "M_Q_full_lower": "M_Q_central",
            "unmet_Q_full_upper": "unmet_Q_central",
            "binding": "binding_central",
        }
    )

    keys = ["allocation_family", "contract_years", "fips"]
    structural = (
        counties.groupby(keys, dropna=False)
        .agg(
            rho_struct_min=("rho", "min"),
            rho_struct_max=("rho", "max"),
            M_Q_struct_min=("M_Q_full_lower", "min"),
            M_Q_struct_max=("M_Q_full_upper", "max"),
            unmet_Q_struct_min=("unmet_Q_full_lower", "min"),
            unmet_Q_struct_max=("unmet_Q_full_upper", "max"),
            F_top10_struct=("top10_struct", "mean"),
        )
        .reset_index()
    )
    structural["D_MQ_noninstitutional"] = (
        structural["M_Q_struct_max"] - structural["M_Q_struct_min"]
    )

    keep = [
        "allocation_family",
        "contract_years",
        "fips",
        "A_P",
        "Q_P",
        "K",
        "rho_central",
        "M_Q_central",
        "unmet_Q_central",
        "binding_central",
    ]
    central = central[[c for c in keep if c in central.columns]]
    out = structural.merge(central, on=keys, how="left", validate="1:1")

    if args.bootstrap_county.exists():
        boot = pd.read_csv(args.bootstrap_county, dtype={"fips": "string"})
        out = out.merge(
            boot[
                [
                    "allocation_family",
                    "contract_years",
                    "fips",
                    "valid_draws",
                    "P_bind",
                    "P_top10_risk",
                ]
            ],
            on=keys,
            how="left",
            validate="1:1",
        )

    out["pressure_class"] = np.select(
        [
            out["rho_central"].lt(0.5),
            out["rho_central"].ge(0.5) & out["rho_central"].lt(1),
            out["rho_central"].ge(1) & out["rho_central"].lt(2),
            out["rho_central"].ge(2) & np.isfinite(out["rho_central"]),
            np.isinf(out["rho_central"]),
        ],
        ["lt_05", "c05_1", "c1_2", "ge_2", "undefined"],
        default="not_allocated",
    )

    out["robust_top10_flag"] = (
        out.get("P_top10_risk", pd.Series(np.nan, index=out.index)).ge(0.8)
        & out["F_top10_struct"].ge(0.75)
    )
    out["statistically_unstable_top10_flag"] = (
        out.get("P_top10_risk", pd.Series(np.nan, index=out.index))
        .between(0.2, 0.8, inclusive="neither")
    )
    out["structurally_unstable_top10_flag"] = out["F_top10_struct"].lt(0.75)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)

    rank_cols = [
        "allocation_family",
        "contract_years",
        "fips",
        "rho_central",
        "P_bind",
        "P_top10_risk",
        "F_top10_struct",
        "D_MQ_noninstitutional",
        "robust_top10_flag",
        "statistically_unstable_top10_flag",
        "structurally_unstable_top10_flag",
    ]
    out[[c for c in rank_cols if c in out.columns]].to_csv(
        args.output_rank,
        index=False,
    )

    print("PASS: support-balanced county spatial robustness complete.")
    print(f"  map-ready={args.output}")
    print(f"  rank stability={args.output_rank}")


if __name__ == "__main__":
    main()
