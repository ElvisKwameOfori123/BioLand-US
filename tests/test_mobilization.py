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
    assert row.A_M == 0
    assert row.Q_M == 0
