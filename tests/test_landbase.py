import numpy as np
import pytest

from bioland_us.landbase import InfeasibleAllocation, allocate_residual


def test_proportional_allocation_closes_residual():
    x = allocate_residual(300.0, np.array([1.0, 2.0]))
    assert np.allclose(x, [100.0, 200.0])


def test_zero_weights_fall_back_to_equal_shares():
    x = allocate_residual(90.0, np.array([0.0, 0.0, 0.0]))
    assert np.allclose(x, [30.0, 30.0, 30.0])


def test_upper_bound_redistributes_excess():
    x = allocate_residual(100.0, np.array([1.0, 1.0]), upper=np.array([20.0, np.inf]))
    assert np.allclose(x, [20.0, 80.0])


def test_lower_bound_is_respected():
    x = allocate_residual(100.0, np.array([1.0, 9.0]), lower=np.array([30.0, 0.0]))
    assert np.allclose(x.sum(), 100.0)
    assert x[0] >= 30.0 - 1e-9


def test_infeasible_bounds_raise():
    with pytest.raises(InfeasibleAllocation):
        allocate_residual(100.0, np.array([1.0, 1.0]), upper=np.array([10.0, 10.0]))
