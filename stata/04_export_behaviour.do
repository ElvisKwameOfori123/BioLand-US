version 18.5
clear
set more off

********************************************************************************
* 04  EXPORT BEHAVIOURAL INPUTS FOR THE PYTHON NATIONAL MODEL
*
* Restricted (git-ignored):
*   $FROZEN_R/behaviour_bootstrap_input.csv   one row per analysis choice
* Public, non-disclosive aggregates (versioned):
*   $FROZEN_P/behaviour_parameters_public.csv
*
* The public file is the single source of behavioural parameters for Python.
********************************************************************************

use "$RESTRICTED/kbs_choices_long.dta", clear
keep if analysis == 1
merge 1:1 id choice using "$FROZEN_R/kbs_accepted_intensive.dta", ///
    keepusing(intensive_status share_exact_observed share_lower share_upper ///
    share_central share_central_ipw w_acres) assert(master match) nogen

assert !missing(share_central) if accept == 1
assert missing(share_central) if accept == 0

rename accept acc
rename share_lower share_lower_frozen
rename share_upper share_upper_frozen
keep id acc offer contract_years land_type experimental_feedstock fips ///
    denom_acres intensive_status share_exact_observed share_lower_frozen ///
    share_upper_frozen share_central share_central_ipw w_acres
order id acc offer contract_years land_type experimental_feedstock
sort id experimental_feedstock land_type
export delimited using "$FROZEN_R/behaviour_bootstrap_input.csv", replace

********************************************************************************
* Public parameter table
********************************************************************************

import delimited using "$RESULTS_P/participation_coefficients.csv", clear varnames(1)
keep if inlist(model, "SMOOTH", "ACRE_WEIGHTED")
replace term = "contract_10yr" if term == "contract10"
gen str64 parameter = cond(model == "SMOOTH", "smooth_log_dollar_", ///
    "acre_weighted_log_dollar_") + term
gen double value = b
gen str64 role = cond(model == "SMOOTH", "Participation transport coefficient", ///
    "Person-to-acreage sensitivity coefficient")
keep parameter value role
tempfile coefs
save `coefs'

import delimited using "$RESULTS_P/conditional_acreage_parameters.csv", clear varnames(1)
gen str64 parameter = "conditional_acreage_" + lower(representation) ///
    + cond(weighting == "acreage", "_acre_weighted", "")
gen double value = share
gen str64 role = cond(representation == "CENTRAL_PRIMARY" & weighting == "per_choice", ///
    "Central conditional acreage share", ///
    cond(weighting == "acreage", "Person-to-acreage sensitivity", ///
    cond(representation == "EXACT_CASE_MEAN", "Conditional acreage diagnostic", ///
    "Structural sensitivity")))
keep parameter value role
append using `coefs'
gsort -role parameter
format value %18.0g
export delimited using "$FROZEN_P/behaviour_parameters_public.csv", replace datafmt

display as result "PASS 04: behavioural inputs exported."
