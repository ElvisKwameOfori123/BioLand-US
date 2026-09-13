"""Draw the four BioLand-US manuscript figures from the frozen reporting workbook."""

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

    candidates = list((root / "data" / "raw").rglob("*CoUSAKHI*2022*.zip"))
    candidates += list((root / "data" / "raw").rglob("*CoUSAKHI*2022*.shp"))
    if not candidates:
        raise FileNotFoundError("County geometry not found under data/raw.")

    source = candidates[0]
    if source.suffix.lower() == ".zip":
        cache = root / "results" / "figures" / "_geometry_cache"
        cache.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(source) as archive:
            archive.extractall(cache)
        shapes = list(cache.rglob("*.shp"))
        if not shapes:
            raise FileNotFoundError(f"No shapefile inside {source}")
        source = shapes[0]

    geo = gpd.read_file(source)
    id_col = next(
        (c for c in ("atlas_stco", "GEOID", "geoid") if c in geo.columns),
        None,
    )
    if id_col is None:
        raise KeyError("County geometry contains no recognized county identifier.")

    geo["fips"] = (
        geo[id_col].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(5)
    )
    geo["statefp"] = geo["fips"].str[:2]
    geo = geo[~geo["statefp"].isin(["02", "15", "72"])].copy()
    states = geo.dissolve(by="statefp")
    return geo, states


def style_from_workbook(xls: pd.ExcelFile):
    colors = pd.read_excel(xls, "Style_Guide").set_index("role")["hex"].to_dict()
    spec = pd.read_excel(xls, "Style_Spec").set_index("setting")["value"].to_dict()

    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [
                "Arial",
                "Helvetica",
                "Nimbus Sans",
                "Liberation Sans",
                "DejaVu Sans",
            ],
            "font.size": float(spec["base_font_pt"]),
            "axes.labelsize": float(spec["base_font_pt"]),
            "xtick.labelsize": float(spec["base_font_pt"]) - 0.5,
            "ytick.labelsize": float(spec["base_font_pt"]) - 0.5,
            "legend.fontsize": float(spec["base_font_pt"]) - 0.8,
            "axes.linewidth": float(spec["axis_linewidth_pt"]),
            "lines.linewidth": 1.0,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.grid": False,
            "legend.frameon": False,
        }
    )
    return colors, spec


