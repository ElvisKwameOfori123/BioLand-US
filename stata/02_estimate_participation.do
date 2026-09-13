version 18.5
clear
set more off

********************************************************************************
* Extensive-margin models.
*
* Categorical randomized-offer model = experimental identification.
* Smooth log-dollar model            = national transport function.
********************************************************************************

use "$FROZEN_R/behaviour_analytic_RESTRICTED.dta", clear

logit acc ib50.offer contract10 pasture switchgrass, vce(cluster id)
estimates store extensive_categorical

margins, at(offer=(50 100 200 300)) post
matrix M = r(table)

preserve
clear
set obs 4
gen double offer = .
gen double margin = .
replace offer = 50  in 1
replace offer = 100 in 2
replace offer = 200 in 3
replace offer = 300 in 4
forvalues j = 1/4 {
    replace margin = M[1,`j'] in `j'
}
export delimited using "$RESULTS_R/extensive_categorical_margins.csv", replace
restore

logit acc ln_offer contract10 pasture switchgrass, vce(cluster id)
estimates store extensive_smooth

scalar B0 = _b[_cons]
scalar B1 = _b[ln_offer]
scalar B2 = _b[contract10]
scalar B3 = _b[pasture]
scalar B4 = _b[switchgrass]

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
replace value = B0 in 1
replace value = B1 in 2
replace value = B2 in 3
replace value = B3 in 4
replace value = B4 in 5
export delimited using "$RESULTS_R/extensive_smooth_coefficients.csv", replace
restore

margins, at(offer=(50 100 200 300)) expression( ///
    invlogit(_b[_cons] + _b[ln_offer]*ln(offer) + ///
    _b[contract10]*contract10 + _b[pasture]*pasture + ///
    _b[switchgrass]*switchgrass) ///
)

matrix MS = r(table)
preserve
clear
set obs 4
gen double offer = .
gen double margin = .
replace offer = 50  in 1
replace offer = 100 in 2
replace offer = 200 in 3
replace offer = 300 in 4
forvalues j = 1/4 {
    replace margin = MS[1,`j'] in `j'
}
export delimited using "$RESULTS_R/extensive_smooth_margins.csv", replace
restore

display as result "PASS: extensive behavioural models estimated."
