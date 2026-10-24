"""Behavioural transport robustness for the rent-indexed track.

Three participation transports, each passed through the same central structure
(T1, FARMLAND land, CENTRAL_PRIMARY s):
    PRIMARY_LOG_DOLLAR  randomized absolute-dollar model (stata 02)
    RATIO_ONLY          ln(offer / rent) model; offer / rent = m everywhere (stata 05)
    OFFER_PLUS_RENT     ln(offer) + ln(rent) model (stata 05)

Evidence-support bounds (decision B12): Study A only observed offers in [$50, $300].
Outside that range the smooth model extrapolates, so monotone bounds replace it:
    offer < 50   : p in [0, p(50)]
    offer > 300  : p in [p(300), 1]

Outputs (results/robustness/)
    transport_national.csv        by family and FAMILY_BALANCED
    support_bounds_national.csv   lower / primary / upper by family and FAMILY_BALANCED
    support_exposure.csv          share of upstream acres below / within / above support
    offer_affordability_national.csv    M_Q when offers above the payable land rent
                                        (bioland_us.economics, E01) are refused
    offer_affordability_by_feedstock.csv  payable rent vs local rent by crop and land

Also: PRIMARY_REGIONAL_RENT_FALLBACK fills the 73 no-rent cells with the USDA-region
mean state rent (R03 sensitivity) in transport_national.csv.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit

from bioland_us.behaviour import conditional_share, load_public_parameters, participation_model
from bioland_us.compensation import reference_multipliers
from bioland_us.config import load_config
from bioland_us.economics import BUDGET_FOR_FEEDSTOCK, max_land_payment
from bioland_us.mobilization import VectorisedT1Model
from bioland_us.validation import require_close


def transport_coefficients(path: Path) -> dict[str, dict[str, float]]:
    t = pd.read_csv(path)
    return {m: dict(zip(g["term"], g["b"])) for m, g in t.groupby("model")}


def covariates(model: VectorisedT1Model, years: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return (np.full(len(model.A_f), float(years == 10)),
            model.land_type.eq("Pasture").to_numpy(float),
            model.feedstock.eq("Switchgrass").to_numpy(float))


def rows_for(model, res, **labels):
    out = [{**labels, "allocation_family": fam, "M_Q_full_lower": res["M_Q_full_lower"][i],
            "M_Q_full_upper": res["M_Q_full_upper"][i]} for i, fam in enumerate(model.families)]
    out.append({**labels, "allocation_family": "FAMILY_BALANCED",
                "M_Q_full_lower": float(np.mean(res["M_Q_full_lower"])),
                "M_Q_full_upper": float(np.mean(res["M_Q_full_upper"]))})
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resource", type=Path, default=Path("data/frozen/public/polysys_allocation.csv"))
    parser.add_argument("--land", type=Path, default=Path("data/frozen/public/compatible_land.csv"))
    parser.add_argument("--rents", type=Path, default=Path("data/frozen/public/rent_context.csv"))
    parser.add_argument("--transport", type=Path, default=Path("results/behaviour/transport_coefficients.csv"))
    parser.add_argument("--deterministic", type=Path, default=Path("results/deterministic/national_mobilization.csv"))
    parser.add_argument("--cpi", type=Path, default=Path("data/frozen/public/cpi_u_annual.csv"))
    parser.add_argument("--budget", type=Path, default=Path("data/frozen/public/perennial_cost_budget.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/robustness"))
    args = parser.parse_args()

    cfg = load_config()
    params = load_public_parameters()
    primary = participation_model(params)
    s = conditional_share(params, "CENTRAL_PRIMARY")
    coefs = transport_coefficients(args.transport)

    resource = pd.read_csv(args.resource, dtype={"fips": "string"})
    rents = pd.read_csv(args.rents, dtype={"fips": "string"})
    model = VectorisedT1Model(resource, pd.read_csv(args.land, dtype={"fips": "string"}))
    r = resource.merge(rents, on=["fips", "land_type"], how="left", validate="m:1")
    rent = r["rent_2012usd_per_acre"].where(r["rent_supported"].fillna(False).astype(bool)).to_numpy(float)
    multipliers = reference_multipliers(resource, rents, cfg["experiment"]["offers_usd_per_acre_year"])
    det = pd.read_csv(args.deterministic)

    transport, bounds, exposure = [], [], []
    for scen in multipliers.itertuples(index=False):
        offer = scen.rent_multiplier * rent
        for years in cfg["experiment"]["contract_years"]:
            c10, pasture, switch = covariates(model, years)
            labels = {"scenario_id": scen.scenario_id, "rent_multiplier": scen.rent_multiplier, "contract_years": years}

            p_primary = model.participation(offer, years, primary)
            ratio = coefs["RATIO_ONLY"]
            p_ratio = expit(ratio["intercept"] + ratio["ln_offer_rent_ratio"] * np.log(scen.rent_multiplier)
                            + ratio["contract_10yr"] * c10 + ratio["pasture"] * pasture
                            + ratio["switchgrass"] * switch)
            p_ratio = np.where(np.isfinite(rent), p_ratio, np.nan)
            opr = coefs["OFFER_PLUS_RENT"]
            with np.errstate(divide="ignore", invalid="ignore"):
                p_opr = expit(opr["intercept"] + opr["ln_offer"] * np.log(offer) + opr["ln_rent"] * np.log(rent)
                              + opr["contract_10yr"] * c10 + opr["pasture"] * pasture
                              + opr["switchgrass"] * switch)

            for spec, p in (("PRIMARY_LOG_DOLLAR", p_primary), ("RATIO_ONLY", p_ratio), ("OFFER_PLUS_RENT", p_opr)):
                res = model.run(p, s)
                transport += rows_for(model, res, transport_spec=spec, **labels)
                if spec == "PRIMARY_LOG_DOLLAR":
                    for i, fam in enumerate(model.families):
                        ref = det.loc[det["scenario_id"].eq(scen.scenario_id) & det["contract_years"].eq(years)
                                      & det["allocation_family"].eq(fam), "M_Q_full_lower"].iloc[0]
                        require_close(float(res["M_Q_full_lower"][i]), float(ref), tolerance=1e-9,
                                      name=f"primary transport reconciliation {scen.scenario_id}/{years}/{fam}")

            p50 = model.participation(np.full(len(offer), 50.0), years, primary)
            p300 = model.participation(np.full(len(offer), 300.0), years, primary)
            low = np.where(offer < 50, 0.0, np.where(offer > 300, p300, p_primary))
            high = np.where(offer < 50, p50, np.where(offer > 300, 1.0, p_primary))
            low[~np.isfinite(offer)] = np.nan
            high[~np.isfinite(offer)] = np.nan
            for bound, p in (("EVIDENCE_LOWER", low), ("PRIMARY", p_primary), ("EVIDENCE_UPPER", high)):
                bounds += rows_for(model, model.run(p, s), bound=bound, **labels)

            if years == cfg["experiment"]["contract_years"][0]:
                cls = np.select([~np.isfinite(offer), offer < 50, offer <= 300],
                                ["UNSUPPORTED_RENT", "BELOW_SUPPORT", "WITHIN_SUPPORT"], "ABOVE_SUPPORT")
                e = pd.DataFrame({"allocation_family": resource["allocation_family"], "land_type": resource["land_type"],
                                  "support": cls, "A_P": resource["A_P"]})
                e = pd.concat([e, e.assign(land_type="All")], ignore_index=True)
                share = e.groupby(["allocation_family", "land_type", "support"])["A_P"].sum()
                share = (share / share.groupby(level=[0, 1]).transform("sum")).rename("acre_share").reset_index()
                exposure.append(share.assign(scenario_id=scen.scenario_id, rent_multiplier=scen.rent_multiplier))

    # ---- R03: regional rent fallback for cells without rent context -----------
    regional_rent = r["rent_2012usd_regional_fallback"].to_numpy(float)
    for scen in multipliers.itertuples(index=False):
        for years in cfg["experiment"]["contract_years"]:
            p = model.participation(scen.rent_multiplier * regional_rent, years, primary)
            transport += rows_for(model, model.run(p, s), transport_spec="PRIMARY_REGIONAL_RENT_FALLBACK",
                                  scenario_id=scen.scenario_id, rent_multiplier=scen.rent_multiplier,
                                  contract_years=years)

    # ---- E01: offer affordability --------------------------------------------
    econ = cfg["economics"]
    cpi = pd.read_csv(args.cpi).set_index("year")["cpi_u_annual_average"]
    price = cfg["polysys"]["biomass_price_usd_per_dry_ton"] * cpi.loc[2012] / cpi.loc[econ["polysys_price_dollar_year"]]
    deflator = cpi.loc[2012] / cpi.loc[econ["cost_budget_dollar_year"]]
    budget = pd.read_csv(args.budget).set_index(["budget_crop", "cost_case"])
    with np.errstate(divide="ignore", invalid="ignore"):
        yield_dt = np.where(resource["A_P"] > 0, resource["Q_P"] / resource["A_P"], np.nan)
    crop = resource["feedstock"].map(BUDGET_FOR_FEEDSTOCK)
    costed = crop.notna().to_numpy()
    l_max = {}
    for case in ("LOW", "HIGH"):
        v = np.full(len(resource), np.nan)
        for name in crop.dropna().unique():
            rows = (crop == name).to_numpy()
            v[rows] = max_land_payment(yield_dt[rows], price, budget.loc[(name, case)], stand_years=econ["stand_years"],
                                       discount_rate=econ["discount_rate"], year2_yield_share=econ["year2_yield_share"],
                                       cost_deflator=deflator)
        l_max[case] = v

    payable = resource[["allocation_family", "fips", "land_type", "feedstock", "A_P", "Q_P"]].copy()
    payable["yield_dt_per_acre"] = yield_dt
    payable["l_max_low_cost"] = l_max["LOW"]
    payable["l_max_high_cost"] = l_max["HIGH"]
    payable["rent_2012usd_per_acre"] = rent

    q = resource["Q_P"].to_numpy(float)
    afford = []
    scenarios = [("A_EXPERIMENT_ANCHORED", f"EXP_ABS_{int(o)}", np.nan, np.full(len(rent), float(o)))
                 for o in cfg["experiment"]["offers_usd_per_acre_year"]]
    scenarios += [("B_RENT_INDEXED", m.scenario_id, m.rent_multiplier, m.rent_multiplier * rent)
                  for m in multipliers.itertuples(index=False)]
    for track, scenario, multiplier, offer in scenarios:
        for years in cfg["experiment"]["contract_years"]:
            p = model.participation(offer, years, primary)
            labels = {"track": track, "scenario_id": scenario, "rent_multiplier": multiplier, "contract_years": years}
            for case, cost_label in (("LOW", "LOW_COST"), ("HIGH", "HIGH_COST")):
                ok = costed & np.isfinite(offer) & (offer <= l_max[case])
                p_aff = np.where(costed & ~ok & np.isfinite(offer), 0.0, p)
                res = model.run(p_aff, s)
                rows = rows_for(model, res, cost_case=cost_label, **labels)
                for i, fam in enumerate(model.families):
                    f = (resource["allocation_family"] == fam).to_numpy()
                    rows[i]["costed_share_of_Q"] = q[f & costed].sum() / q[f].sum()
                    rows[i]["affordable_share_of_costed_Q"] = q[f & ok].sum() / q[f & costed].sum()
                rows[-1]["costed_share_of_Q"] = np.mean([x["costed_share_of_Q"] for x in rows[:-1]])
                rows[-1]["affordable_share_of_costed_Q"] = np.mean([x["affordable_share_of_costed_Q"] for x in rows[:-1]])
                afford += rows

    args.output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(afford).to_csv(args.output_dir / "offer_affordability_national.csv", index=False)
    summary = (payable.loc[payable["l_max_low_cost"].notna() & payable["A_P"].gt(0)]
               .groupby(["feedstock", "land_type"])
               .apply(lambda g: pd.Series({
                   "A_P": g["A_P"].sum(),
                   "median_yield_dt_per_acre": weighted_median(g["yield_dt_per_acre"], g["A_P"]),
                   "median_l_max_low_cost": weighted_median(g["l_max_low_cost"], g["A_P"]),
                   "median_l_max_high_cost": weighted_median(g["l_max_high_cost"], g["A_P"]),
                   "median_local_rent": weighted_median(g["rent_2012usd_per_acre"], g["A_P"]),
               }), include_groups=False).reset_index())
    summary.to_csv(args.output_dir / "offer_affordability_by_feedstock.csv", index=False)

    pd.DataFrame(transport).to_csv(args.output_dir / "transport_national.csv", index=False)
    pd.DataFrame(bounds).to_csv(args.output_dir / "support_bounds_national.csv", index=False)
    pd.concat(exposure, ignore_index=True).to_csv(args.output_dir / "support_exposure.csv", index=False)

    t = pd.DataFrame(transport)
    t = t.loc[t["allocation_family"].eq("FAMILY_BALANCED") & t["contract_years"].eq(5)]
    print("PASS: transport robustness (primary reconciles with 06). Family-balanced M_Q lower, 5-year:")
    print(t.pivot(index="scenario_id", columns="transport_spec", values="M_Q_full_lower").round(4).to_string())
    b = pd.DataFrame(bounds)
    b = b.loc[b["allocation_family"].eq("FAMILY_BALANCED") & b["contract_years"].eq(5)]
    print(b.pivot(index="scenario_id", columns="bound", values="M_Q_full_lower").round(4).to_string())
    a = pd.DataFrame(afford)
    a = a.loc[a["allocation_family"].eq("FAMILY_BALANCED") & a["contract_years"].eq(5)]
    print(f"Offer affordability (price ${price:.1f}/dt in 2012 $):")
    print(a.pivot(index="scenario_id", columns="cost_case", values=["M_Q_full_lower", "affordable_share_of_costed_Q"])
          .round(3).to_string())
    print(summary.round(1).to_string(index=False))


def weighted_median(values: pd.Series, weights: pd.Series) -> float:
    ok = values.notna() & weights.gt(0)
    v, w = values[ok].to_numpy(float), weights[ok].to_numpy(float)
    if len(v) == 0:
        return float("nan")
    o = np.argsort(v)
    cw = np.cumsum(w[o])
    return float(v[o][np.searchsorted(cw, 0.5 * cw[-1])])


if __name__ == "__main__":
    main()
