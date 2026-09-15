"""Evidence-bounded extrapolation sensitivity for BioLand-US rent-indexed land-rental offers.

Outside the randomized $50-$300/acre/year range, impose only monotonicity:
below $50: p in [0,p(50)]
inside support: p_lower=p_primary=p_upper
above $300: p in [p(300),1]

Boundary probabilities are stratum-specific by duration, land type and experimental
feedstock. Frozen T1 capacity, POLYSYS allocation and central conditional acreage are unchanged.
"""
from __future__ import annotations

import os
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(os.environ.get("BIOLAND_PROJECT",Path.cwd()))
D=ROOT/"data"; OUT=ROOT/"results"/"support_bounded_extrapolation"; OUT.mkdir(parents=True,exist_ok=True)
POLY=D/"frozen"/"public"/"POLYSYS_PerennialAllocation_2041_70dt.csv"
LAND=D/"frozen"/"public"/"Census2022_County_CropPasture_LandBase_JOINT_STRUCTURAL.csv"
MAP=D/"frozen"/"public"/"BioLandUS_FeedstockTransfer_07E1_FROZEN.csv"
A=D/"interim"/"BioLandUS_07E_ExperimentAnchoredBehaviouralAccess.csv"
B=D/"interim"/"BioLandUS_07E_RentIndexedBehaviouralAccess.csv"
FAM={"emerging":"FAMILY_01","mature-market low":"FAMILY_02","mature-market medium":"FAMILY_03"}
SB="SUPPORT_BALANCED_REFERENCE"; LO=50.; HI=300.; TOL=1e-12

def need(p):
    if not p.exists(): raise FileNotFoundError(p)
def zf(s): return s.astype("string").str.replace(r"\.0$","",regex=True).str.zfill(5)
def nl(s): return s.astype("string").str.strip().str.lower().map({"crop":"Crop","pasture":"Pasture"})
def nr(x): return " ".join(str(x).strip().lower().replace("_"," ").replace("-"," ").split())
def lam(A,K):
    A=np.asarray(A,float); K=np.asarray(K,float); o=np.full(len(A),np.nan)
    known=np.isfinite(K); pos=known&(A>0)&(K>0); zero=known&(A>0)&(K<=0); noreq=known&(A<=0)
    o[pos]=np.minimum(1,K[pos]/A[pos]); o[zero]=0; o[noreq]=1
    return o
for p in [POLY,LAND,MAP,A,B]: need(p)

# Experimental boundary probabilities.
a=pd.read_csv(A,low_memory=False)
a["land_type"]=nl(a["land_type"])
for c in ["offer_2012usd_acre_year","contract_years","participation_probability","conditional_share_central"]:
    a[c]=pd.to_numeric(a[c],errors="raise")
s=a["conditional_share_central"].dropna().unique()
if len(s)!=1: raise AssertionError("Central conditional share is not constant")
S=float(s[0])
strata=["contract_years","land_type","experimental_feedstock"]
q=a.loc[a["offer_2012usd_acre_year"].isin([LO,HI])]
check=q.groupby(strata+["offer_2012usd_acre_year"])["participation_probability"].agg(["min","max"])
if ((check["max"]-check["min"]).abs()>TOL).any(): raise AssertionError("Boundary probabilities differ within stratum")
boundary=(q.groupby(strata+["offer_2012usd_acre_year"],as_index=False)["participation_probability"].first()
          .pivot(index=strata,columns="offer_2012usd_acre_year",values="participation_probability")
          .reset_index().rename(columns={LO:"p_at_50",HI:"p_at_300"}))
if boundary[["p_at_50","p_at_300"]].isna().any().any(): raise AssertionError("Missing boundaries")
boundary.to_csv(OUT/"behavioural_boundary_probabilities.csv",index=False)

# Track B evidence bounds.
b=pd.read_csv(B,dtype={"fips":"string"},low_memory=False)
b["fips"]=zf(b["fips"]); b["land_type"]=nl(b["landsrce"])
b=b.loc[b["scenario_name"].isin(FAM)].copy(); b["allocation_family"]=b["scenario_name"].map(FAM)
for c in ["rent_multiplier","offer_2012usd_acre_year","contract_years","participation_probability","conditional_share_central"]:
    b[c]=pd.to_numeric(b[c],errors="coerce")
