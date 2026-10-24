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

    args.output_dir.mkdir(parents=True, exist_ok=True)
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


if __name__ == "__main__":
    main()
