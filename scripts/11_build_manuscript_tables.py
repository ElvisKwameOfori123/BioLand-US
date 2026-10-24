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
    results/manuscript/manuscript_numbers.csv     every number quoted in the paper
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

    tables = paper_tables(R, cfg, det, head, county_detail=detail)
    for name, frame in tables.items():
        frame.to_csv(out_m / f"{name}.csv", index=False)
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


def paper_tables(R: Path, cfg: dict, det: pd.DataFrame, head: pd.DataFrame, county_detail: pd.DataFrame) -> dict:
    """Table 2, Table 3, land-class table and the quoted-numbers ledger."""
    H, Y = "SUPPORT_BALANCED_REFERENCE", 5
    fam = det.loc[det["allocation_family"].ne("FAMILY_BALANCED") & det["contract_years"].eq(Y)]
    h = head.loc[head["contract_years"].eq(Y)].set_index("scenario_id")
    hr = h.loc[H]
    central = float(hr["M_Q_central"])

    # ---- Table 2: mobilization by offer design --------------------------------
    exposure = pd.read_csv(R / "robustness/support_exposure.csv")
    within = (exposure.loc[exposure["land_type"].eq("All") & exposure["support"].eq("WITHIN_SUPPORT")]
              .groupby("scenario_id")["production_share"].mean())
    spread = fam.groupby("scenario_id")["M_Q_full_lower"].agg(lambda v: v.max() - v.min())
    order = ["EXP_ABS_50", "EXP_ABS_100", "EXP_ABS_200", "EXP_ABS_300", "RENT_PARITY_BENCHMARK",
             "SUPPORT_ENTRY_REFERENCE", H, "HIGHER_COMPENSATION_200_REFERENCE", "HIGHER_COMPENSATION_300_REFERENCE"]
    capped = pd.read_csv(R / "robustness/capped_offer_national.csv")
    capped = capped.loc[capped["allocation_family"].eq("FAMILY_BALANCED") & capped["contract_years"].eq(Y)].set_index(
        ["scenario_id", "cost_case"])["M_Q_full_lower"]
    t2 = pd.DataFrame({
        "scenario_id": order,
        "offer_design": [h.loc[s, "track"] for s in order],
        "rent_multiplier": [det.loc[det["scenario_id"].eq(s), "rent_multiplier"].iloc[0] for s in order],
        "M_Q_central": [h.loc[s, "M_Q_central"] for s in order],
        "boot_p025": [h.loc[s, "M_Q_boot_p025"] for s in order],
        "boot_p975": [h.loc[s, "M_Q_boot_p975"] for s in order],
        "unmet_share": [1 - h.loc[s, "M_Q_central"] for s in order],
        "family_range_pp": [100 * spread[s] for s in order],
        "within_tested_range_share_of_Q": [within.get(s, 1.0) for s in order],
        "M_Q_affordable_low_cost": [h.loc[s, "M_Q_affordable_low_cost"] for s in order],
        "M_Q_affordable_high_cost": [h.loc[s, "M_Q_affordable_high_cost"] for s in order],
        "M_Q_capped_low_cost": [capped.loc[(s, "LOW_COST")] for s in order],
        "M_Q_capped_high_cost": [capped.loc[(s, "HIGH_COST")] for s in order],
    })

    # ---- Table 3: robustness synthesis at the headline ------------------------
    var = pd.read_csv(R / "structural/national_structural_variants.csv")
    vb = var.loc[var["scenario_id"].eq(H) & var["contract_years"].eq(Y)].groupby(
        ["behaviour_weighting", "behaviour_representation", "landbase_structure"])["M_Q_full_lower"].mean()
    per_choice = vb.xs("PER_CHOICE", level="behaviour_weighting")
    land_c = cfg["land"]["central_structure"]
    loco = pd.read_csv(R / "robustness/loco_national.csv")
    loco = loco.loc[loco["scenario_id"].eq(H), "M_Q_full_lower"]
    dollar = pd.read_csv(R / "robustness/offer_affordability_dollar_year.csv")["M_Q_full_lower"]
    capped_dollar = pd.read_csv(R / "robustness/capped_offer_dollar_year.csv")["M_Q_full_lower"]
    hr10 = head.loc[head["contract_years"].eq(10)].set_index("scenario_id").loc[H]
    rows = [
        ("Behavioural sampling", "Paired respondent bootstrap, 1,000 draws", hr["M_Q_boot_p025"], hr["M_Q_boot_p975"], "Table 2"),
        ("Leave one survey county out", "12 participation models", loco.min(), loco.max(), "Fig. S1c"),
        ("Conditional acreage representation", "Lower, IPW, central, upper", per_choice.xs(land_c, level="landbase_structure").min(),
         per_choice.xs(land_c, level="landbase_structure").max(), "Table S2"),
        ("Census suppression completion", "Farmland-weighted vs equal shares", hr["M_Q_equal_land"], central, "Note S1"),
        ("Person-to-acreage weighting", "Acreage-weighted participation and share", hr["M_Q_acre_weighted"], central, "Table S1"),
        ("Out-of-range offers", "Monotone evidence bounds outside $50–300", hr["M_Q_evidence_lower"], hr["M_Q_evidence_upper"], "Fig. S6b"),
        ("Rent in participation", "Offer + rent model", hr["M_Q_offer_plus_rent"], central, "Table S3"),
        ("Offer-to-rent ratio (stress test)", "Ratio model; restriction rejected, p = 0.0002", central, hr["M_Q_ratio_only"], "Table S3"),
        ("Missing rent", "USDA-region fallback for 73 cells", central, hr["M_Q_regional_rent_fallback"], "Note S2"),
        ("POLYSYS allocation family", "Three independent allocations", fam.loc[fam["scenario_id"].eq(H), "M_Q_full_lower"].min(),
         fam.loc[fam["scenario_id"].eq(H), "M_Q_full_lower"].max(), "Table 2"),
        ("Contract length", "10-year instead of 5-year", hr10["M_Q_central"], central, "Table 2"),
        ("Offer affordability at $70/dt", "Low / high cost budget; 2016–2022 price dollars", dollar.min(), dollar.max(), "Table S4"),
        ("Offer capped at payable rent", "O = min(mR, L); low / high cost; 2016–2022 price dollars", capped_dollar.min(),
         capped_dollar.max(), "Table 2"),
    ]
    t3 = pd.DataFrame(rows, columns=["check", "what_varies", "M_Q_low", "M_Q_high", "supplement"])
    t3["largest_shift_pp"] = 100 * np.maximum((t3["M_Q_low"] - central).abs(), (t3["M_Q_high"] - central).abs())
    t3["verdict"] = np.select([t3["largest_shift_pp"] <= 5, t3["largest_shift_pp"] <= 15],
                              ["Robust (≤5 pp)", "Moderate (5–15 pp)"], "Large (>15 pp)")
    stress = t3["check"].str.contains("stress test")
    t3.loc[stress, "verdict"] = "Stress test only (model rejected)"
    t3.insert(2, "M_Q_central", central)

    # ---- land classes ---------------------------------------------------------
    d = county_detail.copy()
    lc_det = pd.read_csv(R / "deterministic/county_land_mobilization.csv", usecols=["scenario_id", "contract_years",
                         "allocation_family", "land_type", "Q_P", "Q_M_full_lower"])
    lc = (lc_det.loc[lc_det["contract_years"].eq(Y)]
          .groupby(["scenario_id", "allocation_family", "land_type"])[["Q_P", "Q_M_full_lower"]].sum())
    lc = (lc["Q_M_full_lower"] / lc["Q_P"]).groupby(level=["scenario_id", "land_type"]).mean().rename("M_Q_central").reset_index()
    ex = (exposure.loc[exposure["land_type"].ne("All")].groupby(["scenario_id", "land_type", "support"])["production_share"]
          .mean().unstack("support").reset_index())
    land_class = lc.merge(ex, on=["scenario_id", "land_type"], how="left")

    # ---- quoted numbers ---------------------------------------------------------
    sp = pd.read_csv(R / "spatial/county_spatial_robustness.csv", dtype={"fips": "string"})
    sp5 = sp.loc[sp["contract_years"].eq(Y) & sp["A_P"].gt(0)]
    rho = sp5.groupby("fips")["rho_central"].median()
    unresolved = sp5.groupby("fips")["pressure_class"].agg(lambda x: (x == "unresolved").all())
    cls = pd.Series(np.select([unresolved.reindex(rho.index), np.isinf(rho), rho >= 2, rho >= 1, rho >= 0.5],
                              ["unresolved", "zero_capacity", "ge_2", "c1_2", "c05_1"], "lt_05"), index=rho.index)
    n_fam = sp5.groupby("fips")["allocation_family"].nunique()
    agree = sp5.groupby("fips")["robust_top10_flag"].sum()
    unmet = sp.loc[sp["contract_years"].eq(Y)].groupby("fips")["unmet_Q_central"].sum()
    unmet = unmet[unmet > 0].sort_values(ascending=False)
    top = unmet.iloc[: int(np.ceil(0.1 * len(unmet)))].sum() / unmet.sum()
    regional = pd.read_csv(R / "manuscript/regional_mobilization.csv", dtype={"state_fips": "string"})
    beh = pd.read_csv(R / "behaviour/participation_margins.csv")
    cond = pd.read_csv(R / "behaviour/conditional_acreage_by_offer.csv")
    coef = pd.read_csv(R / "behaviour/participation_coefficients.csv")
    pay = pd.read_csv(R / "robustness/offer_affordability_by_feedstock.csv").set_index(["feedstock", "land_type"])
    sb = lambda s: h.loc[s, "M_Q_central"]  # noqa: E731
    nums = {
        "participation_p50": beh.loc[beh["offer"].eq(50), "p_categorical"].iloc[0],
        "participation_p300": beh.loc[beh["offer"].eq(300), "p_categorical"].iloc[0],
        "conditional_share_min_by_offer": cond["share"].min(),
        "conditional_share_max_by_offer": cond["share"].max(),
        "conditional_share_offer_joint_p": cond["joint_offer_p"].iloc[0],
        "conditional_share_central": float(pd.read_csv("data/frozen/public/behaviour_parameters_public.csv")
                                           .set_index("parameter").loc["conditional_acreage_central_primary", "value"]),
        "pasture_coefficient_p": coef.loc[coef["model"].eq("SMOOTH") & coef["term"].eq("pasture"), "p"].iloc[0],
        "MQ_exp50": sb("EXP_ABS_50"), "MQ_exp100": sb("EXP_ABS_100"), "MQ_exp300": sb("EXP_ABS_300"),
        "MQ_rent_parity": sb("RENT_PARITY_BENCHMARK"), "MQ_m335": sb("SUPPORT_ENTRY_REFERENCE"),
        "MQ_headline": central, "MQ_headline_boot_p025": hr["M_Q_boot_p025"], "MQ_headline_boot_p975": hr["M_Q_boot_p975"],
        "MQ_headline_struct_min": hr["M_Q_struct_min"], "MQ_headline_struct_max": hr["M_Q_struct_max"],
        "MQ_headline_acre_weighted": hr["M_Q_acre_weighted"],
        "MQ_headline_affordable_low_cost": hr["M_Q_affordable_low_cost"],
        "MQ_headline_affordable_high_cost": hr["M_Q_affordable_high_cost"],
        "MQ_headline_affordable_range_all_dollar_years_min": dollar.min(),
        "MQ_headline_affordable_range_all_dollar_years_max": dollar.max(),
        "MQ_headline_crop": land_class.query("scenario_id == @H and land_type == 'Crop'")["M_Q_central"].iloc[0],
        "MQ_headline_pasture": land_class.query("scenario_id == @H and land_type == 'Pasture'")["M_Q_central"].iloc[0],
        "within_range_share_rent_parity": within["RENT_PARITY_BENCHMARK"], "within_range_share_headline": within[H],
        "unmet_top10pct_counties_share": top,
        "unmet_share_texas": unmet[unmet.index.str[:2] == "48"].sum() / unmet.sum(),
        "unmet_share_tx_ok_nm": unmet[unmet.index.str[:2].isin(SOUTHERN_PLAINS)].sum() / unmet.sum(),
        "MQ_headline_excl_tx_ok_nm": regional.query("scenario_id == @H and contract_years == @Y and "
                                                    "state_fips == 'NATIONAL_EXCL_TX_OK_NM'")["M_Q_central"].iloc[0],
        "texas_share_of_Q_P": regional.query("scenario_id == @H and contract_years == @Y and state_fips == '48'")[
            "share_of_national_Q_P"].iloc[0],
        "counties_pressure_lt_05": int((cls == "lt_05").sum()), "counties_pressure_05_1": int((cls == "c05_1").sum()),
        "counties_pressure_1_2": int((cls == "c1_2").sum()), "counties_pressure_ge_2": int((cls == "ge_2").sum()),
        "counties_zero_capacity": int((cls == "zero_capacity").sum()), "counties_unresolved": int((cls == "unresolved").sum()),
        "counties_P_bind_ge_08": int((sp5.groupby("fips")["P_bind"].mean() >= 0.8).sum()),
        "counties_P_top10_ge_08": int((sp5.groupby("fips")["P_top10_risk"].mean() >= 0.8).sum()),
        "counties_in_all_three_families": int((n_fam == 3).sum()),
        "hotspot_in_3_families": int(((n_fam == 3) & (agree == 3)).sum()),
        "hotspot_in_2_families": int(((n_fam == 3) & (agree == 2)).sum()),
        "hotspot_in_1_family": int(((n_fam == 3) & (agree == 1)).sum()),
        "switchgrass_payable_rent_low_cost_pasture": pay.loc[("Switchgrass", "Pasture"), "median_l_max_low_cost"],
        "switchgrass_payable_rent_low_cost_crop": pay.loc[("Switchgrass", "Crop"), "median_l_max_low_cost"],
        "loco_headline_min": loco.min(), "loco_headline_max": loco.max(),
    }
    nums.update(extra_numbers(R, H, Y, fam, beh, coef))
    ledger = pd.DataFrame({"key": list(nums), "value": [float(v) for v in nums.values()]})
    return {"table2_mobilization_by_offer": t2, "table3_robustness_synthesis": t3,
            "land_class_mobilization": land_class, "manuscript_numbers": ledger}


