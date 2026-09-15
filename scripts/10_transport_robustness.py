"""Propagate alternative participation-transport specifications through frozen BioLand-US T1 capacity.

Primary science remains the randomized absolute-dollar transport. This script adds:
1) pure ln(offer/rent) stress test;
2) unrestricted ln(offer)+ln(rent) sensitivity;
3) Crop/Pasture mobilization and experimental-support diagnostics;
4) a hard reconciliation to frozen Stage 07G.

Run after stata/06_export_transport_sensitivity.do.
"""
from __future__ import annotations

import os
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(os.environ.get("BIOLAND_PROJECT", Path.cwd()))
DATA = ROOT / "data"
OUT = ROOT / "results" / "transport_sensitivity"
OUT.mkdir(parents=True, exist_ok=True)

POLY = DATA / "frozen" / "public" / "POLYSYS_PerennialAllocation_2041_70dt.csv"
LAND = DATA / "frozen" / "public" / "Census2022_County_CropPasture_LandBase_JOINT_STRUCTURAL.csv"
MAP = DATA / "frozen" / "public" / "BioLandUS_FeedstockTransfer_07E1_FROZEN.csv"
BEH = DATA / "interim" / "BioLandUS_07E_RentIndexedBehaviouralAccess.csv"
HEAD = DATA / "frozen" / "public" / "BioLandUS_07G_HeadlineCentralResults.csv"
RATIO = OUT / "ratio_only_coefficients.csv"
UNRES = OUT / "offer_plus_rent_coefficients.csv"

FAMILIES = {
    "emerging": "FAMILY_01",
    "mature-market low": "FAMILY_02",
    "mature-market medium": "FAMILY_03",
}
SB = "SUPPORT_BALANCED_REFERENCE"
TOL = 1e-10

def need(p: Path):
    if not p.exists():
        raise FileNotFoundError(p)

def fips(s):
    return s.astype("string").str.replace(r"\.0$", "", regex=True).str.zfill(5)

def land(s):
    return s.astype("string").str.strip().str.lower().map({"crop":"Crop","pasture":"Pasture"})

def resource(x):
    return " ".join(str(x).strip().lower().replace("_"," ").replace("-"," ").split())

def coef(path):
    d = pd.read_csv(path)
    return dict(zip(d["parameter"].astype(str), pd.to_numeric(d["value"], errors="raise")))

def expit(x):
    x = np.asarray(x, float)
    out = np.empty_like(x)
    pos = x >= 0
    out[pos] = 1/(1+np.exp(-x[pos]))
    ex = np.exp(x[~pos])
    out[~pos] = ex/(1+ex)
    return out

def pred_ratio(d, b):
    m = pd.to_numeric(d["rent_multiplier"], errors="raise").to_numpy(float)
    y10 = pd.to_numeric(d["contract_years"], errors="raise").eq(10).to_numpy(float)
    pasture = d["land_type"].eq("Pasture").to_numpy(float)
    sw = d["experimental_feedstock"].astype(str).str.lower().eq("switchgrass").to_numpy(float)
    return expit(b["intercept"] + b["ln_offer_rent_ratio"]*np.log(m)
                 + b["contract_10yr"]*y10 + b["pasture"]*pasture + b["switchgrass"]*sw)

def pred_unres(d, b):
    o = pd.to_numeric(d["offer_2012usd_acre_year"], errors="raise").to_numpy(float)
    m = pd.to_numeric(d["rent_multiplier"], errors="raise").to_numpy(float)
    r = o/m
    y10 = pd.to_numeric(d["contract_years"], errors="raise").eq(10).to_numpy(float)
    pasture = d["land_type"].eq("Pasture").to_numpy(float)
    sw = d["experimental_feedstock"].astype(str).str.lower().eq("switchgrass").to_numpy(float)
    return expit(b["intercept"] + b["ln_offer"]*np.log(o) + b["ln_rent"]*np.log(r)
                 + b["contract_10yr"]*y10 + b["pasture"]*pasture + b["switchgrass"]*sw)

def capacity(A, K):
    A = np.asarray(A, float); K = np.asarray(K, float)
    lam = np.full(len(A), np.nan)
    known = np.isfinite(K)
    pos = known & (A>0) & (K>0)
    zero = known & (A>0) & (K<=0)
    noreq = known & (A<=0)
    lam[pos] = np.minimum(1.0, K[pos]/A[pos])
    lam[zero] = 0.0
    lam[noreq] = 1.0
    return lam

