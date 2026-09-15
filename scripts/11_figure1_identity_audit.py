"""BioLand-US Figure 1 identity audit, aligned to the frozen Stage 07E pipeline.

Purpose
-------
1. Verify the frozen Stage 07E identity b = p*s row by row.
2. Diagnose the manuscript Figure 1c aggregation against Figure 1a.
3. Write the identity-consistent central series that Figure 1c should display.

This script does not estimate or alter the behavioural model.
"""
from __future__ import annotations

from pathlib import Path
import os
import numpy as np
import pandas as pd

ROOT = Path(os.environ.get("BIOLAND_PROJECT", str(Path.cwd())))
TRACK_A = ROOT / "data" / "interim" / "BioLandUS_07E_ExperimentAnchoredBehaviouralAccess.csv"
WORKBOOK = ROOT / "results" / "figures" / "BioLandUS_FigureWorkbook_v5_FINAL.xlsx"
OUTDIR = ROOT / "results" / "validation"
OUTFILE = OUTDIR / "figure1_access_identity.csv"

for path in (TRACK_A, WORKBOOK):
    if not path.exists():
        raise FileNotFoundError(f"Required input not found: {path}")

x = pd.read_csv(TRACK_A, low_memory=False)
required = {
    "offer_2012usd_acre_year",
    "contract_years",
    "land_type",
    "experimental_feedstock",
    "participation_probability",
    "conditional_share_central",
    "behavioural_access_central",
}
missing = sorted(required - set(x.columns))
if missing:
    raise ValueError(f"Stage 07E Track A missing columns: {missing}")

for c in [
    "offer_2012usd_acre_year",
    "contract_years",
    "participation_probability",
    "conditional_share_central",
    "behavioural_access_central",
]:
    x[c] = pd.to_numeric(x[c], errors="raise")

x["identity_residual"] = (
    x["behavioural_access_central"]
    - x["participation_probability"] * x["conditional_share_central"]
)
max_row_resid = float(x["identity_residual"].abs().max())
if max_row_resid > 1e-12:
    raise AssertionError(
        f"BLOCKED: Stage 07E b=p*s identity failed. Max residual={max_row_resid:.3e}"
    )

a5 = x.loc[x["contract_years"].eq(5)].copy()
expected_offers = [50, 100, 200, 300]
observed_offers = sorted(a5["offer_2012usd_acre_year"].dropna().unique().astype(int).tolist())
if observed_offers != expected_offers:
    raise ValueError(f"Expected offers {expected_offers}; observed {observed_offers}")

svals = a5["conditional_share_central"].dropna().unique()
if len(svals) != 1:
    raise AssertionError(f"BLOCKED: central conditional share is not constant: {svals}")
S = float(svals[0])

part = pd.read_excel(WORKBOOK, sheet_name="F2Pa_Participation")
access = pd.read_excel(WORKBOOK, sheet_name="F2Pc_Access")
part["offer"] = pd.to_numeric(part["offer"], errors="raise").astype(int)
access["offer"] = pd.to_numeric(access["offer"], errors="raise").astype(int)

smooth_col = "smooth_margin" if "smooth_margin" in part.columns else "smooth_pct"
part["smooth_p"] = pd.to_numeric(part[smooth_col], errors="raise")
if part["smooth_p"].max() > 1.5:
    part["smooth_p"] = part["smooth_p"] / 100.0

strata = (
    a5.groupby("offer_2012usd_acre_year", as_index=False)
    .agg(
        b_central_min=("behavioural_access_central", "min"),
        b_central_max=("behavioural_access_central", "max"),
        p_stratum_min=("participation_probability", "min"),
        p_stratum_max=("participation_probability", "max"),
        n_land_feedstock_cells=("behavioural_access_central", "size"),
    )
    .rename(columns={"offer_2012usd_acre_year": "offer"})
)
strata["offer"] = strata["offer"].astype(int)

out = part[["offer", "smooth_p"]].merge(strata, on="offer", how="left", validate="1:1")
out["s_central"] = S
out["b_identity_central"] = out["smooth_p"] * S

if "b_mid" in access.columns:
    current = access[["offer", "b_mid"]].copy()
    current["current_plotted_b"] = pd.to_numeric(current["b_mid"], errors="raise")
elif "b_mid_pct" in access.columns:
    current = access[["offer", "b_mid_pct"]].copy()
    current["current_plotted_b"] = pd.to_numeric(current["b_mid_pct"], errors="raise") / 100.0
else:
    current = access[["offer"]].copy()
    current["current_plotted_b"] = np.nan

out = out.merge(current[["offer", "current_plotted_b"]], on="offer", how="left", validate="1:1")
out["current_minus_identity"] = out["current_plotted_b"] - out["b_identity_central"]
out["identity_central_pct"] = 100.0 * out["b_identity_central"]
out["stratum_min_pct"] = 100.0 * out["b_central_min"]
out["stratum_max_pct"] = 100.0 * out["b_central_max"]
out["current_plotted_pct"] = 100.0 * out["current_plotted_b"]
out["row_level_max_abs_residual"] = max_row_resid

inside = (
    out["b_identity_central"].ge(out["b_central_min"] - 1e-12)
    & out["b_identity_central"].le(out["b_central_max"] + 1e-12)
)
if not inside.all():
    raise AssertionError("BLOCKED: identity-consistent central series falls outside Stage 07E central stratum range.")

OUTDIR.mkdir(parents=True, exist_ok=True)
out.to_csv(OUTFILE, index=False)

print("=" * 88)
print("BIOLAND-US | FIGURE 1 IDENTITY AUDIT")
print("=" * 88)
print(f"PASS: Stage 07E row-level b=p*s identity. max |residual| = {max_row_resid:.3e}")
print(f"Frozen central conditional share s = {S:.6f}")
print("")
print("Identity-consistent Figure 1c central series:")
print(
    out[[
        "offer", "smooth_p", "identity_central_pct", "stratum_min_pct",
        "stratum_max_pct", "current_plotted_pct", "current_minus_identity"
    ]].to_string(index=False)
)
print("")
if out["current_minus_identity"].abs().max() > 1e-6:
    print("REQUIRES_CORRECTION: current Figure 1c central points are not the displayed smooth p multiplied by s.")
    print("Use b_identity_central as the central points; use the frozen Stage 07E central min/max as whiskers.")
else:
    print("PASS: current Figure 1c central points are identity-consistent with Figure 1a.")
print(f"Wrote: {OUTFILE}")