def extra_numbers(R: Path, H: str, Y: int, fam: pd.DataFrame, beh: pd.DataFrame, coef: pd.DataFrame) -> dict:
    """Capped offers (E02), gate geography (E03), rent coverage and denominators."""
    s = float(pd.read_csv("data/frozen/public/behaviour_parameters_public.csv")
              .set_index("parameter").loc["conditional_acreage_central_primary", "value"])
    n = {}
    for o in (50, 300):
        p = beh.loc[beh["offer"].eq(o), "p_smooth"].iloc[0]
        n[f"participation_smooth_p{o}"] = p
        n[f"behavioural_access_b{o}"] = p * s
    cat = coef.loc[coef["model"].eq("CATEGORICAL")].set_index("term")["p"]
    n["categorical_contract10_p"] = cat["contract10"]
    n["categorical_pasture_p"] = cat["pasture"]
    n["categorical_switchgrass_p"] = cat["switchgrass"]

    # Denominators: family-mean prospective totals and the headline gap.
    h = fam.loc[fam["scenario_id"].eq(H)]
    n["Q_P_family_mean_dt"] = h["Q_P"].mean()
    n["A_P_family_mean_acres"] = h["A_P"].mean()
    n["unmet_Q_headline_dt"] = (h["Q_P"] - h["Q_M_full_lower"]).mean()
    n["unmet_A_headline_acres"] = (h["A_P"] - h["A_M_full_lower"]).mean()
    res = pd.read_csv("data/frozen/public/polysys_allocation.csv", dtype={"fips": "string"})
    tot = res.groupby("allocation_family")["Q_P"].sum()
    herb = res.loc[res["treatment_class"].eq("HERBACEOUS")].groupby("allocation_family")["Q_P"].sum()
    n["herbaceous_share_of_Q_P"] = float((herb / tot).mean())

    cap = pd.read_csv(R / "robustness/capped_offer_national.csv")
    cap = cap.loc[cap["allocation_family"].eq("FAMILY_BALANCED") & cap["contract_years"].eq(Y)].set_index(
        ["scenario_id", "cost_case"])
    for case in ("LOW_COST", "HIGH_COST"):
        c = cap.loc[(H, case)]
        k = case.split("_")[0].lower()
        n[f"MQ_capped_headline_{k}"] = c["M_Q_full_lower"]
        n[f"MQ_capped_headline_{k}_evidence_lower"] = c["M_Q_evidence_lower"]
        n[f"MQ_capped_headline_{k}_evidence_upper"] = c["M_Q_evidence_upper"]
        n[f"capped_headline_{k}_declined_share"] = c["declined_share_of_costed_Q"]
        n[f"capped_headline_{k}_below_50_share"] = c["below_support_share_of_costed_Q"]
        for sc in ("EXP_ABS_100", "EXP_ABS_300", "RENT_PARITY_BENCHMARK", "SUPPORT_ENTRY_REFERENCE",
                   "HIGHER_COMPENSATION_300_REFERENCE"):
            n[f"MQ_capped_{sc}_{k}"] = cap.loc[(sc, case), "M_Q_full_lower"]
    cd = pd.read_csv(R / "robustness/capped_offer_dollar_year.csv")["M_Q_full_lower"]
    n["MQ_capped_headline_range_all_dollar_years_min"] = cd.min()
    n["MQ_capped_headline_range_all_dollar_years_max"] = cd.max()

    g = pd.read_csv(R / "robustness/gate_geography.csv").set_index(["dimension", "group"])
    for lt in ("Crop", "Pasture"):
        x = g.loc[("land_type", lt)]
        n[f"{lt.lower()}_willingness_unmet_share"] = x["willingness_unmet_share"]
        n[f"{lt.lower()}_offer_exceeds_L_low"] = x["offer_exceeds_L_share_of_costed_Q_low"]
        n[f"{lt.lower()}_offer_exceeds_L_high"] = x["offer_exceeds_L_share_of_costed_Q_high"]
        n[f"{lt.lower()}_affordability_loss_share_low"] = x["affordability_loss_share_low"]
    for reg in ("Southern Plains", "Northern Plains", "Corn Belt"):
        x = g.loc[("usdaregion", reg)]
        key = reg.lower().replace(" ", "_")
        n[f"{key}_willingness_unmet_share"] = x["willingness_unmet_share"]
        n[f"{key}_offer_exceeds_L_low"] = x["offer_exceeds_L_share_of_costed_Q_low"]
        n[f"{key}_affordability_loss_share_low"] = x["affordability_loss_share_low"]
    x = g.loc[("southern_plains_tx_ok_nm", "TX_OK_NM")]
    n["tx_ok_nm_affordability_loss_share_low"] = x["affordability_loss_share_low"]
    n["tx_ok_nm_offer_exceeds_L_low"] = x["offer_exceeds_L_share_of_costed_Q_low"]

    conc = pd.read_csv(R / "robustness/deficit_concentration_by_design.csv").set_index("design")
    for d in conc.index:
        n[f"unmet_share_tx_ok_nm_{d.lower()}"] = conc.loc[d, "unmet_share_tx_ok_nm"]
    n["tx_ok_nm_share_of_Q_P"] = float((res.loc[res["fips"].str[:2].isin(SOUTHERN_PLAINS)]
                                        .groupby("allocation_family")["Q_P"].sum() / tot).mean())

    # Rent coverage: survey-county rents against the rents of the prospective allocation.
    survey = pd.read_csv("data/frozen/public/studyA_rent_context.csv")["rent_2012usd_per_acre"]
    n["survey_rent_min"], n["survey_rent_max"] = survey.min(), survey.max()
    rents = pd.read_csv("data/frozen/public/rent_context.csv", dtype={"fips": "string"})
    r = res.merge(rents, on=["fips", "land_type"], how="left")
    r = r.loc[r["rent_supported"].fillna(False).astype(bool) & r["A_P"].gt(0)]
    for lt in ("Crop", "Pasture"):
        x = r.loc[r["land_type"].eq(lt)]
        n[f"{lt.lower()}_rent_median"] = wq(x["rent_2012usd_per_acre"], x["A_P"], 0.5)
        n[f"{lt.lower()}_rent_p95"] = wq(x["rent_2012usd_per_acre"], x["A_P"], 0.95)
        n[f"{lt.lower()}_A_P_share_below_survey_min"] = x.loc[x["rent_2012usd_per_acre"] < survey.min(), "A_P"].sum() / x["A_P"].sum()
    tx = r.loc[r["land_type"].eq("Pasture") & r["fips"].str[:2].eq("48")]
    n["texas_pasture_rent_median"] = wq(tx["rent_2012usd_per_acre"], tx["A_P"], 0.5)
    return n


def wq(values: pd.Series, weights: pd.Series, q: float) -> float:
    v, w = values.to_numpy(float), weights.to_numpy(float)
    o = np.argsort(v)
    cw = np.cumsum(w[o])
    return float(v[o][np.searchsorted(cw, q * cw[-1])])


if __name__ == "__main__":
    main()
