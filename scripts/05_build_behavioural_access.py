"""Build behavioural access and pooled T1 acreage-access rates.

The script evaluates the frozen smooth participation model, combines it with
the central conditional-acreage share, and then applies the explicit T1 pooled
transmission at county × land level.

The distinction remains explicit:
    b = p × s  is landholder-level behavioural access;
    kappa      is the acreage-weighted county × land access rate under T1.
"""

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


RENT_SCENARIO_NAMES = {
    1.0: "RENT_PARITY_BENCHMARK",
    3.3544: "SUPPORT_ENTRY_REFERENCE",
    6.7088: "SUPPORT_BALANCED_REFERENCE",
    13.4175: "HIGHER_COMPENSATION_200_REFERENCE",
    20.1263: "HIGHER_COMPENSATION_300_REFERENCE",
}


def pool_t1(frame: pd.DataFrame) -> pd.DataFrame:
    group = [
        "track",
        "scenario_id",
        "rent_multiplier",
        "contract_years",
        "allocation_family",
        "fips",
        "land_type",
    ]
    x = frame.copy()
    x["_numerator"] = x["A_P"] * x["b"]

    pooled = (
        x.groupby(group, dropna=False, as_index=False)
        .agg(
            A_P=("A_P", "sum"),
            Q_P=("Q_P", "sum"),
            numerator=("_numerator", "sum"),
        )
    )
    missing = (
        x.assign(_missing=x["b"].isna() & x["A_P"].gt(0))
        .groupby(group, dropna=False, as_index=False)["_missing"]
        .any()
    )
    pooled = pooled.merge(missing, on=group, validate="1:1")
    pooled["kappa"] = np.where(
        pooled["_missing"],
        np.nan,
        np.where(pooled["A_P"].gt(0), pooled["numerator"] / pooled["A_P"], 0.0),
    )
    pooled["transmission_id"] = "T1_POOLED_BEHAVIOURAL_TRANSMISSION"
    return pooled.drop(columns=["numerator", "_missing"])


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
    parser.add_argument(
        "--output-resource",
        type=Path,
        default=Path("data/interim/behavioural_access_feedstock.csv"),
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
    central_s = float(cfg["intensive"]["central_all_accept"])

    resource = pd.read_csv(args.resource, dtype={"fips": "string"})
    rents = pd.read_csv(args.rents, dtype={"fips": "string"})

    require_columns(
        resource,
        ["allocation_family", "fips", "land_type", "feedstock", "A_P", "Q_P"],
        name="POLYSYS allocation",
    )
    if "experimental_feedstock" not in resource.columns:
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
            x["rent_multiplier"] = np.nan
            x["offer_2012usd_acre_year"] = float(offer)
            x["contract_years"] = int(duration)
            x["p"] = predict_participation(
                x["offer_2012usd_acre_year"],
                x["contract_years"],
                x["land_type"],
                x["experimental_feedstock"],
                model,
            )
            x["s"] = central_s
            x["b"] = behavioural_access(x["p"], x["s"])
            x["experimental_support_class"] = "EXACT_RANDOMIZED_KNOT"
            rows.append(x)

    for multiplier in cfg["compensation"]["rent_multipliers"]:
        for duration in durations:
            x = base.copy()
            multiplier = float(multiplier)
            x["track"] = "B_RENT_INDEXED"
            x["scenario_id"] = RENT_SCENARIO_NAMES.get(
                multiplier,
                f"RENT_M_{multiplier:g}",
            )
            x["rent_multiplier"] = multiplier
            supported = x["rent_supported"].fillna(False)
            x["offer_2012usd_acre_year"] = np.where(
                supported,
                multiplier * pd.to_numeric(x["rent_2012usd_per_acre"], errors="coerce"),
                np.nan,
            )
            x["contract_years"] = int(duration)
            x["p"] = predict_participation(
                x["offer_2012usd_acre_year"],
                x["contract_years"],
                x["land_type"],
                x["experimental_feedstock"],
                model,
            )
            x["s"] = central_s
            x["b"] = behavioural_access(x["p"], x["s"])
            x["experimental_support_class"] = np.select(
                [
                    ~supported,
                    x["offer_2012usd_acre_year"].lt(50),
                    x["offer_2012usd_acre_year"].between(50, 300, inclusive="both"),
                    x["offer_2012usd_acre_year"].gt(300),
                ],
                [
                    "UNSUPPORTED_RENT",
                    "BELOW_SUPPORT",
                    "WITHIN_SUPPORT",
                    "ABOVE_SUPPORT",
                ],
                default="UNSUPPORTED_RENT",
            )
            rows.append(x)

    feedstock = pd.concat(rows, ignore_index=True)
    if feedstock.loc[
        feedstock["experimental_support_class"].eq("UNSUPPORTED_RENT"),
        "b",
    ].notna().any():
        raise AssertionError("Unsupported rent cells received behavioural access.")

    pooled = pool_t1(feedstock)

    args.output_resource.parent.mkdir(parents=True, exist_ok=True)
    feedstock.to_csv(args.output_resource, index=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pooled.to_csv(args.output, index=False)

    print("PASS: behavioural access and T1 pooled access written.")
    print(f"  feedstock-level b={args.output_resource}")
    print(f"  county-land kappa={args.output}")


if __name__ == "__main__":
    main()
