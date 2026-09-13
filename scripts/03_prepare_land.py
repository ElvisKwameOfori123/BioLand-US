"""Build compatible Crop and Pasture pools from completed Census components.

The suppression-completion step is upstream of this transparent public calculation.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from bioland_us.validation import require_columns, require_nonnegative, require_unique


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/frozen/public/compatible_land.csv"),
    )
    args = parser.parse_args()

    x = pd.read_csv(args.input, dtype={"fips": "string"})
    require_columns(
        x,
        [
            "fips",
            "cropland_total",
            "cropland_pastured_only",
            "pasture_excluding_cropland_and_woodland",
        ],
        name="completed Census land components",
    )
    require_unique(x, ["fips"], name="completed Census land components")

    for col in [
        "cropland_total",
        "cropland_pastured_only",
        "pasture_excluding_cropland_and_woodland",
    ]:
        require_nonnegative(x[col], name=col)

    if (x["cropland_pastured_only"] > x["cropland_total"] + 1e-9).any():
        raise ValueError("CroplandPasturedOnly exceeds CroplandTotal.")

    crop = pd.DataFrame(
        {
            "fips": x["fips"].astype("string").str.zfill(5),
            "land_type": "Crop",
            "B": x["cropland_total"] - x["cropland_pastured_only"],
        }
    )
    pasture = pd.DataFrame(
        {
            "fips": x["fips"].astype("string").str.zfill(5),
            "land_type": "Pasture",
            "B": x["cropland_pastured_only"]
            + x["pasture_excluding_cropland_and_woodland"],
        }
    )
    out = pd.concat([crop, pasture], ignore_index=True)
    require_nonnegative(out["B"], name="compatible land B")
    require_unique(out, ["fips", "land_type"], name="compatible land")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(f"PASS: compatible land written to {args.output}")


if __name__ == "__main__":
    main()
