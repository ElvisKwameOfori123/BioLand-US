"""Paired respondent bootstrap propagated through the national BioLand-US model.

The same respondent multiplicities refit the extensive participation model and
reconstruct the intensive conditional-acreage margin in every draw. The draw is
then propagated through the fixed T1 national model.

This script represents statistical sampling uncertainty only. Structural
alternatives are handled separately in script 08.
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
from bioland_us.mobilization import apply_capacity_constraint, national_summary
from bioland_us.uncertainty import fit_weighted_logit_irls
from bioland_us.validation import require_columns, require_unique


RENT_SCENARIO_NAMES = {
    1.0: "RENT_PARITY_BENCHMARK",
    3.3544: "SUPPORT_ENTRY_REFERENCE",
    6.7088: "SUPPORT_BALANCED_REFERENCE",
    13.4175: "HIGHER_COMPENSATION_200_REFERENCE",
    20.1263: "HIGHER_COMPENSATION_300_REFERENCE",
}


def design_matrix(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    offer = pd.to_numeric(frame["offer"], errors="coerce").to_numpy(float)
    y = pd.to_numeric(frame["acc"], errors="coerce").to_numpy(float)
    contract10 = pd.to_numeric(frame["contract_years"], errors="coerce").eq(10).to_numpy(float)
    pasture = (
        frame["land_type"].astype("string").str.strip().str.lower().eq("pasture")
        .to_numpy(float)
    )
    switchgrass = (
        frame["experimental_feedstock"].astype("string").str.strip().str.lower()
        .eq("switchgrass").to_numpy(float)
    )
    X = np.column_stack(
        [np.ones(len(frame)), np.log(offer), contract10, pasture, switchgrass]
    )
    if not (np.isfinite(X).all() and np.isfinite(y).all()):
        raise ValueError("Bootstrap input contains unusable extensive-model rows.")
    return X, y, frame["id"].astype("string").to_numpy()


def intensive_share(
    frame: pd.DataFrame,
    respondent_multiplicity: pd.Series,
) -> float:
    accepted = frame.loc[pd.to_numeric(frame["acc"], errors="coerce").eq(1)].copy()
    accepted["_w"] = accepted["id"].astype("string").map(respondent_multiplicity).fillna(0.0)
    accepted = accepted.loc[accepted["_w"].gt(0)].copy()

    exact = accepted["share_exact_observed"].notna()
    if not exact.any():
        raise RuntimeError("Bootstrap draw contains no exact accepted intensive cases.")

    mu_exact = float(
        np.average(
            pd.to_numeric(
                accepted.loc[exact, "share_exact_observed"],
                errors="coerce",
            ),
            weights=accepted.loc[exact, "_w"],
        )
    )

    central = pd.to_numeric(accepted["share_exact_observed"], errors="coerce").copy()
    nonexact = ~exact
    lo = pd.to_numeric(accepted.loc[nonexact, "share_lower_frozen"], errors="coerce")
    hi = pd.to_numeric(accepted.loc[nonexact, "share_upper_frozen"], errors="coerce")
    if lo.isna().any() or hi.isna().any():
        raise RuntimeError("Non-exact accepted choices have missing frozen bounds.")

    central.loc[nonexact] = np.minimum(
        hi.to_numpy(),
        np.maximum(lo.to_numpy(), mu_exact),
    )
    if central.isna().any() or ((central < 0) | (central > 1)).any():
        raise RuntimeError("Draw-specific conditional acreage reconstruction failed.")

    return float(np.average(central, weights=accepted["_w"]))


def pool_access(resource: pd.DataFrame, b: np.ndarray) -> pd.DataFrame:
    x = resource.copy()
    x["b"] = b
    x["_numerator"] = x["A_P"] * x["b"]

    keys = ["allocation_family", "fips", "land_type"]
    base = (
        x.groupby(keys, as_index=False, dropna=False)
        .agg(A_P=("A_P", "sum"), Q_P=("Q_P", "sum"), numerator=("_numerator", "sum"))
    )
    missing = (
        x.assign(_missing=x["b"].isna() & x["A_P"].gt(0))
        .groupby(keys, as_index=False)["_missing"]
        .any()
    )
    base = base.merge(missing, on=keys, validate="1:1")
    base["kappa"] = np.where(
        base["_missing"],
        np.nan,
        np.where(base["A_P"].gt(0), base["numerator"] / base["A_P"], 0.0),
    )
    return base.drop(columns=["numerator", "_missing"])


def constrain(
    resource: pd.DataFrame,
    b: np.ndarray,
    land: pd.DataFrame,
    *,
    scenario_id: str,
    contract_years: int,
) -> pd.DataFrame:
    pools = pool_access(resource, b)
    pools["scenario_id"] = scenario_id
    pools["contract_years"] = contract_years
    pools = pools.merge(
        land,
        on=["fips", "land_type"],
        how="left",
        validate="m:1",
    )
    pools["K"] = pools["B"] * pools["kappa"]
    return apply_capacity_constraint(pools)


def county_risk(constrained: pd.DataFrame) -> pd.DataFrame:
    def summarise(group: pd.DataFrame) -> pd.Series:
        A = float(group["A_P"].sum())
        K = group["K"].sum(min_count=1)
        known = group["lambda"].notna().all()
        if not known or not np.isfinite(K):
            rho = np.nan
            binding = np.nan
        elif A > 0 and K <= 0:
            rho = np.inf
            binding = 1.0
        elif A > 0:
            rho = A / float(K)
            binding = float(A > K)
        else:
            rho = 0.0
            binding = 0.0
        return pd.Series({"rho": rho, "binding": binding})

    return (
        constrained.groupby(["allocation_family", "fips"], dropna=False)
        .apply(summarise, include_groups=False)
        .reset_index()
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--behaviour",
        type=Path,
        default=Path("data/frozen/restricted/behaviour_bootstrap_input.csv"),
    )
    parser.add_argument(
        "--resource",
        type=Path,
        default=Path("data/frozen/public/polysys_allocation.csv"),
    )
    parser.add_argument(
        "--land",
        type=Path,
        default=Path("data/frozen/public/compatible_land.csv"),
    )
    parser.add_argument(
        "--rents",
        type=Path,
        default=Path("data/frozen/public/rent_context.csv"),
    )
    parser.add_argument("--seed", type=int, default=20260912)
    parser.add_argument(
        "--output-draws",
        type=Path,
        default=Path("results/bootstrap/national_bootstrap_draws.csv"),
    )
    parser.add_argument(
        "--output-summary",
        type=Path,
        default=Path("results/bootstrap/national_bootstrap_summary.csv"),
    )
    parser.add_argument(
        "--output-county",
        type=Path,
        default=Path("results/bootstrap/support_balanced_county_bootstrap.csv"),
    )
    args = parser.parse_args()

    cfg = load_config()
    n_draws = int(cfg["uncertainty"]["bootstrap_draws"])

    behaviour = pd.read_csv(args.behaviour, dtype={"id": "string"})
    resource = pd.read_csv(args.resource, dtype={"fips": "string"})
    land = pd.read_csv(args.land, dtype={"fips": "string"})
    rents = pd.read_csv(args.rents, dtype={"fips": "string"})

    require_columns(
        behaviour,
        [
            "id",
            "acc",
            "offer",
            "contract_years",
            "land_type",
            "experimental_feedstock",
            "share_exact_observed",
            "share_lower_frozen",
            "share_upper_frozen",
        ],
        name="behaviour bootstrap input",
    )
    require_columns(
        resource,
        [
            "allocation_family",
            "fips",
            "land_type",
            "experimental_feedstock",
            "A_P",
            "Q_P",
        ],
        name="POLYSYS allocation",
    )
    require_columns(land, ["fips", "land_type", "B"], name="compatible land")
    require_columns(
        rents,
        ["fips", "land_type", "rent_supported", "rent_2012usd_per_acre"],
        name="rent context",
    )
    require_unique(land, ["fips", "land_type"], name="compatible land")
    require_unique(rents, ["fips", "land_type"], name="rent context")

    resource["A_P"] = pd.to_numeric(resource["A_P"], errors="raise")
    resource["Q_P"] = pd.to_numeric(resource["Q_P"], errors="raise")
    resource["fips"] = resource["fips"].astype("string").str.zfill(5)

    rent_join = rents[
        ["fips", "land_type", "rent_supported", "rent_2012usd_per_acre"]
    ].copy()
    resource = resource.merge(
        rent_join,
        on=["fips", "land_type"],
        how="left",
        validate="m:1",
    )

    X, y, ids = design_matrix(behaviour)
    respondents = pd.Index(pd.unique(ids))
    if len(respondents) != 403:
        raise ValueError(f"Expected 403 respondents, found {len(respondents)}.")

    id_to_position = {respondent: i for i, respondent in enumerate(respondents)}
    row_positions = np.array([id_to_position[x] for x in ids], dtype=int)

    bcfg = cfg["behaviour"]["smooth_log_dollar"]
    beta_reference = np.array(
        [
            bcfg["intercept"],
            bcfg["ln_offer"],
            bcfg["contract_10yr"],
            bcfg["pasture"],
            bcfg["switchgrass"],
        ],
        dtype=float,
    )

    rng = np.random.default_rng(args.seed)
    draw_rows: list[dict[str, object]] = []
    county_counts: dict[tuple[str, int, str], dict[str, int]] = {}
    failures: list[dict[str, object]] = []

    offers = cfg["experiment"]["offers_usd_per_acre_year"]
    durations = cfg["experiment"]["contract_years"]
    multipliers = cfg["compensation"]["rent_multipliers"]
    support_balanced = float(cfg["compensation"]["support_balanced_multiplier"])

    for draw in range(1, n_draws + 1):
        sampled = rng.integers(0, len(respondents), size=len(respondents))
        multiplicity = np.bincount(sampled, minlength=len(respondents))
        respondent_weight = pd.Series(
            multiplicity,
            index=respondents.astype("string"),
            dtype=float,
        )
        row_weight = multiplicity[row_positions].astype(float)

        beta, converged = fit_weighted_logit_irls(
            X,
            y,
            row_weight,
            beta0=beta_reference,
        )
        try:
            s_draw = intensive_share(behaviour, respondent_weight)
        except Exception as exc:
            failures.append({"draw": draw, "error": repr(exc)})
            continue

        if not converged or not np.isfinite(beta).all() or not np.isfinite(s_draw):
            failures.append({"draw": draw, "error": "behavioural refit did not converge"})
            continue

        model = SmoothParticipationModel(
            intercept=float(beta[0]),
            ln_offer=float(beta[1]),
            contract_10yr=float(beta[2]),
            pasture=float(beta[3]),
            switchgrass=float(beta[4]),
        )

        for offer in offers:
            for duration in durations:
                p = predict_participation(
                    np.full(len(resource), float(offer)),
                    np.full(len(resource), int(duration)),
                    resource["land_type"],
                    resource["experimental_feedstock"],
                    model,
                )
                b = behavioural_access(p, s_draw)
                constrained = constrain(
                    resource,
                    b,
                    land,
                    scenario_id=f"EXP_ABS_{int(offer)}",
                    contract_years=int(duration),
                )
                summary = national_summary(constrained)
                for row in summary.itertuples(index=False):
                    draw_rows.append(
                        {
                            "draw": draw,
                            "track": "A_EXPERIMENT_ANCHORED",
                            "scenario_id": row.scenario_id,
                            "offer_2012usd_acre_year": float(offer),
                            "rent_multiplier": np.nan,
                            "contract_years": int(duration),
                            "allocation_family": row.allocation_family,
                            "conditional_share": s_draw,
                            "M_A_full_lower": row.M_A_full_lower,
                            "M_A_full_upper": row.M_A_full_upper,
                            "M_Q_full_lower": row.M_Q_full_lower,
                            "M_Q_full_upper": row.M_Q_full_upper,
                            "identified_production_share": row.identified_production_share,
                            "binding_county_land_cells": row.binding_county_land_cells,
                        }
                    )

        for multiplier in multipliers:
            supported = resource["rent_supported"].fillna(False).to_numpy(bool)
            local_offer = np.where(
                supported,
                float(multiplier)
                * pd.to_numeric(
                    resource["rent_2012usd_per_acre"],
                    errors="coerce",
                ).to_numpy(float),
                np.nan,
            )
            for duration in durations:
                p = predict_participation(
                    local_offer,
                    np.full(len(resource), int(duration)),
                    resource["land_type"],
                    resource["experimental_feedstock"],
                    model,
                )
                b = behavioural_access(p, s_draw)
                scenario_id = RENT_SCENARIO_NAMES.get(
                    float(multiplier),
                    f"RENT_M_{float(multiplier):g}",
                )
                constrained = constrain(
                    resource,
                    b,
                    land,
                    scenario_id=scenario_id,
                    contract_years=int(duration),
                )
                summary = national_summary(constrained)
                for row in summary.itertuples(index=False):
                    draw_rows.append(
                        {
                            "draw": draw,
                            "track": "B_RENT_INDEXED",
                            "scenario_id": row.scenario_id,
                            "offer_2012usd_acre_year": np.nan,
                            "rent_multiplier": float(multiplier),
                            "contract_years": int(duration),
                            "allocation_family": row.allocation_family,
                            "conditional_share": s_draw,
                            "M_A_full_lower": row.M_A_full_lower,
                            "M_A_full_upper": row.M_A_full_upper,
                            "M_Q_full_lower": row.M_Q_full_lower,
                            "M_Q_full_upper": row.M_Q_full_upper,
                            "identified_production_share": row.identified_production_share,
                            "binding_county_land_cells": row.binding_county_land_cells,
                        }
                    )

                if np.isclose(float(multiplier), support_balanced):
                    risk = county_risk(constrained)
                    for family, group in risk.groupby("allocation_family"):
                        valid = group["rho"].notna()
                        ranked = group.loc[valid].sort_values("rho", ascending=False)
                        n_top = max(1, int(np.ceil(0.10 * len(ranked)))) if len(ranked) else 0
                        top = set(ranked.head(n_top)["fips"].astype(str))
                        for row in group.itertuples(index=False):
                            key = (str(family), int(duration), str(row.fips))
                            acc = county_counts.setdefault(
                                key,
                                {"valid": 0, "binding": 0, "top10": 0},
                            )
                            if pd.notna(row.rho):
                                acc["valid"] += 1
                                acc["binding"] += int(row.binding == 1)
                                acc["top10"] += int(str(row.fips) in top)

        if draw == 1 or draw % 100 == 0 or draw == n_draws:
            print(f"bootstrap draw {draw}/{n_draws}")

    if failures:
        failure_path = args.output_draws.with_name("bootstrap_failures.csv")
        failure_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(failures).to_csv(failure_path, index=False)
        raise RuntimeError(
            f"{len(failures)} bootstrap draws failed; see {failure_path}"
        )

    draws = pd.DataFrame(draw_rows)
    args.output_draws.parent.mkdir(parents=True, exist_ok=True)
    draws.to_csv(args.output_draws, index=False)

    group_cols = [
        "track",
        "scenario_id",
        "offer_2012usd_acre_year",
        "rent_multiplier",
        "contract_years",
        "allocation_family",
    ]
    rows = []
    for key, group in draws.groupby(group_cols, dropna=False):
        record = dict(zip(group_cols, key))
        for metric in [
            "M_A_full_lower",
            "M_A_full_upper",
            "M_Q_full_lower",
            "M_Q_full_upper",
        ]:
            values = pd.to_numeric(group[metric], errors="coerce").dropna()
            record[f"{metric}_mean"] = float(values.mean())
            record[f"{metric}_p025"] = float(values.quantile(0.025))
            record[f"{metric}_p50"] = float(values.quantile(0.50))
            record[f"{metric}_p975"] = float(values.quantile(0.975))
        record["successful_draws"] = int(group["draw"].nunique())
        rows.append(record)

    pd.DataFrame(rows).to_csv(args.output_summary, index=False)

    county_rows = []
    for (family, duration, fips), counts in county_counts.items():
        n = counts["valid"]
        county_rows.append(
            {
                "allocation_family": family,
                "contract_years": duration,
                "fips": fips,
                "valid_draws": n,
                "P_bind": counts["binding"] / n if n else np.nan,
                "P_top10_risk": counts["top10"] / n if n else np.nan,
            }
        )
    pd.DataFrame(county_rows).to_csv(args.output_county, index=False)

    print(f"PASS: {n_draws} paired respondent bootstrap draws propagated nationally.")
    print(f"  national summary={args.output_summary}")
    print(f"  county robustness={args.output_county}")


if __name__ == "__main__":
    main()
