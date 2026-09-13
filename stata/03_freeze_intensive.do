version 18.5
clear
set more off

********************************************************************************
* Conditional acreage architecture.
* The accepted-choice reconstruction is already frozen at respondent-choice level.
********************************************************************************

use "$FROZEN_R/behaviour_analytic_RESTRICTED.dta", clear
keep if acc == 1

count
assert r(N) == 356

count if !missing(share_exact_observed)
local n_exact = r(N)
assert `n_exact' == 203

count if intensive_status == "bounded_range"
local n_range = r(N)

quietly summarize share_exact_observed, meanonly
scalar S_EXACT = r(mean)

quietly summarize share_central_primary, meanonly
scalar S_CENTRAL = r(mean)

quietly summarize share_central_ipw, meanonly
scalar S_IPW = r(mean)

quietly summarize share_lower_frozen, meanonly
scalar S_LOWER = r(mean)

quietly summarize share_upper_frozen, meanonly
scalar S_UPPER = r(mean)

preserve
clear
set obs 5
gen str32 representation = ""
gen double share = .

replace representation = "LOWER_DATA_QUALITY"      in 1
replace representation = "CENTRAL_PRIMARY"         in 2
replace representation = "CENTRAL_IPW_ROBUSTNESS"  in 3
replace representation = "EXACT_CASE_MEAN"         in 4
replace representation = "UPPER_DATA_QUALITY"      in 5

replace share = S_LOWER   in 1
replace share = S_CENTRAL in 2
replace share = S_IPW     in 3
replace share = S_EXACT   in 4
replace share = S_UPPER   in 5

export delimited using "$RESULTS_R/conditional_acreage_parameters.csv", replace
restore

display as result "PASS: intensive conditional-acreage architecture verified."
display as text "Exact accepted choices: `n_exact'"
display as text "Bounded-range accepted choices: `n_range'"
