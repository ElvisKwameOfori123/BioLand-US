version 18.5
clear
set more off

********************************************************************************
* Export the minimum restricted behavioural inputs needed by the Python stages.
* These files remain restricted and must not be committed to GitHub.
********************************************************************************

use "$FROZEN_R/behaviour_analytic_RESTRICTED.dta", clear

keep id acc offer contract land_type experimental_feedstock ///
    share_central_primary

rename contract contract_years
rename share_central_primary share_central

order id acc offer contract_years land_type experimental_feedstock share_central
sort id experimental_feedstock land_type

export delimited using ///
    "$FROZEN_R/behaviour_bootstrap_input.csv", ///
    replace

quietly estimates restore extensive_smooth

preserve
clear
set obs 5
gen str24 parameter = ""
gen double value = .
replace parameter = "intercept"     in 1
replace parameter = "ln_offer"      in 2
replace parameter = "contract_10yr" in 3
replace parameter = "pasture"       in 4
replace parameter = "switchgrass"   in 5
replace value = _b[_cons]       in 1
replace value = _b[ln_offer]    in 2
replace value = _b[contract10]  in 3
replace value = _b[pasture]     in 4
replace value = _b[switchgrass] in 5
export delimited using "$FROZEN_R/behaviour_parameters.csv", replace
restore

display as result "PASS: restricted behavioural exports written."
