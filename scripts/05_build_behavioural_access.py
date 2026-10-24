"""Behavioural access at county x land level under T1 pooled transmission.

For every compensation scenario and contract duration:
    p_f      participation for the experimental archetype of feedstock f (07E1 transfer)
    p_pool   acreage-weighted p over the feedstocks of one county x land pool (T1)
    kappa    = s * p_pool, the acreage-access rate (s = conditional acreage share)

Tracks
    A_EXPERIMENT_ANCHORED  the four randomized Study-A offers, nationally uniform
    B_RENT_INDEXED         O_cl = m * R_cl, multipliers from bioland_us.compensation
                           (cells without rent context stay unresolved, never p = 0)

Behaviour weighting
    PER_CHOICE     central Study-A estimates
    ACRE_WEIGHTED  acreage-weighted p and s (person-to-acreage sensitivity, B07)

Outputs
    data/frozen/public/behavioural_access.csv       county x land pools
    results/deterministic/compensation_scenarios.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from bioland_us.behaviour import (
    conditional_share,
    load_public_parameters,
    participation_model,
    predict_participation,
)
from bioland_us.compensation import reference_multipliers
from bioland_us.config import load_config
from bioland_us.mobilization import pool_participation
from bioland_us.validation import require_columns

POOL_KEYS = ["behaviour_weighting", "track", "scenario_id", "rent_multiplier",
             "contract_years", "allocation_family", "fips", "land_type"]


def support_class(offer: pd.Series) -> np.ndarray:
    return np.select(
        [offer.isna(), offer.lt(50), offer.le(300)],
        ["UNSUPPORTED_RENT", "BELOW_SUPPORT", "WITHIN_SUPPORT"],
        default="ABOVE_SUPPORT",
    )


def scenario_rows(base: pd.DataFrame, cfg: dict, multipliers: pd.DataFrame):
    """Yield (track, scenario_id, multiplier, duration, offer per row)."""
    rent = pd.to_numeric(base["rent_2012usd_per_acre"], errors="coerce").where(
        base["rent_supported"].fillna(False).astype(bool)
    )
    for duration in cfg["experiment"]["contract_years"]:
        for offer in cfg["experiment"]["offers_usd_per_acre_year"]:
            yield ("A_EXPERIMENT_ANCHORED", f"EXP_ABS_{int(offer)}", np.nan, duration,
                   pd.Series(float(offer), index=base.index))
        for row in multipliers.itertuples(index=False):
            yield ("B_RENT_INDEXED", row.scenario_id, row.rent_multiplier, duration,
                   row.rent_multiplier * rent)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resource", type=Path, default=Path("data/frozen/public/polysys_allocation.csv"))
    parser.add_argument("--rents", type=Path, default=Path("data/frozen/public/rent_context.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/frozen/public/behavioural_access.csv"))
    parser.add_argument("--output-scenarios", type=Path,
                        default=Path("results/deterministic/compensation_scenarios.csv"))
    args = parser.parse_args()

    cfg = load_config()
    params = load_public_parameters()

    resource = pd.read_csv(args.resource, dtype={"fips": "string"})
    rents = pd.read_csv(args.rents, dtype={"fips": "string"})
    require_columns(resource, ["allocation_family", "fips", "land_type", "experimental_feedstock", "A_P", "Q_P"],
                    name="POLYSYS allocation")
    require_columns(rents, ["fips", "land_type", "rent_supported", "rent_2012usd_per_acre"], name="rent context")

    multipliers = reference_multipliers(resource, rents, cfg["experiment"]["offers_usd_per_acre_year"])
    configured = np.array(cfg["compensation"]["rent_multipliers"], dtype=float)
    if not np.allclose(np.sort(multipliers["rent_multiplier"]), np.sort(configured), atol=5e-5):
        raise ValueError(
            "Data-derived rent multipliers differ from config: "
            f"{multipliers['rent_multiplier'].round(4).tolist()} vs {configured.tolist()}"
        )

    base = resource.merge(rents[["fips", "land_type", "rent_supported", "rent_2012usd_per_acre"]],
                          on=["fips", "land_type"], how="left", validate="m:1")

    pools = []
    for weighting in ("PER_CHOICE", "ACRE_WEIGHTED"):
        model = participation_model(params, weighting)
        s = conditional_share(params, "CENTRAL_PRIMARY", weighting)
        for track, scenario, multiplier, duration, offer in scenario_rows(base, cfg, multipliers):
            x = base[["allocation_family", "fips", "land_type", "experimental_feedstock", "A_P", "Q_P"]].copy()
            x["p"] = predict_participation(offer.to_numpy(float), np.full(len(x), duration),
                                           x["land_type"], x["experimental_feedstock"], model)
            x["support"] = support_class(offer)
            x["behaviour_weighting"] = weighting
            x["track"] = track
            x["scenario_id"] = scenario
            x["rent_multiplier"] = multiplier
            x["contract_years"] = int(duration)

            pooled = pool_participation(x, POOL_KEYS)
            within = (
                x.assign(_w=x["A_P"].where(x["support"].eq("WITHIN_SUPPORT"), 0.0))
                .groupby(POOL_KEYS, dropna=False, as_index=False)["_w"].sum()
            )
            pooled = pooled.merge(within, on=POOL_KEYS, validate="1:1")
            pooled["within_support_acres"] = pooled.pop("_w")
            pooled["conditional_share"] = s
            pooled["kappa"] = s * pooled["p_pool"]
            pools.append(pooled)

    out = pd.concat(pools, ignore_index=True)
    if not out["kappa"].dropna().between(0, 1).all():
        raise AssertionError("kappa outside [0, 1].")
    out["transmission_id"] = "T1_POOLED_BEHAVIOURAL_TRANSMISSION"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    args.output_scenarios.parent.mkdir(parents=True, exist_ok=True)
    multipliers.to_csv(args.output_scenarios, index=False)

    print(f"PASS: {len(out):,} county x land pools written.")
    print(multipliers.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
