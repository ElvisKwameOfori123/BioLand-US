"""Explicit experimental-treatment transfer used by BioLand-US."""

from __future__ import annotations

import pandas as pd

FEEDSTOCK_TRANSFER = {
    "Switchgrass": ("Switchgrass", "HERBACEOUS", "DIRECT_EXPERIMENTAL_SPECIES"),
    "Miscanthus": (
        "Switchgrass",
        "HERBACEOUS",
        "EXPLICIT_TREATMENT_CLASS_TRANSFER_ASSUMPTION",
    ),
    "Energy cane": (
        "Switchgrass",
        "HERBACEOUS",
        "EXPLICIT_TREATMENT_CLASS_TRANSFER_ASSUMPTION",
    ),
    "Poplar": ("Poplar", "WOODY", "DIRECT_EXPERIMENTAL_SPECIES"),
    "Willow": (
        "Poplar",
        "WOODY",
        "EXPLICIT_TREATMENT_CLASS_TRANSFER_ASSUMPTION",
    ),
    "Eucalyptus": (
        "Poplar",
        "WOODY",
        "EXPLICIT_TREATMENT_CLASS_TRANSFER_ASSUMPTION",
    ),
    "Pine": (
        "Poplar",
        "WOODY",
        "EXPLICIT_TREATMENT_CLASS_TRANSFER_ASSUMPTION",
    ),
}


def apply_feedstock_transfer(
    frame: pd.DataFrame,
    *,
    feedstock_col: str = "feedstock",
) -> pd.DataFrame:
    """Attach experimental archetype and transfer provenance to POLYSYS rows."""
    out = frame.copy()
    mapped = out[feedstock_col].map(FEEDSTOCK_TRANSFER)

    if mapped.isna().any():
        missing = sorted(out.loc[mapped.isna(), feedstock_col].astype(str).unique())
        raise ValueError(f"Unmapped perennial feedstocks: {missing}")

    out["experimental_feedstock"] = mapped.map(lambda x: x[0])
    out["treatment_class"] = mapped.map(lambda x: x[1])
    out["transfer_status"] = mapped.map(lambda x: x[2])
    return out
