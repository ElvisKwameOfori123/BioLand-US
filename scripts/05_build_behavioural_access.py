"""Evaluate p, s, and b = p × s for experiment-anchored and rent-indexed scenarios."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from bioland_us.behaviour import (
    SmoothParticipationModel,
    behavioural_access,
    predict_participation,
)
from bioland_us.config import load_config
from bioland_us.feedstocks import apply_feedstock_transfer
from bioland_us.validation import require_columns


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--resource",
        type=Path,
        default=Path("data/frozen/public/polysys_allocation.csv"),
    )
    parser.add_argument(
        "--rents",
        type=Path,
        default=Path("data/frozen/public/rent_context.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/frozen/public/behavioural_access.csv"),
    )
    args = parser.parse_args()

    cfg = load_config()
    bcfg = cfg["behaviour"]["smooth_log_dollar"]
    model = SmoothParticipationModel(
        intercept=bcfg["intercept"],
        ln_offer=bcfg["ln_offer"],
        contract_10yr=bcfg["contract_10yr"],
        pasture=bcfg["pasture"],
        switchgrass=bcfg["switchgrass"],
    )
    s = float(cfg["intensive"]["central_all_accept"])

    resource = pd.read_csv(args.resource, dtype={"fips": "string"})
    rents = pd.read_csv(args.rents, dtype={"fips": "string"})
    require_columns(
        resource,
        ["allocation_family", "fips", "land_type", "feedstock", "A_P", "Q_P"],
        name="resource",
    )
    if "experimental_feedstock" not in resource:
        resource = apply_feedstock_transfer(resource)

    require_columns(
        rents,
        ["fips", "land_type", "rent_supported", "rent_2012usd_per_acre"],
        name="rent context",
    )

    base = resource.merge(
        rents[["fips", "land_type", "rent_supported", "rent_2012usd_per_acre"]],
        on=["fips", "land_type"],
        how="left",
        validate="m:1",
    )

    rows = []
    durations = cfg["experiment"]["contract_years"]

    for offer in cfg["experiment"]["offers_usd_per_acre_year"]:
        for duration in durations:
            x = base.copy()
            x["track"] = "A_EXPERIMENT_ANCHORED"
            x["scenario_id"] = f"EXP_ABS_{int(offer)}"
            x["offer_2012usd_acre_year"] = float(offer)
            x["rent_multiplier"] = np.nan
            x["contract_years"] = duration
            x["p"] = predict_participation(
                x["offer_2012usd_acre_year"],
                x["contract_years"],
                x["land_type"],
                x["experimental_feedstock"],
                model,
            )
            x["s"] = s
            x["b"] = behavioural_access(x["p"], x["s"])
            rows.append(x)

    for mult in cfg["compensation"]["rent_multipliers"]:
        for duration in durations:
            x = base.copy()
            x["track"] = "B_RENT_INDEXED"
            x["scenario_id"] = f"RENT_M_{mult:g}"
            x["rent_multiplier"] = float(mult)
            x["offer_2012usd_acre_year"] = (
                x["rent_2012usd_per_acre"] * float(mult)
            )
            x.loc[
                ~x["rent_supported"].fillna(False),
                "offer_2012usd_acre_year",
            ] = np.nan
            x["contract_years"] = duration
            x["p"] = predict_participation(
                x["offer_2012usd_acre_year"],
                x["contract_years"],
                x["land_type"],
                x["experimental_feedstock"],
                model,
            )
            x["s"] = s
            x["b"] = behavioural_access(x["p"], x["s"])
            rows.append(x)

    out = pd.concat(rows, ignore_index=True)

    group = [
        "track",
        "scenario_id",
        "rent_multiplier",
        "contract_years",
        "allocation_family",
        "fips",
        "land_type",
    ]
    out["weighted_b_numer"] = out["A_P"] * out["b"]

    def identified_acres(g: pd.DataFrame) -> float:
        return float(g.loc[g["b"].notna(), "A_P"].sum())

    pools = (
        out.groupby(group, dropna=False, as_index=False)
        .agg(
            A_P=("A_P", "sum"),
            Q_P=("Q_P", "sum"),
            weighted_b_numer=("weighted_b_numer", "sum"),
        )
    )
    identified = (
        out.groupby(group, dropna=False)
        .apply(identified_acres, include_groups=False)
        .rename("identified_A_P")
        .reset_index()
    )
    pools = pools.merge(identified, on=group, validate="1:1")
    pools["kappa"] = pools["weighted_b_numer"] / pools["A_P"]
    pools.loc[
        pools["identified_A_P"] < pools["A_P"] - 1e-9,
        "kappa",
    ] = np.nan

    args.output.parent.mkdir(parents=True, exist_ok=True)
    pools.to_csv(args.output, index=False)
    print(f"PASS: behavioural access written to {args.output}")


if __name__ == "__main__":
    main()
