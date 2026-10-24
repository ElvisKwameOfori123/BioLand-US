"""Assemble manuscript tables and the reconciliation ledger from pipeline outputs.

Reads only results produced by 05-10; estimates nothing.

Outputs
    results/manuscript/headline_results.csv       family-balanced M_Q with every
                                                  uncertainty layer side by side
    results/manuscript/regional_mobilization.csv  by state, and national without
                                                  TX, OK and NM (concentration check)
    results/manuscript/county_binding_summary.csv
    results/manuscript/feedstock_coverage.csv
    results/manuscript/payable_rent_by_feedstock.csv  payable land rent vs local rent (E01)
    results/validation/reconciliation_checks.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from bioland_us.config import load_config

SOUTHERN_PLAINS = {"48", "40", "35"}  # TX, OK, NM


def balanced(frame: pd.DataFrame, keys: list[str], value: str) -> pd.DataFrame:
    x = frame.loc[frame["allocation_family"].ne("FAMILY_BALANCED")]
    return x.groupby(keys, dropna=False, as_index=False)[value].mean()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=Path("results"))
    args = parser.parse_args()
    R = args.results
    cfg = load_config()
    central_land = cfg["land"]["central_structure"]
    keys = ["track", "scenario_id", "contract_years"]
    checks = []

    def check(name, ok, value=""):
        checks.append({"check": name, "status": "PASS" if bool(ok) else "FAIL", "value": value})

    # ---- headline -----------------------------------------------------------
    det = pd.read_csv(R / "deterministic/national_mobilization.csv")
    fb = det.loc[det["allocation_family"].eq("FAMILY_BALANCED"), keys + ["M_Q_full_lower", "M_Q_full_upper"]]
    head = fb.rename(columns={"M_Q_full_lower": "M_Q_central", "M_Q_full_upper": "M_Q_central_coverage_upper"})

    var = pd.read_csv(R / "structural/national_structural_variants.csv")
    vkeys = keys + ["behaviour_weighting", "behaviour_representation", "landbase_structure"]
    vb = balanced(var, vkeys, "M_Q_full_lower")
    struct = vb.groupby(keys, as_index=False)["M_Q_full_lower"].agg(M_Q_struct_min="min", M_Q_struct_max="max")
    acre = vb.loc[vb["behaviour_weighting"].eq("ACRE_WEIGHTED") & vb["landbase_structure"].eq(central_land),
                  keys + ["M_Q_full_lower"]].rename(columns={"M_Q_full_lower": "M_Q_acre_weighted"})
    equal = vb.loc[vb["behaviour_weighting"].eq("PER_CHOICE") & vb["behaviour_representation"].eq("CENTRAL_PRIMARY")
                   & vb["landbase_structure"].eq("EQUAL"), keys + ["M_Q_full_lower"]].rename(
        columns={"M_Q_full_lower": "M_Q_equal_land"})
    head = head.merge(struct, on=keys, how="left").merge(acre, on=keys, how="left").merge(equal, on=keys, how="left")

    boot_path = R / "bootstrap/national_bootstrap_summary.csv"
    if boot_path.exists():
        boot = pd.read_csv(boot_path)
        boot = boot.loc[boot["allocation_family"].eq("FAMILY_BALANCED"), keys + ["M_Q_lower_p025", "M_Q_lower_p975", "draws"]]
        head = head.merge(boot.rename(columns={"M_Q_lower_p025": "M_Q_boot_p025", "M_Q_lower_p975": "M_Q_boot_p975",
                                               "draws": "bootstrap_draws"}), on=keys, how="left")
        check("bootstrap draws equal config", boot["draws"].eq(cfg["uncertainty"]["bootstrap_draws"]).all(),
              int(boot["draws"].iloc[0]))

    rob = pd.read_csv(R / "robustness/transport_national.csv")
    rob = rob.loc[rob["allocation_family"].eq("FAMILY_BALANCED")].pivot_table(
        index=["scenario_id", "contract_years"], columns="transport_spec", values="M_Q_full_lower").reset_index()
    rob = rob.rename(columns={"RATIO_ONLY": "M_Q_ratio_only", "OFFER_PLUS_RENT": "M_Q_offer_plus_rent"})
    bnd = pd.read_csv(R / "robustness/support_bounds_national.csv")
    bnd = bnd.loc[bnd["allocation_family"].eq("FAMILY_BALANCED")].pivot_table(
        index=["scenario_id", "contract_years"], columns="bound", values="M_Q_full_lower").reset_index()
    bnd = bnd.rename(columns={"EVIDENCE_LOWER": "M_Q_evidence_lower", "EVIDENCE_UPPER": "M_Q_evidence_upper"})
    rob = rob.rename(columns={"PRIMARY_REGIONAL_RENT_FALLBACK": "M_Q_regional_rent_fallback"})
    head = head.merge(rob[["scenario_id", "contract_years", "M_Q_ratio_only", "M_Q_offer_plus_rent",
                           "M_Q_regional_rent_fallback"]], on=["scenario_id", "contract_years"], how="left")
    aff = pd.read_csv(R / "robustness/offer_affordability_national.csv")
    aff = aff.loc[aff["allocation_family"].eq("FAMILY_BALANCED")].pivot_table(
        index=["scenario_id", "contract_years"], columns="cost_case",
        values=["M_Q_full_lower", "affordable_share_of_costed_Q"]).reset_index()
    aff.columns = ["scenario_id", "contract_years"] + [
        {"M_Q_full_lower": "M_Q_affordable", "affordable_share_of_costed_Q": "affordable_share"}[a] + "_" + b.lower()
        for a, b in aff.columns[2:]]
    head = head.merge(aff, on=["scenario_id", "contract_years"], how="left")
    head = head.merge(bnd[["scenario_id", "contract_years", "M_Q_evidence_lower", "M_Q_evidence_upper"]],
                      on=["scenario_id", "contract_years"], how="left")
    head = head.sort_values(keys).reset_index(drop=True)

    # ---- regional concentration -------------------------------------------
    detail = pd.read_csv(R / "deterministic/county_land_mobilization.csv", dtype={"fips": "string"},
                         usecols=["scenario_id", "contract_years", "allocation_family", "fips", "Q_P", "Q_M_full_lower"])
    detail["state_fips"] = detail["fips"].str[:2]
    focus = detail.loc[detail["scenario_id"].isin(["EXP_ABS_100", "SUPPORT_BALANCED_REFERENCE"])]
    st = focus.groupby(["scenario_id", "contract_years", "allocation_family", "state_fips"], as_index=False)[
        ["Q_P", "Q_M_full_lower"]].sum()
    st = st.groupby(["scenario_id", "contract_years", "state_fips"], as_index=False)[["Q_P", "Q_M_full_lower"]].mean()
    st["M_Q_central"] = st["Q_M_full_lower"] / st["Q_P"]
    st["share_of_national_Q_P"] = st["Q_P"] / st.groupby(["scenario_id", "contract_years"])["Q_P"].transform("sum")
    excl = (focus.loc[~focus["state_fips"].isin(SOUTHERN_PLAINS)]
            .groupby(["scenario_id", "contract_years", "allocation_family"])[["Q_P", "Q_M_full_lower"]].sum())
    excl = (excl["Q_M_full_lower"] / excl["Q_P"]).groupby(level=[0, 1]).mean().rename("M_Q_central").reset_index()
    excl["state_fips"] = "NATIONAL_EXCL_TX_OK_NM"
    regional = pd.concat([st, excl], ignore_index=True)

    # ---- county binding -----------------------------------------------------
    sp = pd.read_csv(R / "spatial/county_spatial_robustness.csv", dtype={"fips": "string"})
    binding = sp.groupby(["allocation_family", "contract_years"]).agg(
        counties_with_allocation=("A_P", lambda a: int((a > 0).sum())),
        binding_counties=("binding_central", lambda b: int((b == 1).sum())),
        unresolved_counties=("pressure_class", lambda c: int((c == "unresolved").sum())),
    ).reset_index()

    # ---- reconciliation -----------------------------------------------------
    full = pd.read_csv(R / "deterministic/county_land_mobilization.csv", dtype={"fips": "string"},
                       usecols=["Q_P", "A_P", "Q_M_full_lower", "unmet_Q_full_upper", "A_M_full_upper", "lambda", "kappa"])
    check("mobilized + unmet = upstream biomass",
          np.allclose(full["Q_M_full_lower"] + full["unmet_Q_full_upper"], full["Q_P"]))
    check("mobilized acreage <= upstream acreage", (full["A_M_full_upper"] <= full["A_P"] + 1e-9).all())
    check("lambda within [0, 1]", full["lambda"].dropna().between(0, 1).all())
    check("kappa within [0, 1]", full["kappa"].dropna().between(0, 1).all())
    check("three independent allocation families", det["allocation_family"].nunique() == 4,
          int(det["allocation_family"].nunique() - 1))
    check("structural variants equal config",
          var.groupby(["behaviour_weighting", "behaviour_representation", "landbase_structure"]).ngroups
          == cfg["uncertainty"]["implemented_structural_variants"])
    check("central identified production share > 99.5%",
          det["identified_production_share"].dropna().min() > 0.995,
          round(float(det["identified_production_share"].dropna().min()), 5))
    land = pd.read_csv("data/frozen/public/compatible_land.csv")
    check("compatible land non-negative", (land["B"].dropna() >= 0).all(), int(land["B"].isna().sum()))
    check("county FIPS are five characters", sp["fips"].str.len().eq(5).all())

    out_m, out_v = R / "manuscript", R / "validation"
    out_m.mkdir(parents=True, exist_ok=True)
    out_v.mkdir(parents=True, exist_ok=True)
    head.to_csv(out_m / "headline_results.csv", index=False)
    regional.to_csv(out_m / "regional_mobilization.csv", index=False)
    binding.to_csv(out_m / "county_binding_summary.csv", index=False)
    pd.read_csv(R / "structural/feedstock_transfer_coverage.csv").to_csv(out_m / "feedstock_coverage.csv", index=False)
    pd.read_csv(R / "robustness/offer_affordability_by_feedstock.csv").to_csv(
        out_m / "payable_rent_by_feedstock.csv", index=False)
    ledger = pd.DataFrame(checks)
    ledger.to_csv(out_v / "reconciliation_checks.csv", index=False)

    if ledger["status"].ne("PASS").any():
        raise AssertionError(ledger.loc[ledger["status"].ne("PASS")].to_string())
    show = head.loc[head["contract_years"].eq(5)].drop(columns=["contract_years"])
    print(f"PASS: {len(ledger)} reconciliation checks.")
    print(show.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
