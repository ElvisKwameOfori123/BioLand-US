"""Draw the manuscript figures directly from the pipeline's result CSVs.

Main text (results/figures/main): Fig1 framework, Fig2 the two gates, Fig3 geography,
Fig4 uncertainty. Supplement (results/figures/supplementary): FigS1-S6.

Read-only: no model arithmetic happens here. The only operations are selecting
rows and averaging county values over the three independent POLYSYS families
for the maps. Colours follow the reference data-viz palette (categorical slots
in fixed order, one-hue sequential ramps, blue-red diverging around rho = 1).

Outputs: PDF and 300-dpi PNG for every figure.
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap, ListedColormap
from matplotlib.patches import Patch

INK, INK2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
SURFACE, EMPTY = "#fcfcfb", "#f0efec"
SLOT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]          # categorical, fixed order
BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
ORANGE = ["#fde3d6", "#f9b99b", "#f39168", "#eb6834", "#c94f1f", "#9c3a14", "#6e280d"]
DIVERGING = {"lt_05": "#256abf", "c05_1": "#9ec5f4", "c1_2": "#f2a3a2", "ge_2": "#e34948",
             "zero_capacity": "#8c1f1f", "unresolved": "#c3c2b7"}
MI_COUNTIES = {"26005": "Allegan", "26015": "Barry", "26023": "Branch", "26067": "Ionia", "26073": "Isabella",
               "26091": "Lenawee", "26093": "Livingston", "26123": "Newaygo", "26145": "Saginaw",
               "26151": "Sanilac", "26157": "Tuscola", "26159": "Van Buren"}
STATE_NAMES = {"01": "Alabama", "04": "Arizona", "05": "Arkansas", "06": "California", "08": "Colorado",
               "09": "Connecticut", "10": "Delaware", "12": "Florida", "13": "Georgia", "16": "Idaho", "17": "Illinois",
               "18": "Indiana", "19": "Iowa", "20": "Kansas", "21": "Kentucky", "22": "Louisiana", "23": "Maine",
               "24": "Maryland", "25": "Massachusetts", "26": "Michigan", "27": "Minnesota", "28": "Mississippi",
               "29": "Missouri", "30": "Montana", "31": "Nebraska", "32": "Nevada", "33": "New Hampshire",
               "34": "New Jersey", "35": "New Mexico", "36": "New York", "37": "North Carolina", "38": "North Dakota",
               "39": "Ohio", "40": "Oklahoma", "41": "Oregon", "42": "Pennsylvania", "44": "Rhode Island",
               "45": "South Carolina", "46": "South Dakota", "47": "Tennessee", "48": "Texas", "49": "Utah",
               "50": "Vermont", "51": "Virginia", "53": "Washington", "54": "West Virginia", "55": "Wisconsin",
               "56": "Wyoming"}
MULTIPLIER_TICKS = [1.0, 3.3544, 6.7088, 13.4175, 20.1263]
HEADLINE = "SUPPORT_BALANCED_REFERENCE"
SOUTHERN_PLAINS = {"48", "40", "35"}


def style() -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Segoe UI", "DejaVu Sans"],
        "font.size": 6.5, "axes.labelsize": 6.5, "xtick.labelsize": 6, "ytick.labelsize": 6,
        "legend.fontsize": 6, "axes.titlesize": 7,
        "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
        "text.color": INK, "axes.linewidth": 0.6, "lines.linewidth": 1.4,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.4, "axes.axisbelow": True,
        "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
        "pdf.fonttype": 42, "svg.fonttype": "none",
    })


def letter(ax, s: str, dx: float = -0.16, dy: float = 1.06) -> None:
    ax.text(dx, dy, s, transform=ax.transAxes, fontweight="bold", fontsize=8, va="top", color=INK)


def save(fig, out: Path, name: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(out / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def pct(ax, axis: str = "y") -> None:
    fmt = mpl.ticker.FuncFormatter(lambda v, _: f"{100 * v:.0f}%")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


def multiplier_axis(ax) -> None:
    ax.set_xscale("log")
    ax.minorticks_off()
    ax.set_xticks(MULTIPLIER_TICKS)
    ax.set_xticklabels(["1", "3.35", "6.71", "13.4", "20.1"])
    ax.set_xlabel("Offer as a multiple of local cash rent, m")


# ----------------------------------------------------------------------------- Figure 1
def figure1(R: Path, out: Path) -> None:
    curve = pd.read_csv(R / "behaviour/participation_curve.csv")
    knots = pd.read_csv(R / "behaviour/participation_margins.csv")
    share = pd.read_csv(R / "behaviour/conditional_acreage_parameters.csv")
    coef = pd.read_csv(R / "behaviour/participation_coefficients.csv")

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.3), gridspec_kw={"width_ratios": [1.15, 1, 1]})

    ax = axes[0]
    ax.fill_between(curve["offer"], curve["ll"], curve["ul"], color=SLOT[0], alpha=0.15, linewidth=0)
    ax.plot(curve["offer"], curve["p_smooth"], color=SLOT[0], label="Smooth ln(offer) model")
    ax.errorbar(knots["offer"], knots["p_categorical"],
                yerr=[knots["p_categorical"] - knots["ll_categorical"], knots["ul_categorical"] - knots["p_categorical"]],
                fmt="o", ms=4, color=INK, mfc="white", mew=0.8, elinewidth=0.7, capsize=0,
                label="Randomized offer (categorical)", zorder=3)
    ax.set_xticks([50, 100, 200, 300])
    ax.set_xlabel("Annual offer (2012 US$ per acre)")
    ax.set_ylabel("Participation probability")
    ax.set_ylim(0, 0.55)
    pct(ax)
    ax.legend(loc="upper left")
    letter(ax, "a")

    ax = axes[1]
    order = ["LOWER_DATA_QUALITY", "EXACT_CASE_MEAN", "CENTRAL_IPW_ROBUSTNESS", "CENTRAL_PRIMARY", "UPPER_DATA_QUALITY"]
    labels = ["Lower bound", "Exact cases", "IPW central", "Central", "Upper bound"]
    y = np.arange(len(order))[::-1]
    for (weighting, color, marker, off, lab) in [("per_choice", SLOT[0], "o", 0.13, "Per choice"),
                                                 ("acreage", SLOT[1], "s", -0.13, "Acreage-weighted")]:
        d = share.loc[share["weighting"].eq(weighting)].set_index("representation").reindex(order)
        ok = d["share"].notna().to_numpy()
        ax.scatter(d["share"][ok], (y + off)[ok], color=color, marker=marker, s=16, label=lab, zorder=3,
                   edgecolor=SURFACE, linewidth=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlim(0.55, 1.0)
    ax.grid(axis="y", visible=False)
    pct(ax, "x")
    ax.set_xlabel("Share of eligible acres enrolled, s")
    ax.legend(loc="upper right")
    letter(ax, "b", dx=-0.42)

    ax = axes[2]
    full = coef.loc[coef["model"].eq("SMOOTH") & coef["term"].eq("ln_offer")].iloc[0]
    loco = coef.loc[coef["model"].str.startswith("LOCO_") & coef["term"].eq("ln_offer")].copy()
    loco["county"] = loco["model"].str.replace("LOCO_", "", regex=False)
    loco = loco.sort_values("b")
    yy = np.arange(len(loco))
    ax.axvspan(full["b"] - 1.96 * full["se"], full["b"] + 1.96 * full["se"], color=SLOT[0], alpha=0.12, linewidth=0)
    ax.axvline(full["b"], color=SLOT[0], linewidth=1)
    ax.scatter(loco["b"], yy, color=INK, s=10, zorder=3)
    ax.set_yticks(yy)
    ax.set_yticklabels(loco["county"].map(MI_COUNTIES), fontsize=5.5)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("ln(offer) coefficient")
    ax.set_ylabel("Survey county left out")
    ax.text(full["b"], len(loco) - 0.2, f"  all counties {full['b']:.2f}", color=INK2, va="bottom", fontsize=5.5)
    letter(ax, "c", dx=-0.32)

    fig.tight_layout(w_pad=1.6)
    save(fig, out / "supplementary", "FigS1_BehaviourDetail")


# ----------------------------------------------------------------------------- Figure 2
def national_panel(ax, det, head, track, xcol, scen_x, bounds=None):
    d = det.loc[det["track"].eq(track) & det["contract_years"].eq(5)].copy()
    d["x"] = d["scenario_id"].map(scen_x)
    fam = d.loc[d["allocation_family"].ne("FAMILY_BALANCED")].groupby("x")["M_Q_full_lower"].agg(["min", "max"])
    h = head.loc[head["track"].eq(track) & head["contract_years"].eq(5)].copy()
    h["x"] = h["scenario_id"].map(scen_x)
    h = h.sort_values("x")
    ax.fill_between(h["x"], h["M_Q_boot_p025"], h["M_Q_boot_p975"], color=SLOT[0], alpha=0.15, linewidth=0,
                    label="Bootstrap 95%")
    ax.vlines(fam.index, fam["min"], fam["max"], color=INK2, linewidth=2.2, label="Allocation-family range")
    if bounds is not None:
        ax.plot(h["x"], h["M_Q_evidence_lower"], color=SLOT[1], linestyle="--", linewidth=1, label="Evidence bounds")
        ax.plot(h["x"], h["M_Q_evidence_upper"], color=SLOT[1], linestyle="--", linewidth=1)
    ax.plot(h["x"], h["M_Q_central"], color=SLOT[0], marker="o", ms=4, mec=SURFACE, mew=0.6, label="Central")
    ax.set_ylim(0, 1.02)
    ax.set_ylabel("Biomass mobilized, M_Q")
    pct(ax)


def figure2(R: Path, out: Path) -> None:
    det = pd.read_csv(R / "deterministic/national_mobilization.csv")
    head = pd.read_csv(R / "manuscript/headline_results.csv")
    scen = pd.read_csv(R / "deterministic/compensation_scenarios.csv")
    exposure = pd.read_csv(R / "robustness/support_exposure.csv")
    county = pd.read_csv(R / "spatial/county_spatial_robustness.csv", dtype={"fips": "string"})

    fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.7))

    ax = axes[0, 0]
    national_panel(ax, det, head, "A_EXPERIMENT_ANCHORED", "offer",
                   {f"EXP_ABS_{o}": o for o in (50, 100, 200, 300)})
    ax.set_xticks([50, 100, 200, 300])
    ax.set_xlabel("Uniform national offer (2012 US$ per acre)")
    ax.legend(loc="lower right")
    letter(ax, "a")

    ax = axes[0, 1]
    mx = dict(zip(scen["scenario_id"], scen["rent_multiplier"]))
    national_panel(ax, det, head, "B_RENT_INDEXED", "m", mx, bounds=True)
    multiplier_axis(ax)
    ax.axvline(mx[HEADLINE], color=MUTED, linestyle=":", linewidth=0.8)
    ax.legend(loc="lower right")
    letter(ax, "b")

    ax = axes[1, 0]
    e = exposure.loc[exposure["land_type"].eq("All")]
    e = e.assign(m=e["rent_multiplier"].round(4)).groupby(["m", "support"])["acre_share"].mean().unstack()
    e = e.reindex(MULTIPLIER_TICKS)
    classes = [("BELOW_SUPPORT", "Below $50", SLOT[1]), ("WITHIN_SUPPORT", "$50–300 (tested)", SLOT[0]),
               ("ABOVE_SUPPORT", "Above $300", SLOT[2]), ("UNSUPPORTED_RENT", "No rent context", MUTED)]
    x = np.arange(len(e))
    bottom = np.zeros(len(e))
    for key, lab, col in classes:
        v = e.get(key, pd.Series(0.0, index=e.index)).fillna(0).to_numpy()
        ax.bar(x, v, bottom=bottom, color=col, width=0.62, edgecolor=SURFACE, linewidth=1, label=lab)
        bottom += v
    ax.set_xticks(x)
    ax.set_xticklabels(["1", "3.35", "6.71", "13.4", "20.1"])
    ax.set_xlabel("Offer as a multiple of local cash rent, m")
    ax.set_ylabel("Share of POLYSYS acres by offer level")
    ax.set_ylim(0, 1)
    ax.grid(axis="x", visible=False)
    pct(ax)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
    letter(ax, "c")

    ax = axes[1, 1]
    c = county.loc[county["contract_years"].eq(5)].groupby("fips")["unmet_Q_central"].sum() / 3
    c = c[c > 0].sort_values(ascending=False)
    cum = c.cumsum() / c.sum()
    xs = np.arange(1, len(c) + 1) / len(c)
    ax.plot(xs, cum.to_numpy(), color=SLOT[0])
    top = float(cum.iloc[int(np.ceil(0.1 * len(c))) - 1])
    plains = float(c[c.index.str[:2].isin(SOUTHERN_PLAINS)].sum() / c.sum())
    ax.scatter([0.1], [top], color=SLOT[1], s=18, zorder=3, edgecolor=SURFACE, linewidth=0.6)
    ax.annotate(f"top 10% of counties\nhold {top:.0%} of unmet biomass", xy=(0.1, top), xytext=(0.25, top - 0.25),
                fontsize=6, color=INK2, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    ax.text(0.98, 0.06, f"TX + OK + NM: {plains:.0%} of unmet biomass", transform=ax.transAxes, ha="right",
            fontsize=6, color=INK2)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    pct(ax)
    pct(ax, "x")
    ax.set_xlabel("Counties with unmet biomass, ranked")
    ax.set_ylabel("Cumulative share of unmet biomass")
    letter(ax, "d")

    fig.tight_layout(h_pad=1.8, w_pad=2.0)
    save(fig, out / "supplementary", "FigS2_NationalDetail")


# ----------------------------------------------------------------------------- Figure 3
def figure3(R: Path, out: Path) -> None:
    head = pd.read_csv(R / "manuscript/headline_results.csv")
    det = pd.read_csv(R / "deterministic/national_mobilization.csv")
    cover = pd.read_csv(R / "manuscript/feedstock_coverage.csv")
    h5 = head.loc[head["scenario_id"].eq(HEADLINE) & head["contract_years"].eq(5)].iloc[0]
    h10 = head.loc[head["scenario_id"].eq(HEADLINE) & head["contract_years"].eq(10)].iloc[0]
    fam = det.loc[det["scenario_id"].eq(HEADLINE) & det["contract_years"].eq(5)
                  & det["allocation_family"].ne("FAMILY_BALANCED"), "M_Q_full_lower"]
    central = float(h5["M_Q_central"])
    transport = [central, h5["M_Q_offer_plus_rent"], h5["M_Q_ratio_only"]]
    rows = [
        ("Statistical (bootstrap 95%)", h5["M_Q_boot_p025"], h5["M_Q_boot_p975"], SLOT[0]),
        ("Structural (10 variants)", h5["M_Q_struct_min"], h5["M_Q_struct_max"], SLOT[1]),
        ("  of which acreage weighting", min(central, h5["M_Q_acre_weighted"]), max(central, h5["M_Q_acre_weighted"]), SLOT[1]),
        ("Evidence support ($50–300)", h5["M_Q_evidence_lower"], h5["M_Q_evidence_upper"], SLOT[2]),
        ("Rent-context transport", min(transport), max(transport), INK2),
        ("POLYSYS allocation family", fam.min(), fam.max(), INK2),
        ("Contract length (5 vs 10 yr)", min(central, h10["M_Q_central"]), max(central, h10["M_Q_central"]), INK2),
    ]
    t3 = pd.read_csv(R / "manuscript/table3_robustness_synthesis.csv").set_index("check")
    for check, label in (("Offer affordability at $70/dt", "Unaffordable offers refused"),
                         ("Offer capped at payable rent", "Offers capped at payable rent")):
        rows.append((label, t3.loc[check, "M_Q_low"], t3.loc[check, "M_Q_high"], SLOT[3]))

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8), gridspec_kw={"width_ratios": [1.8, 1]})
    ax = axes[0]
    y = np.arange(len(rows))[::-1]
    for yi, (lab, lo, hi, col) in zip(y, rows):
        ax.plot([lo, hi], [yi, yi], color=col, linewidth=3, solid_capstyle="round")
        ax.text(hi + 0.012, yi, f"{100 * (hi - lo):.0f} pp", va="center", fontsize=6, color=INK2)
    ax.axvline(central, color=INK, linewidth=0.8)
    ax.text(central, len(rows) - 0.4, f"central {central:.0%}", ha="center", fontsize=6, color=INK2)
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows])
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0.0, 1.08)
    pct(ax, "x")
    ax.set_xlabel("Biomass mobilized, M_Q (rent-indexed headline, m = 6.71)")
    letter(ax, "a", dx=-0.55)

    ax = axes[1]
    x = np.arange(len(cover))
    w = 0.36
    for off, col, colour, lab in [(-w / 2, "tested_species_harvest_share", SLOT[0], "Acres"),
                                  (w / 2, "tested_species_production_share", SLOT[1], "Biomass")]:
        bars = ax.bar(x + off, cover[col], width=w - 0.04, color=colour, label=lab)
        ax.bar_label(bars, labels=[f"{v:.0%}" for v in cover[col]], fontsize=5.5, color=INK2, padding=1)
    ax.set_xticks(x)
    ax.set_xticklabels([f.replace("FAMILY_0", "Family ") for f in cover["allocation_family"]])
    ax.set_ylim(0, 1)
    ax.grid(axis="x", visible=False)
    pct(ax)
    ax.set_ylabel("Share from directly tested species")
    ax.legend(loc="upper right")
    letter(ax, "b", dx=-0.3)

    fig.tight_layout(w_pad=2.4)
    save(fig, out / "main", "Fig4_Uncertainty")


# ----------------------------------------------------------------------------- maps
def load_geometry(root: Path):
    import geopandas as gpd

    cache = root / "data/interim/geometry"
    shp = next(cache.rglob("*.shp"), None) if cache.exists() else None
    if shp is None:
        cache.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(root / "data/raw/CoUSAKHI_LAEA_2022.zip") as z:
            z.extractall(cache)
        shp = next(cache.rglob("*.shp"))
    geo = gpd.read_file(shp)
    geo["fips"] = geo["atlas_stco"].astype(str).str.zfill(5)
    geo = geo.loc[~geo["fips"].str[:2].isin(["02", "15", "72"])].copy()
    states = geo.assign(state=geo["fips"].str[:2]).dissolve(by="state")
    return geo, states


def legend_below(ax, handles, title, ncol=3):
    ax.legend(handles=handles, title=title, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=ncol,
              fontsize=5.5, title_fontsize=6, handlelength=1, handleheight=1, columnspacing=1.2)


def colorbar_below(fig, ax, cmap, label):
    cb = fig.colorbar(mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(0, 1), cmap=cmap), ax=ax,
                      orientation="horizontal", fraction=0.045, pad=0.02, shrink=0.55)
    cb.set_label(label, fontsize=6)
    cb.ax.tick_params(labelsize=5.5)
    cb.outline.set_visible(False)


def basemap(ax, geo, states):
    geo.plot(ax=ax, facecolor=EMPTY, edgecolor="white", linewidth=0.05)
    states.boundary.plot(ax=ax, color=MUTED, linewidth=0.3)
    ax.set_axis_off()
    ax.set_aspect("equal")


def binned(ax, geo, values: pd.Series, bins, colours, labels, title, extra=()):
    m = geo.merge(values.rename("v").reset_index(), on="fips", how="inner")
    cmap = ListedColormap(colours)
    norm = BoundaryNorm(bins, cmap.N)
    m.plot(ax=ax, column="v", cmap=cmap, norm=norm, edgecolor="white", linewidth=0.05)
    handles = [Patch(facecolor=c, label=lab) for c, lab in zip(colours, labels)] + list(extra)
    handles.append(Patch(facecolor=EMPTY, label="No POLYSYS allocation"))
    legend_below(ax, handles, title, ncol=4)


def figure4(R: Path, out: Path, geo, states) -> None:
    county = pd.read_csv(R / "spatial/county_spatial_robustness.csv", dtype={"fips": "string"})
    c5 = county.loc[county["contract_years"].eq(5)]
    allocation = c5.groupby("fips")["Q_P"].sum() / 3 / 1e3
    unmet = c5.groupby("fips")["unmet_Q_central"].sum() / 3 / 1e3

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
    for ax in axes:
        basemap(ax, geo, states)
    bins_a = [0, 50, 150, 400, 800, 1500, 1e9]
    binned(axes[0], geo, allocation[allocation > 0], bins_a, BLUE[:6],
           ["<50", "50–150", "150–400", "400–800", "800–1,500", "≥1,500"], "POLYSYS biomass (kt dry)")
    letter(axes[0], "a", dx=0, dy=1.02)

    # Unmet biomass here is the central lower bound; counties whose rent or land
    # inputs are unresolved get their own class instead of counting as unmet.
    active = c5.loc[c5["A_P"].gt(0)]
    unresolved = active.groupby("fips")["pressure_class"].agg(lambda s: (s == "unresolved").all())
    unresolved = unresolved[unresolved].index
    bins_u = [0, 10, 50, 150, 500, 1e9]
    positive = unmet[(unmet > 0.0005) & ~unmet.index.isin(unresolved)]
    binned(axes[1], geo, positive, bins_u, ORANGE[1:6], ["<10", "10–50", "50–150", "150–500", "≥500"],
           "Unmet biomass (kt dry)", extra=[Patch(facecolor="#d6e9d9", label="Fully mobilized"),
                                             Patch(facecolor=DIVERGING["unresolved"], label="Unresolved inputs")])
    full = geo.loc[geo["fips"].isin(unmet[(unmet <= 0.0005) & (allocation > 0)].index)]
    full.plot(ax=axes[1], facecolor="#d6e9d9", edgecolor="white", linewidth=0.05)
    geo.loc[geo["fips"].isin(unresolved)].plot(ax=axes[1], facecolor=DIVERGING["unresolved"],
                                               edgecolor="white", linewidth=0.05)
    letter(axes[1], "b", dx=0, dy=1.02)
    fig.tight_layout(w_pad=0.5)
    save(fig, out / "supplementary", "FigS3_AllocationAndUnmet")


def figure5(R: Path, out: Path, geo, states) -> None:
    county = pd.read_csv(R / "spatial/county_spatial_robustness.csv", dtype={"fips": "string"})
    c5 = county.loc[county["contract_years"].eq(5) & county["A_P"].gt(0)]

    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.6))
    for ax in axes.flat:
        basemap(ax, geo, states)

    rho = c5.groupby("fips")["rho_central"].median()
    unresolved = c5.groupby("fips")["pressure_class"].agg(lambda s: (s == "unresolved").all())
    cls = pd.Series(np.select([unresolved.reindex(rho.index), np.isinf(rho), rho >= 2, rho >= 1, rho >= 0.5],
                              ["unresolved", "zero_capacity", "ge_2", "c1_2", "c05_1"], "lt_05"), index=rho.index)
    labels = {"lt_05": "ρ < 0.5", "c05_1": "0.5 ≤ ρ < 1", "c1_2": "1 ≤ ρ < 2", "ge_2": "ρ ≥ 2",
              "zero_capacity": "No capacity", "unresolved": "Unresolved inputs"}
    m = geo.merge(cls.rename("c").reset_index(), on="fips")
    for key, col in DIVERGING.items():
        m.loc[m["c"].eq(key)].plot(ax=axes[0, 0], facecolor=col, edgecolor="white", linewidth=0.05)
    legend_below(axes[0, 0], [Patch(facecolor=DIVERGING[k], label=v) for k, v in labels.items()]
                 + [Patch(facecolor=EMPTY, label="No POLYSYS allocation")],
                 "Pressure ρ = POLYSYS acres / contract capacity (median of families)", ncol=4)
    letter(axes[0, 0], "a", dx=0, dy=1.02)

    for ax, col, title, ramp, lab in [
        (axes[0, 1], "P_bind", "P(capacity binds)", BLUE, "b"),
        (axes[1, 0], "P_top10_risk", "P(top-10% pressure)", ORANGE, "c"),
    ]:
        v = c5.groupby("fips")[col].mean()
        mm = geo.merge(v.rename("v").reset_index(), on="fips")
        cmap = LinearSegmentedColormap.from_list(col, ramp[:6])
        mm.plot(ax=ax, column="v", cmap=cmap, vmin=0, vmax=1, edgecolor="white", linewidth=0.05)
        colorbar_below(fig, ax, cmap, title + " (bootstrap, mean of families)")
        letter(ax, lab, dx=0, dy=1.02)

    agree = c5.groupby("fips")["robust_top10_flag"].sum()
    colours = [BLUE[0], BLUE[2], BLUE[4], BLUE[6]]
    mm = geo.merge(agree.rename("n").reset_index(), on="fips")
    for n, col in enumerate(colours):
        mm.loc[mm["n"].eq(n)].plot(ax=axes[1, 1], facecolor=col, edgecolor="white", linewidth=0.05)
    legend_below(axes[1, 1], [Patch(facecolor=c, label=f"{n} of 3") for n, c in enumerate(colours)]
                 + [Patch(facecolor=EMPTY, label="No POLYSYS allocation")],
                 "Allocation families flagging a robust hotspot", ncol=5)
    letter(axes[1, 1], "d", dx=0, dy=1.02)

    fig.tight_layout(h_pad=0.8, w_pad=0.6)
    save(fig, out / "supplementary", "FigS4_SpatialRobustness")


# ----------------------------------------------------------------------------- main figures
def box(ax, x, y, w, h, title, body, edge, fill="white"):
    from matplotlib.patches import FancyBboxPatch

    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.015",
                                linewidth=1.0, edgecolor=edge, facecolor=fill))
    ax.text(x + w / 2, y + h - 0.035, title, ha="center", va="top", fontsize=6.8, fontweight="bold", color=INK)
    ax.text(x + w / 2, y + h - 0.095, body, ha="center", va="top", fontsize=5.8, color=INK2, linespacing=1.35)


def arrow(ax, x0, y0, x1, y1, colour=MUTED):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=colour, lw=1.0, mutation_scale=8, shrinkA=0, shrinkB=0))


def main_figure1(out: Path) -> None:
    """Framework: three evidence streams, two contractual gates, one outcome."""
    fig, ax = plt.subplots(figsize=(7.2, 3.1))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    w, h = 0.2, 0.25
    box(ax, 0.01, 0.70, w, h, "Prospective allocation", "POLYSYS 2041, $70/dt\nacres Aᴾ and biomass Qᴾ\nby county × land × crop", MUTED)
    box(ax, 0.01, 0.38, w, h, "Compatible land", "Census of Agriculture 2022\nCrop and Pasture pools B\n(suppression completed)", MUTED)
    box(ax, 0.01, 0.06, w, h, "Landholder experiment", "Michigan 2012, randomized\n$50–300 rental offers\n1,270 choices, 403 owners", MUTED)
    box(ax, 0.29, 0.06, w, h, "Gate 1: willingness", "participation p(O)\n× acreage share s\n= access b = p·s", SLOT[0], "#eef4fc")
    box(ax, 0.29, 0.38, w, h, "Contract capacity", "K = B · κ\nκ = acreage-weighted b\n(T1 transmission)", SLOT[0], "#eef4fc")
    box(ax, 0.57, 0.38, w, h, "Implementable share", "λ = min(1, K / Aᴾ)\nper county × land pool\nno reallocation", INK2)
    box(ax, 0.57, 0.70, w, h, "Gate 2: affordability", "offer O ≤ payable rent L\nL = $70/dt revenue\n− production cost", SLOT[1], "#fdf0ea")
    box(ax, 0.82, 0.38, 0.17, h, "Mobilized biomass", "M_Q = Σ λ Qᴾ / Σ Qᴾ\nnational, county,\nunmet biomass", INK, "#f6f6f4")
    arrow(ax, 0.21, 0.185, 0.29, 0.185)
    arrow(ax, 0.39, 0.31, 0.39, 0.38)
    arrow(ax, 0.21, 0.505, 0.29, 0.505)
    arrow(ax, 0.49, 0.505, 0.57, 0.505)
    arrow(ax, 0.21, 0.825, 0.57, 0.825)
    arrow(ax, 0.21, 0.79, 0.60, 0.63)
    arrow(ax, 0.67, 0.70, 0.67, 0.63, SLOT[1])
    arrow(ax, 0.77, 0.505, 0.82, 0.505)
    ax.text(0.39, 0.845, "rent-indexed offer O = m × local cash rent", ha="center", fontsize=5.6, color=INK2)
    save(fig, out / "main", "Fig1_Framework")


def main_figure2(R: Path, out: Path) -> None:
    """The two gates: behaviour, national frontier, offer vs payable rent."""
    curve = pd.read_csv(R / "behaviour/participation_curve.csv")
    knots = pd.read_csv(R / "behaviour/participation_margins.csv")
    cond = pd.read_csv(R / "behaviour/conditional_acreage_by_offer.csv")
    head = pd.read_csv(R / "manuscript/headline_results.csv")
    scen = pd.read_csv(R / "deterministic/compensation_scenarios.csv")
    rows = pd.read_csv(R / "robustness/offer_vs_payable_rows.csv")

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5), gridspec_kw={"width_ratios": [1, 1.15, 1.1]})

    ax = axes[0]
    ax.fill_between(curve["offer"], curve["ll"], curve["ul"], color=SLOT[0], alpha=0.15, linewidth=0)
    ax.plot(curve["offer"], curve["p_smooth"], color=SLOT[0])
    ax.errorbar(knots["offer"], knots["p_categorical"],
                yerr=[knots["p_categorical"] - knots["ll_categorical"], knots["ul_categorical"] - knots["p_categorical"]],
                fmt="o", ms=3.5, color=SLOT[0], mfc="white", mew=0.8, elinewidth=0.7)
    ax.errorbar(cond["offer"] * 1.03, cond["share"], yerr=[cond["share"] - cond["ll"], cond["ul"] - cond["share"]],
                fmt="s", ms=3.5, color=SLOT[1], mfc="white", mew=0.8, elinewidth=0.7)
    ax.text(330, 0.43, "participation", color=INK2, fontsize=6, va="center")
    ax.text(330, 0.85, "acreage share\nif accepted", color=INK2, fontsize=6, va="center")
    ax.text(45, 0.97, f"share flat across offers (p = {cond['joint_offer_p'].iloc[0]:.2f})", fontsize=5.6, color=INK2)
    ax.set_xticks([50, 100, 200, 300])
    ax.set_xlim(35, 470)
    ax.set_ylim(0, 1.02)
    pct(ax)
    ax.set_xlabel("Annual offer (2012 US$ per acre)")
    ax.set_ylabel("Share")
    letter(ax, "a")

    ax = axes[1]
    b = head.loc[head["track"].eq("B_RENT_INDEXED") & head["contract_years"].eq(5)].merge(
        scen[["scenario_id", "rent_multiplier"]], on="scenario_id").sort_values("rent_multiplier")
    x = b["rent_multiplier"]
    ax.fill_between(x, b["M_Q_boot_p025"], b["M_Q_boot_p975"], color=SLOT[0], alpha=0.15, linewidth=0)
    ax.plot(x, b["M_Q_central"], color=SLOT[0], marker="o", ms=3.5, mec=SURFACE, label="Willing landholders")
    ax.fill_between(x, b["M_Q_affordable_high_cost"], b["M_Q_affordable_low_cost"], color=SLOT[1], alpha=0.18, linewidth=0)
    ax.plot(x, b["M_Q_affordable_low_cost"], color=SLOT[1], marker="s", ms=3, mec=SURFACE,
            label="…and offer affordable (low cost)")
    ax.plot(x, b["M_Q_affordable_high_cost"], color=SLOT[1], linestyle="--", linewidth=1, label="…(high cost)")
    cap = pd.read_csv(R / "robustness/capped_offer_national.csv")
    cap = cap.loc[cap["allocation_family"].eq("FAMILY_BALANCED") & cap["contract_years"].eq(5)
                  & cap["track"].eq("B_RENT_INDEXED")].pivot(index="rent_multiplier", columns="cost_case",
                                                              values="M_Q_full_lower").sort_index()
    ax.fill_between(cap.index, cap["HIGH_COST"], cap["LOW_COST"], color=SLOT[2], alpha=0.18, linewidth=0)
    ax.plot(cap.index, cap["LOW_COST"], color=SLOT[2], marker="^", ms=3, mec=SURFACE,
            label="Offer capped at payable rent (low cost)")
    ax.plot(cap.index, cap["HIGH_COST"], color=SLOT[2], linestyle="--", linewidth=1, label="…(high cost)")
    head_m = float(scen.loc[scen["scenario_id"].eq(HEADLINE), "rent_multiplier"].iloc[0])
    ax.axvline(head_m, color=MUTED, linestyle=":", linewidth=0.8)
    multiplier_axis(ax)
    ax.set_ylim(0, 1.02)
    pct(ax)
    ax.set_ylabel("Biomass mobilized, M_Q")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.24), ncol=2, fontsize=5.2, handlelength=1.6,
              columnspacing=0.8)
    letter(ax, "b")

    ax = axes[2]
    r = rows.loc[rows["l_max_low_cost"].notna() & rows["A_P"].gt(0) & rows["offer_headline"].notna()]
    for col, colour, style_, lab in [("offer_headline", SLOT[0], "-", f"Offer at {head_m:.1f}× rent"),
                                      ("l_max_low_cost", SLOT[1], "-", "Payable rent, low cost"),
                                      ("l_max_high_cost", SLOT[1], "--", "Payable rent, high cost")]:
        v = r[col].to_numpy(float)
        o = np.argsort(v)
        cw = np.cumsum(r["A_P"].to_numpy(float)[o])
        ax.plot(v[o], cw / cw[-1], color=colour, linestyle=style_, linewidth=1.3, label=lab)
    ax.axvline(0, color=AXIS, linewidth=0.6)
    ax.set_xlim(-150, 400)
    ax.set_ylim(0, 1.0)
    pct(ax)
    ax.set_xlabel("US$ per acre per year (2012)")
    ax.set_ylabel("Cumulative share of herbaceous acres")
    ax.legend(loc="lower right", fontsize=5.6)
    letter(ax, "c")

    fig.tight_layout(w_pad=1.4)
    save(fig, out / "main", "Fig2_TwoGates")


def main_figure3(R: Path, out: Path, geo, states) -> None:
    """Geography of the shortfall: unmet biomass, persistent hotspots, state shares."""
    county = pd.read_csv(R / "spatial/county_spatial_robustness.csv", dtype={"fips": "string"})
    c5 = county.loc[county["contract_years"].eq(5)]
    active = c5.loc[c5["A_P"].gt(0)]
    allocation = c5.groupby("fips")["Q_P"].sum() / 3 / 1e3
    unmet = c5.groupby("fips")["unmet_Q_central"].sum() / 3 / 1e3
    unresolved = active.groupby("fips")["pressure_class"].agg(lambda s: (s == "unresolved").all())
    unresolved = unresolved[unresolved].index

    fig = plt.figure(figsize=(7.2, 4.9))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 0.48])
    ax_a, ax_b, ax_c = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])
    for ax in (ax_a, ax_b):
        basemap(ax, geo, states)

    positive = unmet[(unmet > 0.0005) & ~unmet.index.isin(unresolved)]
    binned(ax_a, geo, positive, [0, 10, 50, 150, 500, 1e9], ORANGE[1:6], ["<10", "10–50", "50–150", "150–500", "≥500"],
           "Unmet biomass (kt dry)", extra=[Patch(facecolor="#d6e9d9", label="Fully mobilized"),
                                             Patch(facecolor=DIVERGING["unresolved"], label="Unresolved inputs")])
    geo.loc[geo["fips"].isin(unmet[(unmet <= 0.0005) & (allocation > 0)].index)].plot(
        ax=ax_a, facecolor="#d6e9d9", edgecolor="white", linewidth=0.05)
    geo.loc[geo["fips"].isin(unresolved)].plot(ax=ax_a, facecolor=DIVERGING["unresolved"], edgecolor="white",
                                               linewidth=0.05)
    letter(ax_a, "a", dx=0, dy=1.02)

    agree = active.groupby("fips")["robust_top10_flag"].sum()
    colours = [BLUE[0], BLUE[2], BLUE[4], BLUE[6]]
    mm = geo.merge(agree.rename("n").reset_index(), on="fips")
    for n, col in enumerate(colours):
        mm.loc[mm["n"].eq(n)].plot(ax=ax_b, facecolor=col, edgecolor="white", linewidth=0.05)
    legend_below(ax_b, [Patch(facecolor=c, label=f"{n} of 3") for n, c in enumerate(colours)]
                 + [Patch(facecolor=EMPTY, label="No POLYSYS allocation")],
                 "Allocations in which the county is a robust hotspot", ncol=3)
    letter(ax_b, "b", dx=0, dy=1.02)

    names = STATE_NAMES
    u = unmet.groupby(unmet.index.str[:2]).sum()
    q = allocation.groupby(allocation.index.str[:2]).sum()
    share_u = (u / u.sum()).sort_values(ascending=False)
    top = share_u.head(8)
    lab = [names.get(k, k) for k in top.index] + ["All other states"]
    vals_u = list(top.values) + [1 - top.sum()]
    qs = q / q.sum()
    vals_q = list(qs.reindex(top.index).values) + [1 - qs.reindex(top.index).sum()]
    y = np.arange(len(lab))[::-1]
    ax_c.barh(y + 0.18, vals_u, height=0.34, color=SLOT[1], label="Share of national unmet biomass")
    ax_c.barh(y - 0.18, vals_q, height=0.34, color=BLUE[2], label="Share of POLYSYS biomass")
    for yi, v in zip(y, vals_u):
        ax_c.text(v + 0.005, yi + 0.18, f"{v:.0%}", va="center", fontsize=5.6, color=INK2)
    ax_c.set_yticks(y)
    ax_c.set_yticklabels(lab)
    ax_c.grid(axis="y", visible=False)
    ax_c.set_xlim(0, 0.65)
    pct(ax_c, "x")
    ax_c.legend(loc="lower right")
    letter(ax_c, "c", dx=-0.1, dy=1.08)
    fig.tight_layout(h_pad=1.2)
    save(fig, out / "main", "Fig3_Geography")


def supplementary_land_class(R: Path, out: Path) -> None:
    lc = pd.read_csv(R / "manuscript/land_class_mobilization.csv")
    scen = pd.read_csv(R / "deterministic/compensation_scenarios.csv")
    lc = lc.merge(scen[["scenario_id", "rent_multiplier"]], on="scenario_id").sort_values("rent_multiplier")
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.5))
    ax = axes[0]
    for land, col, mk in (("Crop", SLOT[0], "o"), ("Pasture", SLOT[1], "s")):
        d = lc.loc[lc["land_type"].eq(land)]
        ax.plot(d["rent_multiplier"], d["M_Q_central"], color=col, marker=mk, ms=3.5, mec=SURFACE, label=land)
    multiplier_axis(ax)
    ax.set_ylim(0, 1.02)
    pct(ax)
    ax.set_ylabel("Biomass mobilized, M_Q")
    ax.legend(loc="lower right")
    letter(ax, "a")
    ax = axes[1]
    classes = [("BELOW_SUPPORT", "Below $50", SLOT[1]), ("WITHIN_SUPPORT", "$50–300", SLOT[0]),
               ("ABOVE_SUPPORT", "Above $300", SLOT[2]), ("UNSUPPORTED_RENT", "No rent context", MUTED)]
    for i, m in enumerate(MULTIPLIER_TICKS):
        for j, land in enumerate(("Crop", "Pasture")):
            d = lc.loc[lc["land_type"].eq(land) & lc["rent_multiplier"].round(4).eq(m)]
            bottom = 0.0
            for key, lab, col in classes:
                v = float(d[key].fillna(0).iloc[0])
                ax.bar(i + (j - 0.5) * 0.38, v, bottom=bottom, width=0.34, color=col, edgecolor=SURFACE,
                       linewidth=0.8, label=lab if (i == 0 and j == 0) else None)
                bottom += v
    ax.set_xticks(range(len(MULTIPLIER_TICKS)))
    ax.set_xticklabels(["1", "3.35", "6.71", "13.4", "20.1"])
    ax.set_xlabel("Offer multiple of local rent, m (left bar Crop, right Pasture)")
    ax.set_ylabel("Share of POLYSYS biomass")
    ax.set_ylim(0, 1)
    ax.grid(axis="x", visible=False)
    pct(ax)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=4)
    letter(ax, "b")
    fig.tight_layout(w_pad=2)
    save(fig, out / "supplementary", "FigS5_LandClass")


def supplementary_transfer_and_gates(R: Path, out: Path) -> None:
    """Rent coverage of the experiment, where each gate binds, and deficit concentration by design."""
    res = pd.read_csv("data/frozen/public/polysys_allocation.csv", dtype={"fips": "string"})
    rents = pd.read_csv("data/frozen/public/rent_context.csv", dtype={"fips": "string"})
    survey = pd.read_csv("data/frozen/public/studyA_rent_context.csv")["rent_2012usd_per_acre"]
    r = res.merge(rents, on=["fips", "land_type"], how="left")
    r = r.loc[r["rent_supported"].fillna(False).astype(bool) & r["A_P"].gt(0)]
    gates = pd.read_csv(R / "robustness/gate_geography.csv")
    conc = pd.read_csv(R / "robustness/deficit_concentration_by_design.csv").set_index("design")
    numbers = pd.read_csv(R / "manuscript/manuscript_numbers.csv").set_index("key")["value"]

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.6), gridspec_kw={"width_ratios": [1, 1.25, 1]})
    ax = axes[0]
    ax.axvspan(survey.min(), survey.max(), color=EMPTY, zorder=0)
    ax.text(np.sqrt(survey.min() * survey.max()), 0.04, "survey\ncounties", ha="center", fontsize=5.6, color=INK2)
    for land, colour in (("Crop", SLOT[0]), ("Pasture", SLOT[1])):
        d = r.loc[r["land_type"].eq(land)]
        v, w = d["rent_2012usd_per_acre"].to_numpy(float), d["A_P"].to_numpy(float)
        o = np.argsort(v)
        ax.plot(v[o], np.cumsum(w[o]) / w.sum(), color=colour, label=f"{land} acres")
    ax.set_xscale("log")
    ax.set_xlim(1, 300)
    ax.set_xticks([1, 3, 10, 30, 100, 300])
    ax.set_xticklabels(["1", "3", "10", "30", "100", "300"])
    ax.minorticks_off()
    ax.set_ylim(0, 1)
    pct(ax)
    ax.set_xlabel("Local cash rent (2012 US$ per acre)")
    ax.set_ylabel("Cumulative share of POLYSYS acres")
    ax.legend(loc="upper left")
    letter(ax, "a")

    ax = axes[1]
    g = gates.loc[gates["dimension"].eq("usdaregion") & gates["Q_P_share"].gt(0.005)]
    g = g.sort_values("Q_P_share")
    y = np.arange(len(g))
    ax.barh(y + 0.2, g["willingness_unmet_share"], height=0.38, color=SLOT[0], label="Willingness shortfall")
    ax.barh(y - 0.2, g["affordability_loss_share_low"], height=0.38, color=SLOT[1],
            label="Lost to affordability (low cost)")
    ax.set_yticks(y)
    ax.set_yticklabels(g["group"])
    ax.grid(axis="y", visible=False)
    pct(ax, "x")
    ax.set_xlabel("Share of national biomass lost at the gate")
    ax.legend(loc="lower right")
    letter(ax, "b", dx=-0.32)

    ax = axes[2]
    designs = [("RENT_INDEXED_REFERENCE", "Rent-indexed\n(6.71× rent)"), ("UNIFORM_50", "Uniform $50"),
               ("UNIFORM_100", "Uniform $100"), ("UNIFORM_300", "Uniform $300"),
               ("RENT_INDEXED_REFERENCE_ACRE_WEIGHTED", "Rent-indexed,\nacreage-weighted")]
    y = np.arange(len(designs))[::-1]
    vals = [conc.loc[k, "unmet_share_tx_ok_nm"] for k, _ in designs]
    ax.barh(y, vals, height=0.55, color=SLOT[1])
    for yi, v in zip(y, vals):
        ax.text(v + 0.01, yi, f"{v:.0%}", va="center", fontsize=5.6, color=INK2)
    ax.axvline(numbers["tx_ok_nm_share_of_Q_P"], color=MUTED, linestyle=":", linewidth=0.9)
    ax.text(numbers["tx_ok_nm_share_of_Q_P"] - 0.02, -0.75, "share of\nallocation", fontsize=5.4,
            color=INK2, ha="right", va="bottom")
    ax.set_yticks(y)
    ax.set_yticklabels([lab for _, lab in designs])
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.9, len(designs) - 0.5)
    ax.grid(axis="y", visible=False)
    pct(ax, "x")
    ax.set_xlabel("Share of unmet biomass in TX, OK, NM")
    letter(ax, "c", dx=-0.45)
    fig.tight_layout(w_pad=1.2)
    save(fig, out / "supplementary", "FigS6_TransferAndGates")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--output", type=Path, default=Path("results/figures"))
    parser.add_argument("--skip-maps", action="store_true")
    args = parser.parse_args()

    style()
    main_figure1(args.output)
    main_figure2(args.results, args.output)
    figure3(args.results, args.output)          # main Fig 4
    figure1(args.results, args.output)          # Fig S1
    figure2(args.results, args.output)          # Fig S2
    supplementary_land_class(args.results, args.output)
    supplementary_transfer_and_gates(args.results, args.output)
    if not args.skip_maps:
        geo, states = load_geometry(Path.cwd())
        main_figure3(args.results, args.output, geo, states)
        figure4(args.results, args.output, geo, states)   # Fig S3
        figure5(args.results, args.output, geo, states)   # Fig S4
    print(f"PASS: figures written to {args.output}")


if __name__ == "__main__":
    main()
