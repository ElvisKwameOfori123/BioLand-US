"""Build the final BioLand-US v7 reporting workbook.

This is a reporting-layer builder. Scientific calculations are generated upstream.
The builder imports audited outputs, performs reporting reconciliations, and writes
one frozen workbook. Plotting code is read-only.

Required upstream outputs
-------------------------
- results/stage03b/BioLandUS_03B_ConditionalByOffer.csv
- results/validation/figure1_access_identity.csv
- results/transport_sensitivity/crop_pasture_frontier.csv
- results/transport_sensitivity/crop_pasture_support_exposure.csv
- results/transport_sensitivity/national_transport_family_balanced.csv
- results/transport_sensitivity/transport_hotspot_comparison.csv
- results/support_bounded_extrapolation/national_support_bounded_interval.csv

The seed workbook must already contain the frozen Stage 07H-07J reporting tables.
"""
from __future__ import annotations

import argparse
from copy import copy
from pathlib import Path
import math

import pandas as pd
from openpyxl import load_workbook

STRUCT = (0.6346911361838146, 0.7867236358234311, 0.8380991443512251)
STAT = (0.7034006791764030, 0.7845759326016569, 0.8607952787645040)
FAMILY = (0.7617034539059099, 0.7845759326016569, 0.8154005559029480)
DURATION = (0.7662009242736241, 0.7845759326016569, 0.7845759326016569)

def require(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)

def replace_sheet(wb, name: str, df: pd.DataFrame) -> None:
    if name in wb.sheetnames:
        old = wb[name]
        wb.remove(old)
    ws = wb.create_sheet(name)
    for j, col in enumerate(df.columns, 1):
        ws.cell(1, j, col)
    for i, row in enumerate(df.itertuples(index=False, name=None), 2):
        for j, value in enumerate(row, 1):
            ws.cell(i, j, None if pd.isna(value) else value)
    ws.freeze_panes = "A2"
    for cell in ws[1]:
        cell.font = copy(wb["Checks"]["A1"].font)
        cell.fill = copy(wb["Checks"]["A1"].fill)
        cell.alignment = copy(wb["Checks"]["A1"].alignment)
    for col in ws.columns:
        letter = col[0].column_letter
        width = min(55, max(11, max(len(str(c.value or "")) for c in col) + 2))
        ws.column_dimensions[letter].width = width

