"""Paired respondent bootstrap propagated through the central national model.

Each draw resamples Study-A respondents with replacement. The same respondent
multiplicities (pairing rule) are used to
    1. refit the smooth participation logit (IRLS, frequency weights), and
    2. rebuild the conditional acreage share s with the frozen central rule
       (exact shares kept; other accepted choices take the draw's exact-case mean
       projected into their own feasible interval).
The draw then passes through the fixed central structure (T1, FARMLAND land,
PER_CHOICE weighting). This is statistical sampling uncertainty only.

Gate: draw 0 (all multiplicities 1) must reproduce the public parameters and
the deterministic national results of 06 before any resampling starts.

Inputs
    data/frozen/restricted/behaviour_bootstrap_input.csv   (Stata 04, restricted)
Outputs (results/bootstrap/)
    national_bootstrap_draws.csv, national_bootstrap_summary.csv,
    support_balanced_county_bootstrap.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from bioland_us.behaviour import (
    SmoothParticipationModel,
    conditional_share,
    load_public_parameters,
    participation_model,
)
from bioland_us.compensation import reference_multipliers
from bioland_us.config import load_config
from bioland_us.mobilization import VectorisedT1Model
from bioland_us.uncertainty import fit_weighted_logit_irls
from bioland_us.validation import require_close, require_columns

SPATIAL_SCENARIO = "SUPPORT_BALANCED_REFERENCE"


def design(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    X = np.column_stack([
        np.ones(len(frame)),
        np.log(frame["offer"].to_numpy(float)),
        frame["contract_years"].eq(10).to_numpy(float),
        frame["land_type"].eq("Pasture").to_numpy(float),
        frame["experimental_feedstock"].eq("Switchgrass").to_numpy(float),
    ])
    return X, frame["acc"].to_numpy(float)


class IntensiveRule:
    """Draw-specific conditional acreage share from accepted choices."""

    def __init__(self, behaviour: pd.DataFrame, position: np.ndarray):
        acc = behaviour["acc"].eq(1).to_numpy()
        self.pos = position[acc]
        self.exact = behaviour.loc[acc, "share_exact_observed"].notna().to_numpy()
        self.share = behaviour.loc[acc, "share_exact_observed"].to_numpy(float)
        self.lo = behaviour.loc[acc, "share_lower_frozen"].to_numpy(float)
        self.hi = behaviour.loc[acc, "share_upper_frozen"].to_numpy(float)

    def __call__(self, multiplicity: np.ndarray) -> float:
        w = multiplicity[self.pos].astype(float)
        if w[self.exact].sum() <= 0:
            return np.nan
        mu = np.average(self.share[self.exact], weights=w[self.exact])
        central = np.where(self.exact, self.share, np.clip(mu, self.lo, self.hi))
        return float(np.average(central, weights=w))


def county_risk(model: VectorisedT1Model, out: dict) -> pd.DataFrame:
    """County binding = any active pool binds; rho = most constrained pool."""
    pools = model.pools[["allocation_family", "fips"]].copy()
    active = model.A > 0
    pools["unresolved"] = active & np.isnan(out["lambda"])
    pools["bind"] = active & (out["lambda"] < 1.0)
    pools["rho"] = np.where(active, out["rho"], np.nan)
    c = pools.groupby(["allocation_family", "fips"]).agg(
        unresolved=("unresolved", "any"), bind=("bind", "any"), rho=("rho", "max")).reset_index()
    c.loc[c["unresolved"], "rho"] = np.nan
    return c


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--behaviour", type=Path, default=Path("data/frozen/restricted/behaviour_bootstrap_input.csv"))
    parser.add_argument("--resource", type=Path, default=Path("data/frozen/public/polysys_allocation.csv"))
    parser.add_argument("--land", type=Path, default=Path("data/frozen/public/compatible_land.csv"))
    parser.add_argument("--rents", type=Path, default=Path("data/frozen/public/rent_context.csv"))
    parser.add_argument("--deterministic", type=Path, default=Path("results/deterministic/national_mobilization.csv"))
    parser.add_argument("--draws", type=int, default=None)
    parser.add_argument("--output-dir", type=Path, default=Path("results/bootstrap"))
    args = parser.parse_args()

    cfg = load_config()
    params = load_public_parameters()
    n_draws = args.draws or int(cfg["uncertainty"]["bootstrap_draws"])
    seed = int(cfg["uncertainty"]["bootstrap_seed"])

    behaviour = pd.read_csv(args.behaviour, dtype={"id": "string"})
    require_columns(behaviour, ["id", "acc", "offer", "contract_years", "land_type", "experimental_feedstock",
                                "share_exact_observed", "share_lower_frozen", "share_upper_frozen"],
                    name="behaviour bootstrap input")
    resource = pd.read_csv(args.resource, dtype={"fips": "string"})
    land = pd.read_csv(args.land, dtype={"fips": "string"})
    rents = pd.read_csv(args.rents, dtype={"fips": "string"})

    ids, position = np.unique(behaviour["id"].to_numpy(), return_inverse=True)
    X, y = design(behaviour)
    intensive = IntensiveRule(behaviour, position)
    model = VectorisedT1Model(resource, land)

    rent = resource.merge(rents, on=["fips", "land_type"], how="left", validate="m:1")
    rent = rent["rent_2012usd_per_acre"].where(rent["rent_supported"].fillna(False).astype(bool)).to_numpy(float)
    multipliers = reference_multipliers(resource, rents, cfg["experiment"]["offers_usd_per_acre_year"])
    configs = [("A_EXPERIMENT_ANCHORED", f"EXP_ABS_{int(o)}", np.nan, np.full(len(rent), float(o)))
               for o in cfg["experiment"]["offers_usd_per_acre_year"]]
    configs += [("B_RENT_INDEXED", r.scenario_id, r.rent_multiplier, r.rent_multiplier * rent)
                for r in multipliers.itertuples(index=False)]
    durations = cfg["experiment"]["contract_years"]

    # ---- draw-0 gate ---------------------------------------------------------
    reference = participation_model(params, "PER_CHOICE")
    beta0, ok = fit_weighted_logit_irls(X, y, np.ones(len(y)), beta0=reference.as_array())
    if not ok or np.max(np.abs(beta0 - reference.as_array())) > 1e-5:
        raise AssertionError(f"Draw 0 does not reproduce the Stata coefficients: {beta0}")
    require_close(intensive(np.ones(len(ids))), conditional_share(params, "CENTRAL_PRIMARY"),
                  tolerance=1e-9, name="draw-0 conditional share")
    det = pd.read_csv(args.deterministic)
    s0 = conditional_share(params, "CENTRAL_PRIMARY")
    for track, scenario, _, offer in configs:
        for years in durations:
            res = model.run(model.participation(offer, years, reference), s0)
            for i, fam in enumerate(model.families):
                ref = det.loc[det["scenario_id"].eq(scenario) & det["contract_years"].eq(years)
                              & det["allocation_family"].eq(fam), "M_Q_full_lower"]
                require_close(float(res["M_Q_full_lower"][i]), float(ref.iloc[0]), tolerance=1e-9,
                              name=f"draw-0 {scenario}/{years}/{fam}")
    print("Draw-0 gate PASS: Stata coefficients, s and the 06 national results are reproduced.")

    # ---- resampling ----------------------------------------------------------
    rng = np.random.default_rng(seed)
    rows, county_rows, failures = [], [], []
    for draw in range(1, n_draws + 1):
        mult = np.bincount(rng.integers(0, len(ids), len(ids)), minlength=len(ids))
        beta, ok = fit_weighted_logit_irls(X, y, mult[position].astype(float), beta0=reference.as_array())
        s = intensive(mult)
        if not ok or not np.all(np.isfinite(beta)) or not np.isfinite(s):
            failures.append(draw)
            continue
        m = SmoothParticipationModel(*beta)
        for track, scenario, multiplier, offer in configs:
            for years in durations:
                res = model.run(model.participation(offer, years, m), s)
                for i, fam in enumerate(model.families):
                    rows.append((draw, track, scenario, multiplier, years, fam, s,
                                 res["M_Q_full_lower"][i], res["M_Q_full_upper"][i],
                                 res["M_A_full_lower"][i], res["M_A_full_upper"][i]))
                if scenario == SPATIAL_SCENARIO:
                    risk = county_risk(model, res)
                    risk["contract_years"] = years
                    risk["draw"] = draw
                    county_rows.append(risk)
        if draw == 1 or draw % 100 == 0:
            print(f"  draw {draw}/{n_draws}")

    if failures:
        raise RuntimeError(f"{len(failures)} bootstrap draws failed to converge: {failures[:10]}")

    draws = pd.DataFrame(rows, columns=["draw", "track", "scenario_id", "rent_multiplier", "contract_years",
                                        "allocation_family", "conditional_share", "M_Q_full_lower",
                                        "M_Q_full_upper", "M_A_full_lower", "M_A_full_upper"])
    balanced = (draws.groupby(["draw", "track", "scenario_id", "rent_multiplier", "contract_years"],
                              dropna=False, as_index=False)
                [["M_Q_full_lower", "M_Q_full_upper", "M_A_full_lower", "M_A_full_upper"]].mean()
                .assign(allocation_family="FAMILY_BALANCED"))
    draws = pd.concat([draws, balanced], ignore_index=True)

    keys = ["track", "scenario_id", "rent_multiplier", "contract_years", "allocation_family"]
    summary = (draws.groupby(keys, dropna=False)["M_Q_full_lower"]
               .quantile([0.025, 0.5, 0.975]).unstack().reset_index()
               .rename(columns={0.025: "M_Q_lower_p025", 0.5: "M_Q_lower_p50", 0.975: "M_Q_lower_p975"}))
    summary["draws"] = n_draws

    county = pd.concat(county_rows, ignore_index=True)
    county["top10"] = 0
    valid = county["rho"].notna()
    rank = county.loc[valid].groupby(["draw", "allocation_family", "contract_years"])["rho"].rank(
        ascending=False, method="first")
    size = county.loc[valid].groupby(["draw", "allocation_family", "contract_years"])["rho"].transform("size")
    county.loc[valid, "top10"] = (rank <= np.ceil(0.10 * size)).astype(int)
    county_summary = (county.loc[valid].groupby(["allocation_family", "contract_years", "fips"])
                      .agg(valid_draws=("draw", "nunique"), P_bind=("bind", "mean"), P_top10_risk=("top10", "mean"))
                      .reset_index())

    args.output_dir.mkdir(parents=True, exist_ok=True)
    draws.to_csv(args.output_dir / "national_bootstrap_draws.csv", index=False)
    summary.to_csv(args.output_dir / "national_bootstrap_summary.csv", index=False)
    county_summary.to_csv(args.output_dir / "support_balanced_county_bootstrap.csv", index=False)

    show = summary.loc[summary["allocation_family"].eq("FAMILY_BALANCED") & summary["contract_years"].eq(5)]
    print(f"PASS: {n_draws} paired respondent draws (seed {seed}).")
    print(show[["scenario_id", "M_Q_lower_p025", "M_Q_lower_p50", "M_Q_lower_p975"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
