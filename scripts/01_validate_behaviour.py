"""Check that the restricted Study-A export agrees with the public parameters.

Run after stata/00_run_behaviour.do. Fails if the choice-level export and the
non-disclosive parameter table disagree, so the bootstrap never runs on stale
inputs.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from bioland_us.behaviour import conditional_share, load_public_parameters
from bioland_us.validation import require_close, require_columns, require_unit_interval


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap-input", type=Path,
                        default=Path("data/frozen/restricted/behaviour_bootstrap_input.csv"))
    args = parser.parse_args()

    params = load_public_parameters()
    x = pd.read_csv(args.bootstrap_input, dtype={"id": "string"})
    require_columns(x, ["id", "acc", "offer", "contract_years", "land_type", "experimental_feedstock",
                        "share_exact_observed", "share_lower_frozen", "share_upper_frozen", "share_central"],
                    name="behaviour bootstrap input")
    require_unit_interval(x["acc"], name="acc")
    require_unit_interval(x["share_central"], name="share_central", allow_missing=True)
    if x["id"].isna().any():
        raise ValueError("Respondent id contains missing values.")
    if x.loc[x["acc"].eq(1), "share_central"].isna().any():
        raise ValueError("Accepted choice without a central conditional share.")

    accepted = x.loc[x["acc"].eq(1)]
    require_close(float(accepted["share_central"].mean()), conditional_share(params, "CENTRAL_PRIMARY"),
                  tolerance=1e-9, name="central conditional share")
    require_close(float(accepted["share_exact_observed"].mean()), conditional_share(params, "EXACT_CASE_MEAN"),
                  tolerance=1e-9, name="exact-case mean")

    print(f"PASS: {len(x):,} choices, {x['id'].nunique():,} respondents, {int(x['acc'].sum()):,} accepts; "
          "export matches public parameters.")


if __name__ == "__main__":
    main()
