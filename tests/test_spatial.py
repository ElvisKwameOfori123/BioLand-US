import numpy as np
import pandas as pd

from bioland_us.mobilization import apply_capacity_constraint
from bioland_us.spatial import county_central_summary


def pools(K_crop, K_pasture):
    frame = pd.DataFrame(
        {
            "allocation_family": ["FAMILY_01", "FAMILY_01"],
            "scenario_id": ["example", "example"],
            "contract_years": [5, 5],
            "fips": ["01001", "01001"],
            "land_type": ["Crop", "Pasture"],
            "A_P": [100.0, 10.0],
            "Q_P": [500.0, 50.0],
            "B": [1000.0, 1000.0],
            "K": [K_crop, K_pasture],
        }
    )
    return apply_capacity_constraint(frame)


def test_spare_pasture_cannot_hide_binding_crop_pool():
    # Summed capacity (50 + 500) exceeds summed acreage (110), but crop binds.
    county = county_central_summary(pools(50.0, 500.0)).iloc[0]
    assert county.binding == 1
    assert county.rho == 2.0
    assert np.isclose(county.M_Q_full_lower, (250.0 + 50.0) / 550.0)


def test_unresolved_pool_leaves_county_pressure_unknown():
    county = county_central_summary(pools(np.nan, 500.0)).iloc[0]
    assert np.isnan(county.rho)
    assert np.isnan(county.binding)
    assert county.M_Q_full_lower < county.M_Q_full_upper