for p in [POLY, LAND, MAP, BEH, HEAD, RATIO, UNRES]:
    need(p)

ratio_b, unres_b = coef(RATIO), coef(UNRES)
poly = pd.read_csv(POLY, dtype={"fips":"string"}, low_memory=False)
lb = pd.read_csv(LAND, dtype={"fips":"string"}, low_memory=False)
mp = pd.read_csv(MAP, low_memory=False)
beh = pd.read_csv(BEH, dtype={"fips":"string"}, low_memory=False)

rcol = "resource_canonical" if "resource_canonical" in poly else "resource"
poly["fips"] = fips(poly["fips"])
poly["land_type"] = land(poly["land_type"])
poly["resource_norm"] = poly[rcol].map(resource)
poly = poly.loc[poly["scenario_name"].isin(FAMILIES)].copy()
poly["allocation_family"] = poly["scenario_name"].map(FAMILIES)
poly["A_P"] = pd.to_numeric(poly["harvest_acres"], errors="raise")
poly["Q_P"] = pd.to_numeric(poly["production_dry_tons"], errors="raise")

map_resource = "polysys_resource_norm"
map_arch = "central_experimental_archetype"
poly = poly.merge(mp[[map_resource,map_arch]].rename(columns={map_resource:"resource_norm"}),
                  on="resource_norm", how="left", validate="m:1")
if poly[map_arch].isna().any():
    raise ValueError("Unmapped feedstock rows.")

lb["fips"] = fips(lb["fips"])
lb = lb.drop_duplicates("fips")

if "landsrce" not in beh:
    raise ValueError("Stage 07E Track B missing landsrce")
beh["fips"] = fips(beh["fips"])
beh["land_type"] = land(beh["landsrce"])
beh = beh.loc[beh["scenario_name"].isin(FAMILIES)].copy()
beh["allocation_family"] = beh["scenario_name"].map(FAMILIES)
for c in ["rent_multiplier","offer_2012usd_acre_year","contract_years",
          "participation_probability","conditional_share_central"]:
    beh[c] = pd.to_numeric(beh[c], errors="coerce")

svals = beh["conditional_share_central"].dropna().unique()
if len(svals) != 1:
    raise AssertionError("Central conditional acreage share is not constant.")
S = float(svals[0])

parts=[]
for spec in ["PRIMARY_LOG_DOLLAR","RATIO_ONLY","OFFER_PLUS_RENT"]:
    z=beh.copy()
    z["transport_spec"]=spec
    ok = z["participation_probability"].notna() & z["offer_2012usd_acre_year"].gt(0) & z["rent_multiplier"].gt(0)
    p=np.full(len(z),np.nan)
    if spec=="PRIMARY_LOG_DOLLAR":
        p[ok]=z.loc[ok,"participation_probability"].to_numpy(float)
    elif spec=="RATIO_ONLY":
        p[ok]=pred_ratio(z.loc[ok],ratio_b)
    else:
        p[ok]=pred_unres(z.loc[ok],unres_b)
    z["p_transport"]=p
    z["b_transport"]=p*S
    parts.append(z)
beh3=pd.concat(parts,ignore_index=True)

join = ["scenario_name","allocation_family","fips","land_type","experimental_feedstock"]
poly2 = poly.rename(columns={map_arch:"experimental_feedstock"})
expanded = beh3.merge(poly2[join+["A_P","Q_P"]],
                      on=join, how="left", validate="m:m")
if expanded[["A_P","Q_P"]].isna().any().any():
    raise ValueError("Behaviour-to-POLYSYS join failed.")

expanded["num"]=expanded["A_P"]*expanded["b_transport"]
keys=["transport_spec","compensation_scenario_id","rent_multiplier","contract_years",
      "scenario_name","allocation_family","fips","land_type"]
pool=(expanded.groupby(keys,dropna=False,as_index=False)
      .agg(A_P=("A_P","sum"),Q_P=("Q_P","sum"),num=("num","sum")))
miss=(expanded.assign(_miss=expanded["b_transport"].isna() & expanded["A_P"].gt(0))
      .groupby(keys,dropna=False,as_index=False)["_miss"].any())
