"""Behavioural response functions used by BioLand-US."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit

PUBLIC_PARAMETERS = Path("data/frozen/public/behaviour_parameters_public.csv")
INTENSIVE_REPRESENTATIONS = [
    "LOWER_DATA_QUALITY",
    "CENTRAL_IPW_ROBUSTNESS",
    "CENTRAL_PRIMARY",
    "UPPER_DATA_QUALITY",
]


@dataclass(frozen=True)
class SmoothParticipationModel:
    """Frozen smooth log-dollar participation model."""

    intercept: float
    ln_offer: float
    contract_10yr: float
    pasture: float
    switchgrass: float

    def as_array(self) -> np.ndarray:
        return np.array(
            [self.intercept, self.ln_offer, self.contract_10yr, self.pasture, self.switchgrass]
        )


def load_public_parameters(path: Path = PUBLIC_PARAMETERS) -> dict[str, float]:
    """Read the Stata-exported, non-disclosive behavioural parameters."""
    table = pd.read_csv(path)
    return dict(zip(table["parameter"], table["value"].astype(float)))


def participation_model(params: dict[str, float], weighting: str = "PER_CHOICE") -> SmoothParticipationModel:
    """Smooth model from the public parameters; ACRE_WEIGHTED is the B07 sensitivity."""
    prefix = {"PER_CHOICE": "smooth_log_dollar_", "ACRE_WEIGHTED": "acre_weighted_log_dollar_"}[weighting]
    return SmoothParticipationModel(
        **{term: params[prefix + term] for term in
           ("intercept", "ln_offer", "contract_10yr", "pasture", "switchgrass")}
    )


def conditional_share(params: dict[str, float], representation: str, weighting: str = "PER_CHOICE") -> float:
    """Conditional acreage share s for one intensive representation."""
    suffix = "_acre_weighted" if weighting == "ACRE_WEIGHTED" else ""
    return params[f"conditional_acreage_{representation.lower()}{suffix}"]


def predict_participation(
    offer: pd.Series | np.ndarray | float,
    contract_years: pd.Series | np.ndarray | int,
    land_type: pd.Series | np.ndarray | str,
    experimental_feedstock: pd.Series | np.ndarray | str,
    model: SmoothParticipationModel,
) -> np.ndarray:
    """Predict contract participation probability.

    Missing / unsupported offers remain missing. Offers must be strictly positive.
    """
    offer_arr = np.asarray(offer, dtype=float)
    years = np.asarray(contract_years)
    land = pd.Series(np.asarray(land_type)).astype("string").str.strip().str.lower()
    feed = (
        pd.Series(np.asarray(experimental_feedstock))
        .astype("string")
        .str.strip()
        .str.lower()
    )

    if np.any((offer_arr <= 0) & np.isfinite(offer_arr)):
        raise ValueError("Contract offers must be strictly positive when observed.")

    eta = (
        model.intercept
        + model.ln_offer * np.log(offer_arr)
        + model.contract_10yr * (years == 10).astype(float)
        + model.pasture * land.eq("pasture").to_numpy(dtype=float)
        + model.switchgrass * feed.eq("switchgrass").to_numpy(dtype=float)
    )
    p = expit(eta)
    p[~np.isfinite(offer_arr)] = np.nan
    return p


def behavioural_access(
    participation_probability: pd.Series | np.ndarray,
    conditional_share: float | pd.Series | np.ndarray,
) -> np.ndarray:
    """Return b = p × s while preserving missing participation as missing."""
    p = np.asarray(participation_probability, dtype=float)
    s = np.asarray(conditional_share, dtype=float)

    if np.any((p < 0) | (p > 1)):
        raise ValueError("Participation probability must lie in [0, 1].")
    if np.any((s < 0) | (s > 1)):
        raise ValueError("Conditional acreage share must lie in [0, 1].")

    return p * s