b=b.merge(boundary,on=strata,how="left",validate="m:1")
support=b["experimental_support_class"].astype("string"); primary=b["participation_probability"]
plo=np.full(len(b),np.nan); phi=np.full(len(b),np.nan)
within=support.eq("WITHIN_SUPPORT")&primary.notna()
below=support.eq("BELOW_SUPPORT")&primary.notna()
above=support.eq("ABOVE_SUPPORT")&primary.notna()
plo[within]=primary[within]; phi[within]=primary[within]
plo[below]=0; phi[below]=b.loc[below,"p_at_50"]
plo[above]=b.loc[above,"p_at_300"]; phi[above]=1
if np.any(np.isfinite(plo)&np.isfinite(phi)&(plo>phi+TOL)): raise AssertionError("Invalid bounds")
b["p_evidence_lower"]=plo; b["p_primary"]=primary; b["p_evidence_upper"]=phi
for tag in ["evidence_lower","primary","evidence_upper"]:
    b["b_"+tag]=b["p_"+tag]*S
b.to_csv(OUT/"rent_indexed_behavioural_evidence_bounds.csv",index=False)

# Frozen POLYSYS and land.
poly=pd.read_csv(POLY,dtype={"fips":"string"},low_memory=False)
lb=pd.read_csv(LAND,dtype={"fips":"string"},low_memory=False)
mp=pd.read_csv(MAP,low_memory=False)
rcol="resource_canonical" if "resource_canonical" in poly else "resource"
poly["fips"]=zf(poly["fips"]); poly["land_type"]=nl(poly["land_type"]); poly["resource_norm"]=poly[rcol].map(nr)
poly=poly.loc[poly["scenario_name"].isin(FAM)].copy(); poly["allocation_family"]=poly["scenario_name"].map(FAM)
poly["A_P"]=pd.to_numeric(poly["harvest_acres"],errors="raise"); poly["Q_P"]=pd.to_numeric(poly["production_dry_tons"],errors="raise")
poly=poly.merge(mp[["polysys_resource_norm","central_experimental_archetype"]].rename(
    columns={"polysys_resource_norm":"resource_norm","central_experimental_archetype":"experimental_feedstock"}),
    on="resource_norm",how="left",validate="m:1")
lb["fips"]=zf(lb["fips"]); lb=lb.drop_duplicates("fips")

join=["scenario_name","allocation_family","fips","land_type","experimental_feedstock"]
x=b.merge(poly[join+["A_P","Q_P"]],on=join,how="left",validate="m:m")
if x[["A_P","Q_P"]].isna().any().any(): raise ValueError("Behaviour-to-POLYSYS join failed")

# Pool all three behavioural bounds through T1.
g=["compensation_scenario_id","rent_multiplier","contract_years","scenario_name","allocation_family","fips","land_type"]
pools=[]
for tag in ["evidence_lower","primary","evidence_upper"]:
    z=x.copy(); z["num"]=z["A_P"]*z["b_"+tag]
    p=(z.groupby(g,dropna=False,as_index=False).agg(A_P=("A_P","sum"),Q_P=("Q_P","sum"),num=("num","sum")))
    m=(z.assign(_miss=z["b_"+tag].isna()&z["A_P"].gt(0)).groupby(g,dropna=False,as_index=False)["_miss"].any())
    p=p.merge(m,on=g,validate="1:1")
    p["kappa"]=np.where(p["_miss"],np.nan,np.where(p["A_P"]>0,p["num"]/p["A_P"],0))
    p["bound"]=tag; pools.append(p.drop(columns=["num","_miss"]))
pool=pd.concat(pools,ignore_index=True)
pool=pool.merge(lb[["fips","B_crop_equal_acres","B_pasture_equal_acres"]],on="fips",how="left",validate="m:1")
pool["B"]=np.where(pool["land_type"].eq("Crop"),pool["B_crop_equal_acres"],pool["B_pasture_equal_acres"])
pool["K"]=pool["B"]*pool["kappa"]; pool["lambda"]=lam(pool["A_P"],pool["K"])
pool["Q_M_lower"]=np.where(pool["lambda"].notna(),pool["lambda"]*pool["Q_P"],0)
pool["Q_M_upper"]=np.where(pool["lambda"].notna(),pool["lambda"]*pool["Q_P"],pool["Q_P"])
pool.to_csv(OUT/"county_land_support_bounded_mobilization.csv",index=False)