pool=pool.merge(miss,on=keys,validate="1:1")
pool["kappa"]=np.where(pool["_miss"],np.nan,np.where(pool["A_P"]>0,pool["num"]/pool["A_P"],0))
pool=pool.drop(columns=["num","_miss"])
pool=pool.merge(lb[["fips","B_crop_equal_acres","B_pasture_equal_acres"]],
                on="fips",how="left",validate="m:1")
pool["B"]=np.where(pool["land_type"].eq("Crop"),
                   pd.to_numeric(pool["B_crop_equal_acres"],errors="coerce"),
                   pd.to_numeric(pool["B_pasture_equal_acres"],errors="coerce"))
pool["K"]=pool["B"]*pool["kappa"]
pool["lambda"]=capacity(pool["A_P"],pool["K"])
pool["Q_M_lower"]=np.where(pool["lambda"].notna(),pool["lambda"]*pool["Q_P"],0.0)
pool["Q_M_upper"]=np.where(pool["lambda"].notna(),pool["lambda"]*pool["Q_P"],pool["Q_P"])
pool["unmet_Q"]=pool["Q_P"]-pool["Q_M_lower"]
pool.to_csv(OUT/"county_land_transport_sensitivity.csv",index=False)

rows=[]
group=["transport_spec","compensation_scenario_id","rent_multiplier","contract_years",
       "scenario_name","allocation_family"]
for k,g in pool.groupby(group,dropna=False):
    q=float(g["Q_P"].sum()); lo=float(g["Q_M_lower"].sum()); hi=float(g["Q_M_upper"].sum())
    rows.append({**dict(zip(group,k)),"Q_P":q,"M_Q_full_lower":lo/q,"M_Q_full_upper":hi/q})
fam=pd.DataFrame(rows)
fam.to_csv(OUT/"national_transport_by_family.csv",index=False)
bal=(fam.groupby(["transport_spec","compensation_scenario_id","rent_multiplier","contract_years"],as_index=False)
     [["Q_P","M_Q_full_lower","M_Q_full_upper"]].mean())
bal["allocation_family"]="FAMILY_BALANCED"
bal.to_csv(OUT/"national_transport_family_balanced.csv",index=False)

# Reconcile primary to Stage 07G.
old=pd.read_csv(HEAD,low_memory=False)
old=old.loc[old["track"].eq("B_RENT_INDEXED")
            & old["behaviour_representation"].eq("CENTRAL_PRIMARY")
            & old["landbase_structure"].eq("JOINT_EQUAL")
            & old["scenario_name"].isin(FAMILIES),
            ["compensation_scenario_id","rent_multiplier","contract_years","scenario_name","M_Q_full_lower"]]
chk=fam.loc[fam["transport_spec"].eq("PRIMARY_LOG_DOLLAR"),
            ["compensation_scenario_id","rent_multiplier","contract_years","scenario_name","M_Q_full_lower"]].merge(
    old,on=["compensation_scenario_id","rent_multiplier","contract_years","scenario_name"],
    suffixes=("_new","_07G"),validate="1:1")
chk["difference"]=chk["M_Q_full_lower_new"]-chk["M_Q_full_lower_07G"]
chk.to_csv(OUT/"primary_reconciliation_to_07G.csv",index=False)
recon=float(chk["difference"].abs().max())
if recon>TOL:
    raise AssertionError(f"Primary transport fails Stage 07G reconciliation: {recon:.3e}")

# Crop/Pasture frontier, primary.
pri=pool.loc[pool["transport_spec"].eq("PRIMARY_LOG_DOLLAR")].copy()
rows=[]
gcols=["compensation_scenario_id","rent_multiplier","contract_years","allocation_family","land_type"]
for k,g in pri.groupby(gcols,dropna=False):
    q=float(g["Q_P"].sum()); lo=float(g["Q_M_lower"].sum()); hi=float(g["Q_M_upper"].sum())
    rows.append({**dict(zip(gcols,k)),"M_Q_full_lower":lo/q,"M_Q_full_upper":hi/q})
landfam=pd.DataFrame(rows)
landbal=(landfam.groupby(["compensation_scenario_id","rent_multiplier","contract_years","land_type"],as_index=False)
         [["M_Q_full_lower","M_Q_full_upper"]].mean())
