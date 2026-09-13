"""Fail-fast validation helpers used across BioLand-US stages."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


class ValidationError(ValueError):
    """Raised when a frozen scientific or data-integrity condition fails."""


def require_columns(frame: pd.DataFrame, columns: Iterable[str], *, name: str) -> None:
    """Require a dataframe to contain all named columns."""
    required = list(columns)
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValidationError(f"{name}: missing required columns: {missing}")


def require_unique(frame: pd.DataFrame, columns: Iterable[str], *, name: str) -> None:
    """Require uniqueness of an identifier or compound key."""
    key = list(columns)
    duplicate = frame.duplicated(key, keep=False)
    if duplicate.any():
        count = int(duplicate.sum())
        raise ValidationError(f"{name}: {count} rows violate uniqueness of {key}")


def require_unit_interval(values: pd.Series, *, name: str, allow_missing: bool = False) -> None:
    """Require probabilities / shares to remain in [0, 1]."""
    series = pd.to_numeric(values, errors="coerce")

    if not allow_missing and series.isna().any():
        raise ValidationError(f"{name}: missing values are not allowed")

    finite = series.dropna()
    bad = (finite < 0) | (finite > 1)
    if bad.any():
        raise ValidationError(
            f"{name}: {int(bad.sum())} values fall outside the unit interval"
        )


def require_nonnegative(values: pd.Series, *, name: str, allow_missing: bool = False) -> None:
    """Require a numeric quantity to be non-negative."""
    series = pd.to_numeric(values, errors="coerce")

    if not allow_missing and series.isna().any():
        raise ValidationError(f"{name}: missing values are not allowed")

    finite = series.dropna()
    bad = finite < 0
    if bad.any():
        raise ValidationError(f"{name}: {int(bad.sum())} negative values found")


def require_close(
    observed: float,
    expected: float,
    *,
    tolerance: float,
    name: str,
) -> None:
    """Require two scalar values to agree within an absolute tolerance."""
    if not np.isclose(observed, expected, rtol=0.0, atol=tolerance):
        raise ValidationError(
            f"{name}: observed={observed!r}, expected={expected!r}, "
            f"tolerance={tolerance}"
        )
