version 18.5
clear all
set more off
set linesize 255

********************************************************************************
* BIOLAND-US CLEAN
* EXPORT TRANSPORT-SENSITIVITY COEFFICIENTS
*
* Purpose
*   Re-estimate the already-audited Stage 04C rent-matched transport models
*   and export full coefficient vectors for national propagation in Python.
*
* Primary behavioural model remains the randomized absolute-dollar model.
* These are robustness / transport sensitivities only.
********************************************************************************

* Run this do-file from the BioLand-US repository root.
* Restricted respondent-level files are never committed to GitHub.
global ROOT "`c(pwd)'"
global INFILE "$ROOT\data\frozen\restricted\KBS_A_Extensive_RentContext_RESTRICTED.dta"
global OUTDIR "$ROOT\results\transport_sensitivity"

capture mkdir "$ROOT\results"
capture mkdir "$OUTDIR"

confirm file "$INFILE"
use "$INFILE", clear

count
assert r(N)==1270
count if rent_matched==1
assert r(N)==1157

capture confirm variable land_f
if _rc encode land, gen(land_f)
capture confirm variable feedstock_f
if _rc encode feedstock, gen(feedstock_f)
capture confirm variable ln_offer
if _rc gen double ln_offer = ln(offer)
capture confirm variable ln_offer_rent_ratio
if _rc gen double ln_offer_rent_ratio = ln(offer/rent_2012_usd_per_acre) if rent_matched==1
capture confirm variable ln_rent_2012
if _rc gen double ln_rent_2012 = ln(rent_2012_usd_per_acre) if rent_matched==1

********************************************************************************
* 1. Ratio-only transport sensitivity
********************************************************************************
logit accept ///
    c.ln_offer_rent_ratio ///
    i.contract ///
    i.land_f ///
    i.feedstock_f ///
    if rent_matched==1, ///
    vce(cluster id)

preserve
clear
set obs 5
gen str32 parameter = ""
gen double value = .
replace parameter = "intercept" in 1
replace parameter = "ln_offer_rent_ratio" in 2
replace parameter = "contract_10yr" in 3
replace parameter = "pasture" in 4
replace parameter = "switchgrass" in 5
replace value = _b[_cons] in 1
replace value = _b[ln_offer_rent_ratio] in 2
replace value = _b[10.contract] in 3
replace value = _b[2.land_f] in 4
replace value = _b[2.feedstock_f] in 5
export delimited using "$OUTDIR\ratio_only_coefficients.csv", replace
restore

********************************************************************************
* 2. Unrestricted offer + rent sensitivity
********************************************************************************
logit accept ///
    c.ln_offer ///
    c.ln_rent_2012 ///
    i.contract ///
    i.land_f ///
    i.feedstock_f ///
    if rent_matched==1, ///
    vce(cluster id)

preserve
clear
set obs 6
gen str32 parameter = ""
gen double value = .
replace parameter = "intercept" in 1
replace parameter = "ln_offer" in 2
replace parameter = "ln_rent" in 3
replace parameter = "contract_10yr" in 4
replace parameter = "pasture" in 5
replace parameter = "switchgrass" in 6
replace value = _b[_cons] in 1
replace value = _b[ln_offer] in 2
replace value = _b[ln_rent_2012] in 3
replace value = _b[10.contract] in 4
replace value = _b[2.land_f] in 5
replace value = _b[2.feedstock_f] in 6
export delimited using "$OUTDIR\offer_plus_rent_coefficients.csv", replace
restore

********************************************************************************
* 3. Compact diagnostics
********************************************************************************
test ln_offer + ln_rent_2012 = 0
local p_ratio_restriction = r(p)

preserve
clear
set obs 1
gen double p_ratio_restriction = `p_ratio_restriction'
gen long n_rent_matched = 1157
gen long n_rent_matched_respondents = 370
export delimited using "$OUTDIR\transport_model_diagnostics.csv", replace
restore

display as text "==============================================================="
display as text "TRANSPORT-SENSITIVITY EXPORT COMPLETE"
display as text "ratio-only:       $OUTDIR\ratio_only_coefficients.csv"
display as text "offer + rent:     $OUTDIR\offer_plus_rent_coefficients.csv"
display as text "diagnostics:      $OUTDIR\transport_model_diagnostics.csv"
display as result "Ratio restriction p-value = " %9.4f `p_ratio_restriction'
display as text "==============================================================="
