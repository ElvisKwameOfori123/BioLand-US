from __future__ import annotations

import pandas as pd

from bioland_us.feedstocks import apply_feedstock_transfer


def test_frozen_feedstock_transfer():
    feedstocks = [
        "Switchgrass",
        "Miscanthus",
        "Energy cane",
        "Poplar",
        "Willow",
        "Eucalyptus",
        "Pine",
    ]
    out = apply_feedstock_transfer(pd.DataFrame({"feedstock": feedstocks}))

    herb = out.loc[out["treatment_class"].eq("HERBACEOUS")]
    woody = out.loc[out["treatment_class"].eq("WOODY")]

    assert set(herb["feedstock"]) == {"Switchgrass", "Miscanthus", "Energy cane"}
    assert set(herb["experimental_feedstock"]) == {"Switchgrass"}
    assert set(woody["feedstock"]) == {"Poplar", "Willow", "Eucalyptus", "Pine"}
    assert set(woody["experimental_feedstock"]) == {"Poplar"}
    assert out["transfer_status"].eq("DIRECT_EXPERIMENTAL_SPECIES").sum() == 2
