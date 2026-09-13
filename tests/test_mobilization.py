import numpy as np
import pandas as pd

from bioland_us.mobilization import apply_capacity_constraint


def test_zero_capacity_binding_rule():
    frame = pd.DataFrame(
        {
            "allocation_family": ["FAMILY_01"],
            "fips": ["01001"],
            "land_type": ["Crop"],
            "scenario_id": ["example"],
            "contract_years": [5],
            "A_P": [100.0],
            "Q_P": [500.0],
            "B": [200.0],
            "K": [0.0],
        }
    )

    out = apply_capacity_constraint(frame)
    row = out.iloc[0]

    assert row.zero_capacity_binding == 1
    assert np.isinf(row.rho)
    assert row["lambda"] == 0
    assert row.A_M_known == 0
    assert row.Q_M_known == 0
    assert row.A_M_full_lower == 0
    assert row.A_M_full_upper == 0
    assert row.Q_M_full_lower == 0
    assert row.Q_M_full_upper == 0


def test_unsupported_cell_is_not_zero_capacity():
    frame = pd.DataFrame(
        {
            "allocation_family": ["FAMILY_01"],
            "fips": ["01001"],
            "land_type": ["Crop"],
            "scenario_id": ["example"],
            "contract_years": [5],
            "A_P": [100.0],
            "Q_P": [500.0],
            "B": [200.0],
            "K": [np.nan],
        }
    )

    out = apply_capacity_constraint(frame)
    row = out.iloc[0]

    assert row.capacity_status == "UNSUPPORTED"
    assert np.isnan(row["lambda"])
    assert np.isnan(row.A_M_known)
    assert row.A_M_full_lower == 0
    assert row.A_M_full_upper == 100
    assert row.Q_M_full_lower == 0
    assert row.Q_M_full_upper == 500
