"""Draw the final BioLand-US five main figures plus Extended Data Figure 1.

The script is strictly read-only with respect to the reporting workbook.
All scientific arithmetic belongs upstream or in scripts/13_build_figure_workbook.py.
"""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Patch
import numpy as np
import pandas as pd


def load_geometry(root: Path):
    import geopandas as gpd
    cache = root / "results" / "figures" / "main" / "_geom_cache"
    candidates = list(cache.rglob("*CoUSAKHI*2022*.shp")) if cache.exists() else []
    candidates += list((root / "data" / "raw").rglob("*CoUSAKHI*2022*.shp"))
    zips = list((root / "data" / "raw").rglob("*CoUSAKHI*2022*.zip"))
    if not candidates and zips:
        cache.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zips[0]) as z:
            z.extractall(cache)
        candidates = list(cache.rglob("*.shp"))
    if not candidates:
        raise FileNotFoundError("County geometry not found.")
    geo = gpd.read_file(candidates[0])
    id_col = next((c for c in ("atlas_stco","GEOID","geoid") if c in geo.columns),None)
    if id_col is None:
        raise KeyError("County geometry has no recognized county identifier.")
    geo["fips"]=geo[id_col].astype(str).str.replace(r"\.0$","",regex=True).str.zfill(5)
    geo["statefp"]=geo["fips"].str[:2]
    geo=geo[~geo["statefp"].isin(["02","15","72"])].copy()
    return geo, geo.dissolve(by="statefp")


def styles(xls):
    C=pd.read_excel(xls,"Style_Guide").set_index("role")["hex"].to_dict()
    S=pd.read_excel(xls,"Style_Spec").set_index("setting")["value"].to_dict()
    mpl.rcParams.update({
        "font.family":"sans-serif",
        "font.sans-serif":["Arial","Helvetica","Nimbus Sans","Liberation Sans","DejaVu Sans"],
        "font.size":float(S.get("base_font_pt",6)),
        "axes.labelsize":float(S.get("base_font_pt",6)),
        "xtick.labelsize":float(S.get("base_font_pt",6))-0.5,
        "ytick.labelsize":float(S.get("base_font_pt",6))-0.5,
        "legend.fontsize":float(S.get("base_font_pt",6))-0.8,
        "axes.linewidth":float(S.get("axis_linewidth_pt",0.6)),
        "pdf.fonttype":42,"ps.fonttype":42,"svg.fonttype":"none",
        "axes.grid":False,"legend.frameon":False,
        "savefig.facecolor":"white","figure.facecolor":"white","axes.facecolor":"white",
    })
    return C,S


def clean(ax):
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

def letter(ax,s,dx=-0.14,dy=1.04):
    ax.text(dx,dy,s,transform=ax.transAxes,fontweight="bold",fontsize=8,va="top")

