"""Prepare compatible Crop and Pasture land surfaces.

Preferred input is the frozen joint Census land-base table with EQUAL, OWNED
and RENTED completion surfaces. The script writes one clear file per structural
surface and uses JOINT_EQUAL as the deterministic central land base.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from bioland_us.validation import require_nonnegative, require_unique


STRUCTURES = {
    "JOINT_EQUAL": ("B_crop_equal_acres", "B_pasture_equal_acres"),
    "JOINT_OWNED": ("B_crop_owned_acres", "B_pasture_owned_acres"),
    "JOINT_RENTED": ("B_crop_rented_acres", "B_pasture_rented_acres"),
}


def build_long(frame: pd.DataFrame, crop_col: str, pasture_col: str) -> pd.DataFrame:
    crop = pd.DataFrame(
        {
            "fips": frame["fips"].astype("string").str.zfill(5),
            "land_type": "Crop",
            "B": pd.to_numeric(frame[crop_col], errors="coerce"),
        }
    )
    pasture = pd.DataFrame(
        {
            "fips": frame["fips"].astype("string").str.zfill(5),
            "land_type": "Pasture",
            "B": pd.to_numeric(frame[pasture_col], errors="coerce"),
        }
    )
    out = pd.concat([crop, pasture], ignore_index=True)
    require_nonnegative(out["B"], name=f"{crop_col}/{pasture_col}", allow_missing=True)
    require_unique(out, ["fips", "land_type"], name="compatible land")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/frozen/public/compatible_land.csv"),
    )
    parser.add_argument(
        "--structures-dir",
        type=Path,
        default=Path("data/frozen/public/land_structures"),
    )
    args = parser.parse_args()

    x = pd.read_csv(args.input, dtype={"fips": "string"}, low_memory=False)
    if "fips" not in x.columns:
        raise ValueError("Completed Census land input lacks fips.")
    require_unique(x, ["fips"], name="completed Census land")

    available = {
        name: cols
        for name, cols in STRUCTURES.items()
        if all(col in x.columns for col in cols)
    }

    if available:
        args.structures_dir.mkdir(parents=True, exist_ok=True)
        outputs = {}
        for name, (crop_col, pasture_col) in available.items():
            out = build_long(x, crop_col, pasture_col)
            path = args.structures_dir / f"{name}.csv"
            out.to_csv(path, index=False)
            outputs[name] = out

        if "JOINT_EQUAL" not in outputs:
            raise ValueError("JOINT_EQUAL land surface is required as the central case.")
        central = outputs["JOINT_EQUAL"]
    else:
        # Transparent fallback for a pre-completed component table.
        required = {
            "cropland_total",
            "cropland_pastured_only",
            "pasture_excluding_cropland_and_woodland",
        }
        missing = sorted(required - set(x.columns))
        if missing:
            raise ValueError(
                "Land input contains neither frozen structural surfaces nor "
                f"the required completed components: {missing}"
            )
        for col in required:
            x[col] = pd.to_numeric(x[col], errors="coerce")
            require_nonnegative(x[col], name=col)
        if (x["cropland_pastured_only"] > x["cropland_total"] + 1e-9).any():
            raise ValueError("Cropland pastured only exceeds total cropland.")

        x["B_crop_equal_acres"] = x["cropland_total"] - x["cropland_pastured_only"]
        x["B_pasture_equal_acres"] = (
            x["cropland_pastured_only"]
            + x["pasture_excluding_cropland_and_woodland"]
        )
        central = build_long(
            x,
            "B_crop_equal_acres",
            "B_pasture_equal_acres",
        )
        args.structures_dir.mkdir(parents=True, exist_ok=True)
        central.to_csv(args.structures_dir / "JOINT_EQUAL.csv", index=False)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    central.to_csv(args.output, index=False)

    print("PASS: compatible land surfaces written.")
    print(f"  central={args.output}")
    print(f"  structural directory={args.structures_dir}")
    print(f"  available structures={', '.join(sorted(available)) if available else 'JOINT_EQUAL'}")


if __name__ == "__main__":
    main()
