import pandas as pd
import pytest

from bioland_us.validation import (
    ValidationError,
    require_columns,
    require_nonnegative,
    require_unique,
    require_unit_interval,
)


def test_require_columns_passes():
    frame = pd.DataFrame({"a": [1], "b": [2]})
    require_columns(frame, ["a", "b"], name="example")


def test_require_columns_fails():
    frame = pd.DataFrame({"a": [1]})
    with pytest.raises(ValidationError):
        require_columns(frame, ["a", "b"], name="example")


def test_require_unique_fails_on_duplicate_key():
    frame = pd.DataFrame({"fips": ["01001", "01001"]})
    with pytest.raises(ValidationError):
        require_unique(frame, ["fips"], name="counties")


def test_require_unit_interval():
    require_unit_interval(pd.Series([0.0, 0.5, 1.0]), name="probability")
    with pytest.raises(ValidationError):
        require_unit_interval(pd.Series([0.0, 1.2]), name="probability")


def test_require_nonnegative():
    require_nonnegative(pd.Series([0.0, 2.0]), name="acreage")
    with pytest.raises(ValidationError):
        require_nonnegative(pd.Series([0.0, -1.0]), name="acreage")
