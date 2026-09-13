"""Explicit treatment-class transfer from Study-A feedstocks to POLYSYS resources."""

from __future__ import annotations

import pandas as pd


_CANONICAL = {
    "switchgrass": ("Switchgrass", "Switchgrass", "HERBACEOUS", True),
    "miscanthus": ("Miscanthus", "Switchgrass", "HERBACEOUS", False),
    "energy cane": ("Energy cane", "Switchgrass", "HERBACEOUS", False),
    "poplar": ("Poplar", "Poplar", "WOODY", True),
    "willow": ("Willow", "Poplar", "WOODY", False),
    "eucalyptus": ("Eucalyptus", "Poplar", "WOODY", False),
    "pine": ("Pine", "Poplar", "WOODY", False),
}


def normalize_feedstock(value: object) -> str:
    """Normalize POLYSYS resource spelling for transfer lookup."""
    return " ".join(
        str(value).strip().lower().replace("_", " ").replace("-", " ").split()
    )


def apply_feedstock_transfer(
    frame: pd.DataFrame,
    *,
    feedstock_col: str = "feedstock",
) -> pd.DataFrame:
    """Attach the frozen experimental-archetype transfer and provenance.

    Central mapping:
        Switchgrass, Miscanthus, Energy cane -> Switchgrass archetype
        Poplar, Willow, Eucalyptus, Pine      -> Poplar archetype

    Untested species are explicit treatment-class transfers, not observations
    from the experiment.
    """
    out = frame.copy()
    key = out[feedstock_col].map(normalize_feedstock)
    mapped = key.map(_CANONICAL)

    if mapped.isna().any():
        missing = sorted(out.loc[mapped.isna(), feedstock_col].astype(str).unique())
        raise ValueError(f"Unmapped perennial feedstocks: {missing}")

    out["feedstock"] = mapped.map(lambda x: x[0])
    out["experimental_feedstock"] = mapped.map(lambda x: x[1])
    out["treatment_class"] = mapped.map(lambda x: x[2])
    out["directly_tested_species"] = mapped.map(lambda x: x[3]).astype(bool)
    out["transfer_status"] = out["directly_tested_species"].map(
        {
            True: "DIRECT_EXPERIMENTAL_SPECIES",
            False: "EXPLICIT_TREATMENT_CLASS_TRANSFER_ASSUMPTION",
        }
    )
    return out