def save(fig,out,name,dpi):
    out.mkdir(parents=True,exist_ok=True)
    for ext in ("pdf","svg"):
        fig.savefig(out/f"{name}.{ext}",bbox_inches="tight")
    fig.savefig(out/f"{name}.png",dpi=dpi,bbox_inches="tight")
    plt.close(fig)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--workbook",type=Path,default=Path("results/figures/BioLandUS_FigureWorkbook_v7_FINAL.xlsx"))
    p.add_argument("--project-root",type=Path,default=Path.cwd())
    p.add_argument("--output",type=Path,default=Path("results/figures/main"))
    a=p.parse_args()

    xls=pd.ExcelFile(a.workbook)
    checks=pd.read_excel(xls,"Checks")
    if checks["status"].astype(str).eq("FAIL").any():
        raise RuntimeError("Reporting workbook contains failed reconciliation checks.")
    C,S=styles(xls); dpi=int(float(S.get("dpi_raster",600)))

    # ---------------------------------------------------------------- Figure 1
    part=pd.read_excel(xls,"F2Pa_Participation")
    f1b=pd.read_excel(xls,"F1Pb_ConditionalByOffer")
    access=pd.read_excel(xls,"F2Pc_Access")
    fig,axes=plt.subplots(1,3,figsize=(7.2,2.25))

    ax=axes[0]
    ax.plot(part.offer,part.smooth_pct,color=C.get("five_year","#0072B2"),marker="o",label="Smooth log-dollar transport")
    ax.scatter(part.offer,part.categorical_pct,facecolor="white",edgecolor="#222222",linewidth=.7,zorder=3,label="Categorical experimental margin")
    ax.set_xlabel(r"Annual land-rental offer (2012 US\$ acre$^{-1}$ yr$^{-1}$)")
    ax.set_ylabel("Predicted participation (%)"); ax.set_xticks(part.offer); clean(ax); letter(ax,"a")
    ax.legend(loc="upper left")

    ax=axes[1]
    y=f1b.margin_pct.to_numpy(float)
    lo=f1b.ci_low_pct.to_numpy(float); hi=f1b.ci_high_pct.to_numpy(float)
    ax.errorbar(f1b.offer,y,yerr=np.vstack([y-lo,hi-y]),fmt="o",color="#222222",capsize=2)
    national=float(f1b.national_constant_pct.iloc[0]); jp=float(f1b.joint_offer_p.iloc[0])
    ax.axhline(national,color="#777777",linestyle="--",linewidth=.8)
    ax.text(52,national+4,f"National constant {national:.1f}%",ha="left",color="#666666")
    ax.text(.97,.08,f"Joint offer p = {jp:.3f}",transform=ax.transAxes,ha="right",color="#666666")
    ax.set_xlabel(r"Annual land-rental offer (2012 US\$ acre$^{-1}$ yr$^{-1}$)")
    ax.set_ylabel("Conditional acreage share (%)"); ax.set_xticks(f1b.offer); ax.set_ylim(0,100)
    clean(ax); letter(ax,"b",dx=-0.22)

    ax=axes[2]
    y=access.b_mid_pct.to_numpy(float)
    ax.errorbar(access.offer,y,
                yerr=np.vstack([y-access.b_min_pct.to_numpy(float),access.b_max_pct.to_numpy(float)-y]),
                fmt="o",color=C.get("five_year","#0072B2"),capsize=2)
    ax.set_xlabel(r"Annual land-rental offer (2012 US\$ acre$^{-1}$ yr$^{-1}$)")
    ax.set_ylabel(r"Behavioural land access, $b=p\times s$ (%)")
    ax.set_xticks(access.offer); ax.set_ylim(0,None); clean(ax); letter(ax,"c")
    fig.tight_layout(w_pad=2.0)
    save(fig,a.output,"Figure1_Behaviour",dpi)

    # ---------------------------------------------------------------- Figure 2
    exp=pd.read_excel(xls,"F3Pa_ExperimentMQ")
    rent=pd.read_excel(xls,"F3Pb_RentIndexMQ")
    support=pd.read_excel(xls,"F3Pc_SupportExposure")
    conc=pd.read_excel(xls,"F3Pd_UnmetConcentration")
    nums=pd.read_excel(xls,"Numbers").set_index("key")["value"].to_dict()
    fig,axes=plt.subplots(2,2,figsize=(7.2,4.65))
    for ax,d,xcol,xlabel,ticks,islog,panel in [
        (axes[0,0],exp,"offer_2012usd_acre_year",r"Annual land-rental offer (2012 US\$ acre$^{-1}$ yr$^{-1}$)",[50,100,200,300],False,"a"),
        (axes[0,1],rent,"rent_multiplier",r"Rental-offer multiplier relative to local cash rent, $m$",[1,3.3544,6.7088,13.4175,20.1263],True,"b"),
    ]:
        d=d[d.contract_years.eq(5)]
        bal=d[d.allocation_family.eq("FAMILY_BALANCED")].sort_values(xcol)
        fam=d[d.allocation_family.isin(["FAMILY_01","FAMILY_02","FAMILY_03"])]
        flo=fam.groupby(xcol).p50_pct.min().sort_index()
        fhi=fam.groupby(xcol).p50_pct.max().reindex(flo.index)
        ax.fill_between(bal[xcol],bal.p025_pct,bal.p975_pct,color=C.get("statistical","#56B4E9"),alpha=.15)
        ax.fill_between(flo.index,flo.values,fhi.values,color="#808080",alpha=.22)
        ax.plot(bal[xcol],bal.p50_pct,color="#222222",marker="o")
        if islog:
            ax.set_xscale("log"); ax.minorticks_off()
            ax.axvline(6.7088,color="#777777",linestyle=":",linewidth=.7)
            ax.set_xticks(ticks); ax.set_xticklabels(["1","3.35","6.71","13.42","20.13"])
        else: ax.set_xticks(ticks)
        ax.set_xlabel(xlabel); ax.set_ylabel(r"Biomass mobilized, $M_Q$ (%)"); ax.set_ylim(0,105)
        clean(ax); letter(ax,panel)

    ax=axes[1,0]
    x=np.arange(len(support)); bottom=np.zeros(len(support))
    roles=[("below","support_below"),("within","support_within"),("above","support_above"),("unsupported","unsupported")]
    for col,role in roles:
        ax.bar(x,support[col],bottom=bottom,color=C.get(role,"#AAAAAA"),width=.66,label=col)
        bottom+=support[col].to_numpy(float)
    ax.set_xticks(x); ax.set_xticklabels(["1","3.35","6.71","13.42","20.13"])
    ax.set_xlabel(r"Rental-offer multiplier, $m$"); ax.set_ylabel("Production exposure (%)"); ax.set_ylim(0,100)
    clean(ax); letter(ax,"c")

    ax=axes[1,1]
    ax.plot(conc.county_share_pct,conc.cumulative_unmet_pct,color="#222222")
    ax.fill_between(conc.county_share_pct,0,conc.cumulative_unmet_pct,color="#D9D9D9",alpha=.4)
    top10=float(nums["unmet_top10pct_counties_share_pct"]); states=float(nums["unmet_share_TX_OK_NM_pct"])
    ax.axvline(10,color="#999999",linestyle=":",linewidth=.7); ax.scatter(10,top10,color="#B2182B",zorder=3)
    ax.annotate(f"Top 10% of positive-unmet counties\n= {top10:.1f}% of unmet biomass",xy=(10,top10),xytext=(18,top10-17),
                arrowprops=dict(arrowstyle="-",color="#777777",lw=.6))
    ax.text(.98,.07,f"TX + OK + NM = {states:.1f}% of unmet biomass",transform=ax.transAxes,ha="right")
    ax.set_xlabel("Counties ranked by unmet biomass (%)"); ax.set_ylabel("Cumulative national unmet biomass (%)")
    ax.set_xlim(0,100); ax.set_ylim(0,100); clean(ax); letter(ax,"d",dx=-.22)
    fig.tight_layout(h_pad=2.1,w_pad=1.7)
    save(fig,a.output,"Figure2_NationalMobilization",dpi)

    # ---------------------------------------------------------------- Figure 3
    ladder=pd.read_excel(xls,"F4_UncertaintyLadder")
    cover=pd.read_excel(xls,"F4_FeedstockCoverage")
    ladder=ladder[ladder.implemented.astype(str).str.lower().isin(["true","1"])].copy()
    fig,axes=plt.subplots(1,2,figsize=(7.2,2.55),gridspec_kw={"width_ratios":[1.7,1]})
    ax=axes[0]; y=np.arange(len(ladder))[::-1]
    role_cycle=[
        C.get("structural","#E69F00"),C.get("statistical","#0072B2"),
        C.get("support_within","#009E73"),C.get("ten_year","#CC79A7"),
        C.get("upstream_family","#7A8793"),C.get("contract_duration","#009E73")
    ]
    for yi,(_,r),color in zip(y,ladder.iterrows(),role_cycle):
        ax.plot([r.low_pct,r.high_pct],[yi,yi],color=color,linewidth=1.8)
        ax.scatter(r.central_pct,yi,color="#222222",zorder=3)
        ax.text(r.high_pct+.8,yi,f"{r.width_pp:.1f} pp",va="center",color="#555555")
    ax.axvline(float(ladder.iloc[0].central_pct),color="#CCCCCC",linewidth=.7)
    ax.set_yticks(y); ax.set_yticklabels([
        "Structural specification","Statistical bootstrap","Evidence-bounded extrapolation",
        "Rent-context transport","POLYSYS allocation family","Contract duration"
    ])
    ax.set_xlim(55,105); ax.set_xlabel(r"Biomass mobilized, $M_Q$ (%)"); clean(ax); letter(ax,"a")

    ax=axes[1]; x=np.arange(len(cover)); w=.36
    ax.bar(x-w/2,cover.harvest_pct,width=w,color=C.get("coverage_area","#0072B2"),label="Harvested acreage")
    ax.bar(x+w/2,cover.production_pct,width=w,color=C.get("coverage_production","#CC79A7"),label="Biomass production")
    ax.set_xticks(x); ax.set_xticklabels(cover.family_label); ax.set_ylim(0,100)
    ax.set_ylabel("Directly tested-species coverage (%)"); clean(ax); letter(ax,"b",dx=-.22)
    ax.legend(loc="upper center",bbox_to_anchor=(.5,-.18))
    fig.tight_layout(w_pad=2.2)
    save(fig,a.output,"Figure3_UncertaintyAndEvidence",dpi)

    # ---------------------------------------------------------------- maps
    geo,states=load_geometry(a.project_root)
    def base(ax):
        geo.plot(ax=ax,facecolor="#F2F2F2",edgecolor="white",linewidth=.08)
        states.boundary.plot(ax=ax,color="#808080",linewidth=.3)
        ax.set_axis_off(); ax.set_aspect("equal")

    # Figure 4
    mb=pd.read_excel(xls,"MapB_Unmet",dtype={"fips":str})
    mb["fips"]=mb.fips.astype(str).str.replace(r"\.0$","",regex=True).str.zfill(5)
    alloc_bins=[-np.inf,50,150,400,800,1500,np.inf]
    alloc_labels=["<50","50–150","150–400","400–800","800–1,500","≥1,500"]
    unmet_bins=[0,10,50,150,500,np.inf]
    unmet_labels=["<10","10–50","50–150","150–500","≥500"]
    mb["alloc_class"]=pd.cut(mb.Q_P_mean_kt,bins=alloc_bins,labels=alloc_labels,right=False)
    mb["unmet_class"]=pd.cut(mb.unmet_Q_mean_kt,bins=unmet_bins,labels=unmet_labels,right=False)
    mb.loc[mb.unmet_Q_mean_kt.eq(0),"unmet_class"]="Fully mobilized"
    blues=["#EFF3FF","#C6DBEF","#9ECAE1","#6BAED6","#3182BD","#08519C"]
    reds={"Fully mobilized":"#F2F2F2","<10":"#FEE5D9","10–50":"#FCBBA1","50–150":"#FC9272","150–500":"#EF3B2C","≥500":"#99000D"}
    fig,axes=plt.subplots(1,2,figsize=(10.5,3.6))
    for ax in axes: base(ax)
    m=geo.merge(mb[["fips","alloc_class"]],on="fips",how="left")
    for lab,col in zip(alloc_labels,blues):
        m[m.alloc_class.astype(str).eq(lab)].plot(ax=axes[0],facecolor=col,edgecolor="white",linewidth=.05)
    axes[0].legend(handles=[Patch(facecolor=c,label=l) for l,c in zip(alloc_labels,blues)]+[Patch(facecolor="#F2F2F2",label="No retained allocation")],
                   title="Mean across families (thousand dry tons)",loc="lower left",ncol=2,fontsize=5,title_fontsize=5)
    letter(axes[0],"a",dx=-.05,dy=1.02)

    m=geo.merge(mb[["fips","unmet_class"]],on="fips",how="left")
    for lab,col in reds.items():
        m[m.unmet_class.astype(str).eq(lab)].plot(ax=axes[1],facecolor=col,edgecolor="white",linewidth=.05)
    axes[1].legend(handles=[Patch(facecolor=c,label=l) for l,c in reds.items()]+[Patch(facecolor="#F2F2F2",label="No retained allocation")],
                   title="Mean across families (thousand dry tons)",loc="lower left",ncol=2,fontsize=5,title_fontsize=5)
    letter(axes[1],"b",dx=-.05,dy=1.02)
    fig.tight_layout(w_pad=.6)
    save(fig,a.output,"Figure4_AllocationAndUnmetBiomass",dpi)

    # Figure 5
    pressure=pd.read_excel(xls,"MapA_Pressure",dtype={"fips":str})
    consensus=pd.read_excel(xls,"MapC_Consensus",dtype={"fips":str})
    for d in (pressure,consensus):
        d["fips"]=d.fips.astype(str).str.replace(r"\.0$","",regex=True).str.zfill(5)
    fig,axes=plt.subplots(2,2,figsize=(7.2,4.6))
    for ax in axes.flat: base(ax)
    cls=[("lt_05","#2166AC",r"$\rho<0.5$"),("c05_1","#92C5DE",r"$0.5\leq\rho<1$"),
         ("c1_2","#F4A582",r"$1\leq\rho<2$"),("ge_2","#B2182B",r"$\rho\geq2$"),
         ("undefined","#555555","Capacity undefined")]
    m=geo.merge(pressure[["fips","display_class"]],on="fips",how="left")
    for k,col,_ in cls:
        m[m.display_class.eq(k)].plot(ax=axes[0,0],facecolor=col,edgecolor="white",linewidth=.05)
    axes[0,0].legend(handles=[Patch(facecolor=c,label=l) for _,c,l in cls]+[Patch(facecolor="#F2F2F2",label="No retained allocation")],
                     loc="lower left",ncol=2,fontsize=5)
    letter(axes[0,0],"a",dx=-.05)

    bindcol="P_bind"; topcol="P_top10" if "P_top10" in consensus else "P_top10_risk"
    cmap=LinearSegmentedColormap.from_list("bind",["#F7FBFF","#08519C"])
    m=geo.merge(consensus[["fips",bindcol]],on="fips",how="left")
    m.plot(column=bindcol,ax=axes[0,1],cmap=cmap,vmin=0,vmax=1,edgecolor="white",linewidth=.04)
    cb=fig.colorbar(mpl.cm.ScalarMappable(norm=Normalize(0,1),cmap=cmap),ax=axes[0,1],fraction=.028,pad=.01)
    cb.set_label(r"$P(\mathrm{binding})$"); letter(axes[0,1],"b",dx=-.05)

    cmap2=LinearSegmentedColormap.from_list("top",["#FCFBFD","#54278F"])
    m=geo.merge(consensus[["fips",topcol]],on="fips",how="left")
    m.plot(column=topcol,ax=axes[1,0],cmap=cmap2,vmin=0,vmax=1,edgecolor="white",linewidth=.04)
    cb=fig.colorbar(mpl.cm.ScalarMappable(norm=Normalize(0,1),cmap=cmap2),ax=axes[1,0],fraction=.028,pad=.01)
    cb.set_label(r"$P(\mathrm{Top\ 10\%\ risk})$"); letter(axes[1,0],"c",dx=-.05)

    items=[("h0","#EFEDF5","0/3"),("h1","#DADAEB","1/3"),("h2","#9E9AC8","2/3"),("h3","#54278F","3/3"),
           ("incomplete_families","#BDBDBD","<3 families")]
    m=geo.merge(consensus[["fips","display_class"]],on="fips",how="left")
    for k,col,_ in items:
        m[m.display_class.eq(k)].plot(ax=axes[1,1],facecolor=col,edgecolor="white",linewidth=.05)
    axes[1,1].legend(handles=[Patch(facecolor=c,label=l) for _,c,l in items]+[Patch(facecolor="#F2F2F2",label="No retained allocation")],
                     title="Independent POLYSYS families identifying robust hotspot",loc="lower left",ncol=3,fontsize=4.7,title_fontsize=5)
    letter(axes[1,1],"d",dx=-.05)
    fig.tight_layout(h_pad=.7,w_pad=.7)
    save(fig,a.output,"Figure5_SpatialRobustness",dpi)

    # ------------------------------------------------------- Extended Data Fig. 1
    fr=pd.read_excel(xls,"ED1_CropPastureFrontier")
    se=pd.read_excel(xls,"ED1_CropPastureSupport")
    fr=fr[fr.contract_years.eq(5)].sort_values(["land_type","rent_multiplier"])
    se=se[se.contract_years.eq(5)].sort_values(["land_type","rent_multiplier"])
    fig,axes=plt.subplots(1,2,figsize=(7.2,2.6))
    ax=axes[0]
    for land_type,marker in [("Crop","o"),("Pasture","s")]:
        d=fr[fr.land_type.eq(land_type)]
        ax.plot(d.rent_multiplier,100*d.M_Q_full_lower,marker=marker,label=land_type)
    ax.set_xscale("log"); ax.set_xticks([1,3.3544,6.7088,13.4175,20.1263]); ax.set_xticklabels(["1","3.35","6.71","13.42","20.13"])
    ax.axvline(6.7088,color="#999999",linestyle=":",linewidth=.7)
    ax.set_xlabel(r"Rental-offer multiplier, $m$"); ax.set_ylabel(r"Biomass mobilized, $M_Q$ (%)")
    ax.set_ylim(0,105); clean(ax); letter(ax,"a"); ax.legend()

    ax=axes[1]; mult=[1,3.3544,6.7088,13.4175,20.1263]; x=np.arange(len(mult)); width=.36
    support_colors={"below":"#56B4E9","within":"#009E73","above":"#E69F00","unsupported":"#999999"}
    for offset,land_type in [(-width/2,"Crop"),(width/2,"Pasture")]:
        d=se[se.land_type.eq(land_type)].set_index("rent_multiplier").reindex(mult)
        bottom=np.zeros(len(mult))
        for col in ["below","within","above","unsupported"]:
            vals=100*d[col].to_numpy(float)
            ax.bar(x+offset,vals,width=width,bottom=bottom,color=support_colors[col],
                   edgecolor="white",linewidth=.2,label=col if land_type=="Crop" else None)
            bottom+=vals
    ax.set_xticks(x); ax.set_xticklabels(["1","3.35","6.71","13.42","20.13"])
    ax.set_xlabel(r"Rental-offer multiplier, $m$"); ax.set_ylabel("Production exposure (%)"); ax.set_ylim(0,100)
    clean(ax); letter(ax,"b"); ax.legend(loc="upper center",bbox_to_anchor=(.5,-.18),ncol=2,title="Support class")
    fig.tight_layout(w_pad=1.8)
    save(fig,a.output,"ExtendedData_Figure1_CropPasture",dpi)

    print("PASS: final read-only figure suite written")
    print(a.output)

if __name__=="__main__":
    main()
