"""Structural sensitivity, kept separate from bootstrap (statistical) uncertainty.

Implemented structural variants (config uncertainty.implemented_structural_variants)
    PER_CHOICE behaviour x 4 intensive representations x 2 Census surfaces
    ACRE_WEIGHTED behaviour (CENTRAL_PRIMARY s) x 2 Census surfaces

Contract duration, compensation scenario and the three allocation families are
scenario dimensions and are not collapsed into the range.

Two different things are reported separately (they were previously mixed):
    structural range   min / max across variants of the full-denominator LOWER
                       bound (and separately of the UPPER bound)
    coverage gap       upper - lower within a variant, caused only by
                       unresolved rent / land cells

T2-T4 institutional alternatives remain unquantified (institutional ledger).

Outputs (results/structural/)
    national_structural_variants.csv     every variant
    national_structural_sensitivity.csv  ranges per scenario
    county_land_structural_variants.csv  support-balanced pools for 09
    feedstock_transfer_coverage.csv
    institutional_readiness.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from bioland_us.behaviour import INTENSIVE_REPRESENTATIONS, conditional_share, load_public_parameters
from bioland_us.config import load_config
from bioland_us.mobilization import apply_capacity_constraint, national_summary
from bioland_us.validation import require_columns

INSTITUTIONAL_LEDGER = [
    ("T1_POOLED_BEHAVIOURAL_TRANSMISSION", "IMPLEMENTED_CORE", True,
     "Explicit reference transmission used in the core model."),
    ("T2_ROLE_DIFFERENTIATED_TRANSMISSION", "DEFERRED_REQUIRES_NATIONAL_ROLE_WEIGHTS", False,
     "No defensible national bridge between prior agricultural lessor experience and parcel-level role weights."),
    ("T3_PROPORTIONAL_OVERLAP_REPRESENTATION", "DEFERRED_REQUIRES_FORMULA_FREEZE", False,
     "No empirically identified national overlap parameter is frozen."),
    ("T4_OPTIMISTIC_OWNER_AVAILABILITY_BENCHMARK", "DEFERRED_REQUIRES_FORMULA_FREEZE", False,
     "Operator-owned acreage cannot be read as universal landlord availability without more evidence."),
]


def variants(params: dict, structures: list[str]):
    for rep in INTENSIVE_REPRESENTATIONS:
        for land in structures:
            yield "PER_CHOICE", rep, land, conditional_share(params, rep, "PER_CHOICE")
    for land in structures:
        yield "ACRE_WEIGHTED", "CENTRAL_PRIMARY", land, conditional_share(params, "CENTRAL_PRIMARY", "ACRE_WEIGHTED")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--access", type=Path, default=Path("data/frozen/public/behavioural_access.csv"))
    parser.add_argument("--resource", type=Path, default=Path("data/frozen/public/polysys_allocation.csv"))
    parser.add_argument("--land-dir", type=Path, default=Path("data/frozen/public/land_structures"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/structural"))
    args = parser.parse_args()

    cfg = load_config()
    params = load_public_parameters()
    structures = cfg["land"]["structures"]
    central_land = cfg["land"]["central_structure"]
    spatial_scenario = "SUPPORT_BALANCED_REFERENCE"

    access = pd.read_csv(args.access, dtype={"fips": "string"})
    require_columns(access, ["behaviour_weighting", "scenario_id", "allocation_family", "contract_years",
                             "fips", "land_type", "A_P", "Q_P", "p_pool"], name="behavioural access")
    lands = {
        name: pd.read_csv(args.land_dir / f"{name}.csv", dtype={"fips": "string"})[["fips", "land_type", "B"]]
        for name in structures
    }

    national, county_land = [], []
    n_variants = 0
    for weighting, rep, land_name, s in variants(params, structures):
        n_variants += 1
        x = access.loc[access["behaviour_weighting"].eq(weighting)].copy()
        x["kappa"] = s * x["p_pool"]
        x = x.merge(lands[land_name], on=["fips", "land_type"], how="left", validate="m:1")
        x["K"] = x["B"] * x["kappa"]
        x["behaviour_representation"] = rep
        x["landbase_structure"] = land_name
        constrained = apply_capacity_constraint(x)
        national.append(national_summary(constrained))
        county_land.append(constrained.loc[constrained["scenario_id"].eq(spatial_scenario)])

    if n_variants != int(cfg["uncertainty"]["implemented_structural_variants"]):
        raise AssertionError(f"Implemented {n_variants} structural variants; config expects a different count.")

    national = pd.concat(national, ignore_index=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    national.to_csv(args.output_dir / "national_structural_variants.csv", index=False)
    pd.concat(county_land, ignore_index=True).to_csv(
        args.output_dir / "county_land_structural_variants.csv", index=False)

    is_central = (national["behaviour_weighting"].eq("PER_CHOICE")
                  & national["behaviour_representation"].eq("CENTRAL_PRIMARY")
                  & national["landbase_structure"].eq(central_land))
    keys = ["track", "scenario_id", "rent_multiplier", "allocation_family", "contract_years"]
    ranges = (
        national.assign(coverage_gap=national["M_Q_full_upper"] - national["M_Q_full_lower"])
        .groupby(keys, dropna=False)
        .agg(variants=("M_Q_full_lower", "size"),
             M_Q_lower_struct_min=("M_Q_full_lower", "min"),
             M_Q_lower_struct_max=("M_Q_full_lower", "max"),
             M_Q_upper_struct_min=("M_Q_full_upper", "min"),
             M_Q_upper_struct_max=("M_Q_full_upper", "max"),
             max_coverage_gap=("coverage_gap", "max"))
        .reset_index()
        .merge(national.loc[is_central, keys + ["M_Q_full_lower"]].rename(
            columns={"M_Q_full_lower": "M_Q_central_lower"}), on=keys, how="left", validate="1:1")
    )
    ranges["M_Q_struct_range"] = ranges["M_Q_lower_struct_max"] - ranges["M_Q_lower_struct_min"]
    ranges.to_csv(args.output_dir / "national_structural_sensitivity.csv", index=False)

    resource = pd.read_csv(args.resource)
    coverage = (
        resource.assign(A_direct=resource["A_P"].where(resource["directly_tested_species"], 0.0),
                        Q_direct=resource["Q_P"].where(resource["directly_tested_species"], 0.0))
        .groupby("allocation_family")[["A_P", "Q_P", "A_direct", "Q_direct"]].sum()
    )
    coverage = pd.DataFrame({
        "tested_species_harvest_share": coverage["A_direct"] / coverage["A_P"],
        "tested_species_production_share": coverage["Q_direct"] / coverage["Q_P"],
    }).reset_index()
    coverage["interpretation"] = ("Share of the POLYSYS allocation directly represented by species tested "
                                  "in Study A; untested species are transferred, not set to zero.")
    coverage.to_csv(args.output_dir / "feedstock_transfer_coverage.csv", index=False)

    pd.DataFrame(INSTITUTIONAL_LEDGER, columns=["transmission_id", "status", "quantitative", "reason"]).to_csv(
        args.output_dir / "institutional_readiness.csv", index=False)

    print(f"PASS: {n_variants} structural variants; statistical uncertainty not mixed in.")
    show = ranges.loc[ranges["scenario_id"].isin(["EXP_ABS_100", spatial_scenario]) & ranges["contract_years"].eq(5)]
    print(show[["scenario_id", "allocation_family", "M_Q_central_lower", "M_Q_lower_struct_min",
                "M_Q_lower_struct_max", "max_coverage_gap"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