landbal["allocation_family"]="FAMILY_BALANCED"
landbal.to_csv(OUT/"crop_pasture_frontier.csv",index=False)

# Crop/Pasture support exposure, production-weighted.
support=[]
for k,g in expanded.loc[expanded["transport_spec"].eq("PRIMARY_LOG_DOLLAR")].groupby(
    ["compensation_scenario_id","rent_multiplier","contract_years","allocation_family","land_type"],dropna=False):
    q=pd.to_numeric(g["Q_P"],errors="coerce").fillna(0); total=float(q.sum())
    r=dict(zip(["compensation_scenario_id","rent_multiplier","contract_years","allocation_family","land_type"],k))
    for cls,name in [("BELOW_SUPPORT","below"),("WITHIN_SUPPORT","within"),
                     ("ABOVE_SUPPORT","above"),("UNSUPPORTED_RENT","unsupported")]:
        r[name]=float(q[g["experimental_support_class"].eq(cls)].sum())/total if total else np.nan
    support.append(r)
sf=pd.DataFrame(support)
sb=(sf.groupby(["compensation_scenario_id","rent_multiplier","contract_years","land_type"],as_index=False)
    [["below","within","above","unsupported"]].mean())
sb["allocation_family"]="FAMILY_BALANCED"
sb.to_csv(OUT/"crop_pasture_support_exposure.csv",index=False)

# Support-balanced hotspot comparison using manuscript positive-unmet county convention.
hpool=pool.loc[pool["compensation_scenario_id"].eq(SB)&pool["contract_years"].eq(5)].copy()
cf=(hpool.groupby(["transport_spec","allocation_family","fips"],as_index=False)
    .agg(Q_P=("Q_P","sum"),Q_M=("Q_M_lower","sum"),A_P=("A_P","sum"),K=("K",lambda s:s.sum(min_count=1))))
cf["unmet_Q"]=cf["Q_P"]-cf["Q_M"]
cf["binding"]=(cf["A_P"]>cf["K"]).fillna(False)
cf.to_csv(OUT/"support_balanced_county_transport_by_family.csv",index=False)
ct=(cf.groupby(["transport_spec","fips"],as_index=False)
    .agg(family_presence=("allocation_family","nunique"),Q_P=("Q_P","mean"),
         Q_M=("Q_M","mean"),unmet_Q=("unmet_Q","mean"),binding=("binding","max")))
ct.to_csv(OUT/"support_balanced_county_transport_family_balanced.csv",index=False)

hot=[]
for spec,g in ct.groupby("transport_spec"):
    total=float(g["unmet_Q"].sum())
    st=g["fips"].astype(str).str.zfill(5).str[:2]
    positive=g.loc[g["unmet_Q"]>0].sort_values("unmet_Q",ascending=False)
    n=len(positive); nt=max(1,int(np.ceil(.10*n))) if n else 0
    hot.append({
        "transport_spec":spec,
        "unmet_Q_million_dt":total/1e6,
        "Texas_share_unmet_pct":100*float(g.loc[st.eq("48"),"unmet_Q"].sum())/total,
        "TX_OK_NM_share_unmet_pct":100*float(g.loc[st.isin(["48","40","35"]),"unmet_Q"].sum())/total,
        "positive_unmet_counties":n,
        "top10_positive_unmet_counties_n":nt,
        "top10pct_positive_unmet_counties_share_unmet_pct":100*float(positive.head(nt)["unmet_Q"].sum())/total,
        "binding_counties":int(g["binding"].sum()),
    })
hot=pd.DataFrame(hot)
hot.to_csv(OUT/"transport_hotspot_comparison.csv",index=False)

print("="*96)
print("BIOLAND-US | TRANSPORT ROBUSTNESS COMPLETE")
print("="*96)
print(f"PASS: PRIMARY transport reproduces Stage 07G; max |difference| = {recon:.3e}")
print(f"Central conditional share used: s = {S:.6f}\n")
print("Family-balanced support-balanced 5-year mobilization:")
print(bal.loc[bal["compensation_scenario_id"].eq(SB)&bal["contract_years"].eq(5),
              ["transport_spec","M_Q_full_lower","M_Q_full_upper"]].to_string(index=False))
print("\nHotspot comparison:")
print(hot.to_string(index=False))
print(f"\nOutputs written to: {OUT}")