# National family and family-balanced summaries.
rows=[]
for k,h in pool.groupby(["bound","compensation_scenario_id","rent_multiplier","contract_years","allocation_family"],dropna=False):
    q=float(h["Q_P"].sum()); qlo=float(h["Q_M_lower"].sum()); qhi=float(h["Q_M_upper"].sum())
    rows.append({**dict(zip(["bound","compensation_scenario_id","rent_multiplier","contract_years","allocation_family"],k)),
                 "M_Q_full_lower":qlo/q,"M_Q_full_upper":qhi/q})
nf=pd.DataFrame(rows); nf.to_csv(OUT/"national_support_bounds_by_family.csv",index=False)
nb=(nf.groupby(["bound","compensation_scenario_id","rent_multiplier","contract_years"],as_index=False)
    [["M_Q_full_lower","M_Q_full_upper"]].mean())
nb["allocation_family"]="FAMILY_BALANCED"
nb.to_csv(OUT/"national_support_bounds_family_balanced.csv",index=False)

# Compact interval table.
wide=nb.pivot_table(index=["compensation_scenario_id","rent_multiplier","contract_years"],
                    columns="bound",values=["M_Q_full_lower","M_Q_full_upper"]).reset_index()
wide.columns=["_".join([str(x) for x in c if str(x)!=""]).rstrip("_") if isinstance(c,tuple) else c for c in wide.columns]
interval=pd.DataFrame({
    "compensation_scenario_id":wide["compensation_scenario_id"],
    "rent_multiplier":wide["rent_multiplier"],
    "contract_years":wide["contract_years"],
    "M_Q_evidence_lower":wide["M_Q_full_lower_evidence_lower"],
    "M_Q_primary_point_lower":wide["M_Q_full_lower_primary"],
    "M_Q_primary_point_upper":wide["M_Q_full_upper_primary"],
    "M_Q_evidence_upper":wide["M_Q_full_upper_evidence_upper"],
})
interval["evidence_width_pp"]=100*(interval["M_Q_evidence_upper"]-interval["M_Q_evidence_lower"])
interval.to_csv(OUT/"national_support_bounded_interval.csv",index=False)

# Crop/Pasture support-bounded result.
cp=[]
for k,h in pool.groupby(["bound","compensation_scenario_id","rent_multiplier","contract_years","allocation_family","land_type"],dropna=False):
    q=float(h["Q_P"].sum()); qlo=float(h["Q_M_lower"].sum()); qhi=float(h["Q_M_upper"].sum())
    cp.append({**dict(zip(["bound","compensation_scenario_id","rent_multiplier","contract_years","allocation_family","land_type"],k)),
               "M_Q_full_lower":qlo/q,"M_Q_full_upper":qhi/q})
cp=pd.DataFrame(cp)
cpb=(cp.groupby(["bound","compensation_scenario_id","rent_multiplier","contract_years","land_type"],as_index=False)
     [["M_Q_full_lower","M_Q_full_upper"]].mean())
cpb["allocation_family"]="FAMILY_BALANCED"; cpb.to_csv(OUT/"crop_pasture_support_bounds.csv",index=False)

r=interval.loc[interval["compensation_scenario_id"].eq(SB)&interval["contract_years"].eq(5)]
print("="*96)
print("BIOLAND-US | EVIDENCE-BOUNDED EXTRAPOLATION SENSITIVITY")
print("="*96)
print(f"Frozen central conditional share: s = {S:.6f}")
print("Tail rule: below $50 -> p in [0,p(50)]; above $300 -> p in [p(300),1].")
print("Within-support participation remains the frozen primary Stage 07E prediction.\n")
print("Support-balanced 5-year family-balanced result:")
print(r[["rent_multiplier","M_Q_evidence_lower","M_Q_primary_point_lower",
         "M_Q_primary_point_upper","M_Q_evidence_upper","evidence_width_pp"]].to_string(index=False))
print(f"\nOutputs written to: {OUT}")