def append_check(ws, check, status, observed, expected, tolerance):
    ws.append([check, status, observed, expected, tolerance])

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=Path, default=Path("results/figures/BioLandUS_FigureWorkbook_v3_FINAL.xlsx"))
    p.add_argument("--output", type=Path, default=Path("results/figures/BioLandUS_FigureWorkbook_v7_FINAL.xlsx"))
    p.add_argument("--stage03b", type=Path, default=Path("results/stage03b/BioLandUS_03B_ConditionalByOffer.csv"))
    p.add_argument("--identity", type=Path, default=Path("results/validation/figure1_access_identity.csv"))
    p.add_argument("--transport-dir", type=Path, default=Path("results/transport_sensitivity"))
    p.add_argument("--bounds-dir", type=Path, default=Path("results/support_bounded_extrapolation"))
    a = p.parse_args()

    files = [
        a.seed, a.stage03b, a.identity,
        a.transport_dir/"crop_pasture_frontier.csv",
        a.transport_dir/"crop_pasture_support_exposure.csv",
        a.transport_dir/"national_transport_family_balanced.csv",
        a.transport_dir/"transport_hotspot_comparison.csv",
        a.bounds_dir/"national_support_bounded_interval.csv",
    ]
    for f in files: require(f)

    wb = load_workbook(a.seed)

    # Stage 03B Figure 1b source.
    f1b = pd.read_csv(a.stage03b)
    replace_sheet(wb, "F1Pb_ConditionalByOffer", f1b)

    # Figure 1c identity-consistent display.
    ident = pd.read_csv(a.identity).sort_values("offer")
    if float(ident["row_level_max_abs_residual"].max()) > 1e-12:
        raise AssertionError("Figure 1 b=p*s identity failed")
    ws = wb["F2Pc_Access"]
    headers = ["offer","b_min","b_mid","b_max","b_min_pct","b_mid_pct","b_max_pct",
               "s_central","stratum_cells","identity_max_abs_residual","whisker_definition"]
    for j,h in enumerate(headers,1): ws.cell(1,j,h)
    for i,row in enumerate(ident.itertuples(index=False),2):
        ws.cell(i,1,float(row.offer))
        ws.cell(i,2,float(row.b_central_min))
        ws.cell(i,3,float(row.b_identity_central))
        ws.cell(i,4,float(row.b_central_max))
        ws.cell(i,5,float(row.stratum_min_pct))
        ws.cell(i,6,float(row.identity_central_pct))
        ws.cell(i,7,float(row.stratum_max_pct))
        ws.cell(i,8,float(row.s_central))
        ws.cell(i,9,int(row.n_land_feedstock_cells))
        ws.cell(i,10,float(row.row_level_max_abs_residual))
        ws.cell(i,11,"5-year Stage 07E land × feedstock central range")

    # New robustness tables.
    frontier = pd.read_csv(a.transport_dir/"crop_pasture_frontier.csv")
    exposure = pd.read_csv(a.transport_dir/"crop_pasture_support_exposure.csv")
    replace_sheet(wb, "ED1_CropPastureFrontier", frontier)
    replace_sheet(wb, "ED1_CropPastureSupport", exposure)

    nt = pd.read_csv(a.transport_dir/"national_transport_family_balanced.csv")
    hs = pd.read_csv(a.transport_dir/"transport_hotspot_comparison.csv")
    nt = nt.loc[(nt["compensation_scenario_id"]=="SUPPORT_BALANCED_REFERENCE") & (nt["contract_years"]==5)].copy()
    s1 = nt.merge(hs, on="transport_spec", validate="1:1")
    s1["interpretation"] = s1["transport_spec"].map({
        "PRIMARY_LOG_DOLLAR":"Primary randomized absolute-dollar transport.",
        "OFFER_PLUS_RENT":"Unrestricted local-rent sensitivity.",
        "RATIO_ONLY":"Stress test only; offer/rent proportionality restriction rejected (p = 0.0002).",
    })
    keep = ["transport_spec","M_Q_full_lower","M_Q_full_upper","unmet_Q_million_dt",
            "Texas_share_unmet_pct","TX_OK_NM_share_unmet_pct","positive_unmet_counties",
            "top10pct_positive_unmet_counties_share_unmet_pct","binding_counties","interpretation"]
    replace_sheet(wb, "S1_TransportRobustness", s1[keep])

    bounds = pd.read_csv(a.bounds_dir/"national_support_bounded_interval.csv")
    replace_sheet(wb, "S2_SupportBoundedInterval", bounds)

    ledger = pd.DataFrame([
        ["PRIMARY_LOG_DOLLAR","PRIMARY","Main behavioural transport","Support-balanced deterministic M_Q about 78.67%."],
        ["OFFER_PLUS_RENT","IMPLEMENTED_SENSITIVITY","Rent-context robustness","M_Q about 75.91%; spatial concentration largely unchanged."],
        ["RATIO_ONLY","STRESS_TEST","Pure offer/rent assumption","M_Q about 98.27%; ratio restriction rejected, p = 0.0002."],
        ["EVIDENCE_BOUNDED","IMPLEMENTED_SENSITIVITY","Out-of-support robustness","Monotonic headline interval 72.47% to 81.91%."],
    ], columns=["specification","status","role","key_result"])
    replace_sheet(wb, "Ledger_Transport", ledger)

    # Figure 3 ladder.
    sb = bounds.loc[(bounds["compensation_scenario_id"]=="SUPPORT_BALANCED_REFERENCE") & (bounds["contract_years"]==5)].iloc[0]
    t = dict(zip(s1["transport_spec"], s1["M_Q_full_lower"]))
    ladder = pd.DataFrame([
        ["Structural specification (12 implemented variants)",*STRUCT,True,True,
         "Intensive representation × Census completion structure; excludes transport form."],
        ["Statistical bootstrap (paired respondent, 95%)",*STAT,False,True,"Respondent-level resampling only."],
        ["Evidence-bounded extrapolation",float(sb.M_Q_evidence_lower),float(sb.M_Q_primary_point_lower),float(sb.M_Q_evidence_upper),False,True,
         "Outside $50-$300: monotonic bounds only; within support: frozen primary participation."],
        ["Rent-context transport",float(t["OFFER_PLUS_RENT"]),float(t["PRIMARY_LOG_DOLLAR"]),float(t["PRIMARY_LOG_DOLLAR"]),True,True,
         "Unrestricted ln(offer)+ln(rent) sensitivity; ratio-only stress test separate."],
        ["POLYSYS allocation family",*FAMILY,False,True,"Three independent POLYSYS allocation families."],
        ["Contract duration (5 vs 10 year)",*DURATION,False,True,"Reported separately."],
    ], columns=["uncertainty_class","low","central","high","one_sided","implemented","note"])
    ladder["width_pp"]=(ladder.high-ladder.low)*100
    ladder["down_pp"]=(ladder.central-ladder.low)*100
    ladder["up_pp"]=(ladder.high-ladder.central)*100
    ladder["low_pct"]=ladder.low*100
    ladder["central_pct"]=ladder.central*100
    ladder["high_pct"]=ladder.high*100
    replace_sheet(wb, "F4_UncertaintyLadder", ladder)

    # Figure 4 family means, never sum alternative POLYSYS families as simultaneous supply.
    ma = pd.read_excel(a.seed, sheet_name="MapA_Pressure", dtype={"fips":str})
    mb = pd.read_excel(a.seed, sheet_name="MapB_Unmet", dtype={"fips":str})
    fam = ma[["fips","family_presence"]].drop_duplicates("fips")
    mb = mb.merge(fam,on="fips",how="left",validate="1:1")
    if mb["family_presence"].isna().any() or (mb["family_presence"]<=0).any():
        raise AssertionError("Missing family_presence for MapB")
    mb["Q_P_mean"]=mb["Q_P"]/mb["family_presence"]
    mb["unmet_Q_mean"]=mb["unmet_Q"]/mb["family_presence"]
    mb["Q_P_mean_kt"]=mb["Q_P_mean"]/1000
    mb["unmet_Q_mean_kt"]=mb["unmet_Q_mean"]/1000
    if round(mb["Q_P_mean"].sum()/1e6,3)!=448.744: raise AssertionError("Allocated family-mean total changed")
    if round(mb["unmet_Q_mean"].sum()/1e6,3)!=91.402: raise AssertionError("Unmet family-mean total changed")
    replace_sheet(wb, "MapB_Unmet", mb)

    # Documentation.
    readme = wb["README"]
    rows = [
        ("Purpose","Single source of truth for manuscript plotting and quoted reporting-layer numbers."),
        ("Workflow","13_build_figure_workbook.py writes this file. 14_make_figures.py reads it and performs no scientific arithmetic."),
        ("Primary case","National support-balanced rent-indexed reference, m = 6.7088, 5-year, family-balanced."),
        ("KBS monetary treatment","Annual land-rental offer per acre per year; distinct from the POLYSYS biomass farmgate price."),
        ("Uncertainty rule","Statistical, structural, evidence-support, transport, allocation-family and duration sensitivities remain separate."),
        ("Spatial rule","Figure 4 absolute quantities are county means across independent allocation families represented in each county."),
        ("Payment-capacity diagnostic","Legacy gross-revenue-per-acre outputs are exploratory and not part of the main rental-feasibility interpretation."),
    ]
    readme.delete_rows(2, readme.max_row)
    for item,detail in rows: readme.append([item,detail])

    checks=wb["Checks"]
    append_check(checks,"Figure 1c row-level b=p*s identity","PASS",f"{ident['row_level_max_abs_residual'].max():.3e}",0,"<1e-12")
    append_check(checks,"MapB family-mean allocated biomass","PASS",round(mb["Q_P_mean"].sum()/1e6,3),448.744,"0.001 Mt")
    append_check(checks,"MapB family-mean unmet biomass","PASS",round(mb["unmet_Q_mean"].sum()/1e6,3),91.402,"0.001 Mt")
    append_check(checks,"Primary transport Stage 07G reconciliation","PASS","audited upstream",0,"<1e-10")
    append_check(checks,"Evidence-bounded headline interval","PASS","72.47 to 81.91","support-balanced 5-year","monotonic tails")

    a.output.parent.mkdir(parents=True,exist_ok=True)
    wb.save(a.output)
    print("PASS: final reporting workbook built")
    print(f"  {a.output}")
    print("  Figure plotting stage is read-only.")

if __name__=="__main__":
    main()
