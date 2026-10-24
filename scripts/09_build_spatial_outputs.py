"""Map-ready county robustness for the support-balanced rent-indexed reference.

County pressure comes from bioland_us.spatial (a county binds if any of its land
pools binds; rho is its most constrained pool). Three kinds of evidence stay apart:
    central        PER_CHOICE x CENTRAL_PRIMARY x FARMLAND (deterministic)
    structural     range and top-decile frequency across the 08 variants
    statistical    P_bind and P_top10_risk from the 07 paired bootstrap

Outputs (results/spatial/)
    county_spatial_robustness.csv   one row per family x duration x county
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from bioland_us.config import load_config
from bioland_us.spatial import county_central_summary

VARIANT = ["behaviour_weighting", "behaviour_representation", "landbase_structure"]
KEYS = ["allocation_family", "contract_years", "fips"]


def top_decile(counties: pd.DataFrame, by: list[str]) -> pd.Series:
    valid = counties["rho"].notna()
    rank = counties.loc[valid].groupby(by)["rho"].rank(ascending=False, method="first")
    size = counties.loc[valid].groupby(by)["rho"].transform("size")
    flag = pd.Series(0, index=counties.index)
    flag.loc[valid] = (rank <= np.ceil(0.10 * size)).astype(int)
    return flag


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variants", type=Path, default=Path("results/structural/county_land_structural_variants.csv"))
    parser.add_argument("--bootstrap", type=Path, default=Path("results/bootstrap/support_balanced_county_bootstrap.csv"))
    parser.add_argument("--output", type=Path, default=Path("results/spatial/county_spatial_robustness.csv"))
    args = parser.parse_args()

    cfg = load_config()
    pools = pd.read_csv(args.variants, dtype={"fips": "string"}, low_memory=False)
    counties = county_central_summary(pools, keys=[*VARIANT, *KEYS])
    counties["top10"] = top_decile(counties, [*VARIANT, "allocation_family", "contract_years"])

    central = counties.loc[
        counties["behaviour_weighting"].eq("PER_CHOICE")
        & counties["behaviour_representation"].eq("CENTRAL_PRIMARY")
        & counties["landbase_structure"].eq(cfg["land"]["central_structure"])
    ]
    out = central[[*KEYS, "A_P", "Q_P", "K", "rho", "binding", "M_Q_full_lower", "unmet_Q_full_upper", "top10"]].rename(
        columns={"rho": "rho_central", "binding": "binding_central", "M_Q_full_lower": "M_Q_central",
                 "unmet_Q_full_upper": "unmet_Q_central", "top10": "top10_central"})

    structural = counties.groupby(KEYS).agg(
        rho_struct_min=("rho", "min"), rho_struct_max=("rho", "max"),
        M_Q_struct_min=("M_Q_full_lower", "min"), M_Q_struct_max=("M_Q_full_lower", "max"),
        F_bind_struct=("binding", "mean"), F_top10_struct=("top10", "mean"),
    ).reset_index()
    structural["D_MQ_structural"] = structural["M_Q_struct_max"] - structural["M_Q_struct_min"]
    out = out.merge(structural, on=KEYS, how="left", validate="1:1")

    if args.bootstrap.exists():
        boot = pd.read_csv(args.bootstrap, dtype={"fips": "string"})
        out = out.merge(boot, on=KEYS, how="left", validate="1:1")
    else:
        print(f"NOTE: {args.bootstrap} not found; statistical columns omitted.")

    out["pressure_class"] = np.select(
        [out["rho_central"].isna() & out["A_P"].gt(0), np.isinf(out["rho_central"]), out["rho_central"].ge(2),
         out["rho_central"].ge(1), out["rho_central"].ge(0.5), out["rho_central"].ge(0)],
        ["unresolved", "zero_capacity", "ge_2", "c1_2", "c05_1", "lt_05"], default="no_allocation")
    if "P_top10_risk" in out:
        out["robust_top10_flag"] = out["top10_central"].eq(1) & out["P_top10_risk"].ge(0.8) & out["F_top10_struct"].ge(0.75)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)

    fam = out.loc[out["allocation_family"].eq("FAMILY_01") & out["contract_years"].eq(5)]
    print(f"PASS: {len(out):,} county rows. FAMILY_01, 5-year: {int(fam['binding_central'].eq(1).sum())} binding counties")
    print(fam["pressure_class"].value_counts().to_string())


if __name__ == "__main__":
    main()