def clean(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def letter(ax, value):
    ax.text(
        -0.12,
        1.04,
        value,
        transform=ax.transAxes,
        fontsize=8,
        fontweight="bold",
        va="top",
    )


def save(fig, out_dir: Path, name: str, dpi: int):
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(out_dir / f"{name}.svg", bbox_inches="tight")
    fig.savefig(out_dir / f"{name}.png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--workbook",
        type=Path,
        default=Path("results/figures/BioLandUS_FigureWorkbook_v3_FINAL.xlsx"),
    )
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("results/figures/main"))
    args = parser.parse_args()

    xls = pd.ExcelFile(args.workbook)
    checks = pd.read_excel(xls, "Checks")
    if checks["status"].eq("FAIL").any():
        raise RuntimeError("Reporting workbook contains failed reconciliation checks.")

    C, spec = style_from_workbook(xls)
    dpi = int(spec["dpi_raster"])

    part = pd.read_excel(xls, "F2Pa_Participation")
    acre = pd.read_excel(xls, "F2Pb_AcreageSummary")
    access = pd.read_excel(xls, "F2Pc_Access")

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.25))

    ax = axes[0]
    ax.plot(part.offer, part.smooth_pct, color=C["five_year"], marker="o")
    ax.scatter(
        part.offer,
        part.categorical_pct,
        facecolor="white",
        edgecolor="#222222",
        linewidth=0.7,
        zorder=3,
    )
    ax.set_xlabel(r"Annual offer (2012 US\$ acre$^{-1}$ yr$^{-1}$)")
    ax.set_ylabel("Predicted participation (%)")
    ax.set_xticks(part.offer)
    clean(ax)
    letter(ax, "a")

    ax = axes[1]
    d = acre.set_index("representation")["share_pct"]
    lo = float(d["Lower data-quality"])
    hi = float(d["Upper data-quality"])
    central = float(d["Central all-accept"])
    exact = float(d["Exact-case mean"])
    ipw = float(d["IPW all-accept"])
    ax.barh(0, hi - lo, left=lo, height=0.14, color="#DDDDDD")
    ax.scatter(central, 0, color=C["five_year"], zorder=3)
    ax.scatter(exact, 0.15, facecolor="white", edgecolor="#222222", zorder=3)
    ax.scatter(ipw, -0.15, color=C["ten_year"], marker="D", zorder=3)
    ax.text(central + 1, 0, f"Central {central:.1f}%", va="center")
    ax.text(exact + 1, 0.15, f"Exact {exact:.1f}%", va="center")
    ax.text(ipw + 1, -0.15, f"IPW {ipw:.1f}%", va="center")
    ax.text(
        (lo + hi) / 2,
        -0.35,
        f"Data-quality range: {lo:.1f}–{hi:.1f}%",
        ha="center",
        color="#777777",
    )
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.5, 0.45)
    ax.set_yticks([])
    ax.set_xlabel("Conditional acreage share (%)")
    clean(ax)
    ax.spines["left"].set_visible(False)
    letter(ax, "b")

    ax = axes[2]
    yerr = np.vstack(
        (access.b_mid_pct - access.b_min_pct, access.b_max_pct - access.b_mid_pct)
    )
    ax.errorbar(
        access.offer,
        access.b_mid_pct,
        yerr=yerr,
        fmt="o",
        color=C["five_year"],
        capsize=2,
    )
    ax.set_xlabel(r"Annual offer (2012 US\$ acre$^{-1}$ yr$^{-1}$)")
    ax.set_ylabel(r"Behavioural access, $b=p\times s$ (%)")
    ax.set_xticks(access.offer)
    ax.set_ylim(0, None)
    clean(ax)
    letter(ax, "c")

    fig.tight_layout(w_pad=2.0)
    save(fig, args.output, "Figure1_Behaviour", dpi)

    exp = pd.read_excel(xls, "F3Pa_ExperimentMQ")
    rent = pd.read_excel(xls, "F3Pb_RentIndexMQ")
    support = pd.read_excel(xls, "F3Pc_SupportExposure")
    concentration = pd.read_excel(xls, "F3Pd_UnmetConcentration")
    numbers = pd.read_excel(xls, "Numbers").set_index("key")["value"].to_dict()

    fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.65))
    for ax, data, xcol, xlabel, ticks, is_log, panel in [
        (
            axes[0, 0],
            exp,
            "offer_2012usd_acre_year",
            r"Annual offer (2012 US\$ acre$^{-1}$ yr$^{-1}$)",
            [50, 100, 200, 300],
            False,
            "a",
        ),
        (
            axes[0, 1],
            rent,
            "rent_multiplier",
            r"Rent multiplier, $m$",
            [1, 3.3544, 6.7088, 13.4175, 20.1263],
            True,
            "b",
        ),
    ]:
        d = data[data.contract_years.eq(5)]
        bal = d[d.allocation_family.eq("FAMILY_BALANCED")].sort_values(xcol)
        fam = d[d.allocation_family.isin(["FAMILY_01", "FAMILY_02", "FAMILY_03"])]
        lo = fam.groupby(xcol).p50_pct.min().sort_index()
        hi = fam.groupby(xcol).p50_pct.max().reindex(lo.index)

        ax.fill_between(
            bal[xcol],
            bal.p025_pct,
            bal.p975_pct,
            color=C["statistical"],
            alpha=0.13,
        )
        ax.fill_between(lo.index, lo.values, hi.values, color="#808080", alpha=0.22)
        ax.plot(bal[xcol], bal.p50_pct, color="#222222", marker="o")
        if is_log:
            ax.set_xscale("log")
            ax.minorticks_off()
            ax.set_xticklabels(["1", "3.35", "6.71", "13.42", "20.13"])
            ax.axvline(6.7088, color="#777777", linestyle=":", linewidth=0.7)
        ax.set_xticks(ticks)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(r"Biomass mobilized, $M_Q$ (%)")
        ax.set_ylim(0, 105)
        clean(ax)
        letter(ax, panel)

    ax = axes[1, 0]
    x = np.arange(len(support))
    bottom = np.zeros(len(support))
    for col, role in [
        ("below", "support_below"),
        ("within", "support_within"),
        ("above", "support_above"),
        ("unsupported", "unsupported"),
    ]:
        ax.bar(x, support[col], bottom=bottom, color=C[role], width=0.66)
        bottom += support[col].to_numpy()
    ax.set_xticks(x)
    ax.set_xticklabels(["1", "3.35", "6.71", "13.42", "20.13"])
    ax.set_xlabel(r"Rent multiplier, $m$")
    ax.set_ylabel("Production exposure (%)")
    ax.set_ylim(0, 100)
    clean(ax)
    letter(ax, "c")

    ax = axes[1, 1]
    ax.plot(
        concentration.county_share_pct,
        concentration.cumulative_unmet_pct,
        color="#222222",
    )
    ax.fill_between(
        concentration.county_share_pct,
        0,
        concentration.cumulative_unmet_pct,
        color="#D9D9D9",
        alpha=0.4,
    )
    top10 = float(numbers["unmet_top10pct_counties_share_pct"])
    states = float(numbers["unmet_share_TX_OK_NM_pct"])
    ax.axvline(10, color="#999999", linestyle=":", linewidth=0.7)
    ax.scatter(10, top10, color=C["pressure_ge_2"], zorder=3)
    ax.annotate(
        f"Top 10% of counties\n= {top10:.1f}% of unmet biomass",
        xy=(10, top10),
        xytext=(18, top10 - 17),
        arrowprops=dict(arrowstyle="-", color="#777777", lw=0.6),
    )
    ax.text(
        0.98,
        0.07,
        f"TX + OK + NM = {states:.1f}% of unmet biomass",
        transform=ax.transAxes,
        ha="right",
    )
    ax.set_xlabel("Counties ranked by unmet biomass (%)")
    ax.set_ylabel("Cumulative national unmet biomass (%)")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    clean(ax)
    letter(ax, "d")

    fig.tight_layout(h_pad=2.1, w_pad=1.7)
    save(fig, args.output, "Figure2_NationalMobilization", dpi)

    ladder = pd.read_excel(xls, "F4_UncertaintyLadder")
    cover = pd.read_excel(xls, "F4_FeedstockCoverage")
    implemented = ladder[
        ladder["implemented"].astype(str).str.lower().isin(["true", "1"])
    ].copy()

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(7.2, 2.35),
        gridspec_kw={"width_ratios": [1.65, 1]},
    )

    ax = axes[0]
    y = np.arange(len(implemented))[::-1]
    roles = ["structural", "statistical", "upstream_family", "contract_duration"]
    for yi, (_, row), role in zip(y, implemented.iterrows(), roles):
        ax.plot(
            [row.low_pct, row.high_pct],
            [yi, yi],
            color=C[role],
            linewidth=1.8,
        )
        ax.scatter(row.central_pct, yi, color="#222222", zorder=3)
        ax.text(row.high_pct + 1, yi, f"{row.width_pp:.1f} pp", va="center")
    ax.set_yticks(y)
    ax.set_yticklabels(
        [
            "Structural specification",
            "Statistical bootstrap",
            "POLYSYS allocation family",
            "Contract duration",
        ]
    )
    ax.set_xlabel(r"Biomass mobilized, $M_Q$ (%)")
    clean(ax)
    letter(ax, "a")

    ax = axes[1]
    x = np.arange(len(cover))
    w = 0.36
    ax.bar(x - w / 2, cover.harvest_pct, width=w, color=C["coverage_area"])
    ax.bar(
        x + w / 2,
        cover.production_pct,
        width=w,
        color=C["coverage_production"],
    )
    ax.set_xticks(x)
    ax.set_xticklabels(cover.family_label)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Directly tested-species coverage (%)")
    clean(ax)
    letter(ax, "b")

    fig.tight_layout(w_pad=2.2)
    save(fig, args.output, "Figure3_UncertaintyAndEvidence", dpi)

    geo, states = load_geometry(args.project_root)
    pressure = pd.read_excel(xls, "MapA_Pressure")
    consensus = pd.read_excel(xls, "MapC_Consensus")
    for frame in (pressure, consensus):
        frame["fips"] = (
            frame["fips"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(5)
        )

    fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.6))

    def map_base(ax):
        geo.plot(
            ax=ax,
            facecolor=C["not_allocated"],
            edgecolor="white",
            linewidth=0.08,
        )
        states.boundary.plot(ax=ax, color="#808080", linewidth=0.3)
        ax.set_axis_off()
        ax.set_aspect("equal")

    ax = axes[0, 0]
    map_base(ax)
    merged = geo.merge(pressure[["fips", "display_class"]], on="fips", how="left")
    for cls, role in [
        ("lt_05", "pressure_lt_05"),
        ("c05_1", "pressure_05_1"),
        ("c1_2", "pressure_1_2"),
        ("ge_2", "pressure_ge_2"),
        ("undefined", "undefined"),
    ]:
        merged[merged.display_class.eq(cls)].plot(
            ax=ax,
            facecolor=C[role],
            edgecolor="white",
            linewidth=0.06,
        )
    letter(ax, "a")
    ax.set_title("Implementation pressure", loc="left")

    ax = axes[0, 1]
    map_base(ax)
    merged = geo.merge(consensus[["fips", "P_bind"]], on="fips", how="left")
    cmap = LinearSegmentedColormap.from_list(
        "bind",
        [C["prob_bind_low"], C["prob_bind_high"]],
    )
    merged.plot(
        column="P_bind",
        ax=ax,
        cmap=cmap,
        vmin=0,
        vmax=1,
        edgecolor="white",
        linewidth=0.05,
    )
    cb = fig.colorbar(
        mpl.cm.ScalarMappable(norm=Normalize(0, 1), cmap=cmap),
        ax=ax,
        fraction=0.028,
        pad=0.01,
    )
    cb.set_label(r"$P(\mathrm{binding})$")
    letter(ax, "b")
    ax.set_title("Probability of binding", loc="left")

    ax = axes[1, 0]
    map_base(ax)
    merged = geo.merge(consensus[["fips", "P_top10"]], on="fips", how="left")
    cmap = LinearSegmentedColormap.from_list(
        "top",
        [C["prob_top_low"], C["prob_top_high"]],
    )
    merged.plot(
        column="P_top10",
        ax=ax,
        cmap=cmap,
        vmin=0,
        vmax=1,
        edgecolor="white",
        linewidth=0.05,
    )
    cb = fig.colorbar(
        mpl.cm.ScalarMappable(norm=Normalize(0, 1), cmap=cmap),
        ax=ax,
        fraction=0.028,
        pad=0.01,
    )
    cb.set_label(r"$P(\mathrm{Top\ 10\%\ risk})$")
    letter(ax, "c")
    ax.set_title("Probability of top-risk membership", loc="left")

    ax = axes[1, 1]
    map_base(ax)
    merged = geo.merge(consensus[["fips", "display_class"]], on="fips", how="left")
    items = [
        ("h0", "hotspot_0", "0/3"),
        ("h1", "hotspot_1", "1/3"),
        ("h2", "hotspot_2", "2/3"),
        ("h3", "hotspot_3", "3/3"),
        ("incomplete_families", "incomplete_families", "<3 families"),
    ]
    for cls, role, _ in items:
        merged[merged.display_class.eq(cls)].plot(
            ax=ax,
            facecolor=C[role],
            edgecolor="white",
            linewidth=0.06,
        )
    ax.legend(
        handles=[Patch(facecolor=C[role], label=label) for _, role, label in items],
        loc="lower left",
        ncol=3,
        fontsize=5,
    )
    letter(ax, "d")
    ax.set_title("Robust hotspot consensus", loc="left")

    fig.tight_layout(h_pad=0.7, w_pad=0.7)
    save(fig, args.output, "Figure4_SpatialRobustness", dpi)


if __name__ == "__main__":
    main()
