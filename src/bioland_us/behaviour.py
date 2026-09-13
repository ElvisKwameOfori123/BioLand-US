"""Behavioural response functions used by BioLand-US."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.special import expit


@dataclass(frozen=True)
class SmoothParticipationModel:
    """Frozen smooth log-dollar participation model."""

    intercept: float
    ln_offer: float
    contract_10yr: float
    pasture: float
    switchgrass: float


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
