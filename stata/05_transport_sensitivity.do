version 18.5
clear
set more off

********************************************************************************
* 05  RENT-CONTEXT TRANSPORT SENSITIVITY
*
* Inputs : $RESTRICTED/kbs_choices_long.dta
*          $FROZEN_P/studyA_rent_context.csv   (Python scripts/04_prepare_rents.py)
* Output : $RESULTS_P/transport_coefficients.csv  (public aggregates)
*
* Rent is matched on survey county x land type for respondents who named exactly
* one survey county (decision B11; respondents with several or other counties
* have no unique local rent).
*
* RATIO_ONLY       logit on ln(offer / rent): pure relative-price transport
* OFFER_PLUS_RENT  logit on ln(offer) and ln(rent) separately
* The ratio restriction b_ln_offer + b_ln_rent = 0 is tested and reported.
* The primary transport stays the randomized absolute-dollar model (02).
********************************************************************************

import delimited using "$FROZEN_P/studyA_rent_context.csv", clear ///
    stringcols(1) varnames(1)
keep fips land_type rent_2012usd_per_acre
rename rent_2012usd_per_acre rent
tempfile rent
save `rent'

use "$RESTRICTED/kbs_choices_long.dta", clear
keep if analysis == 1
merge m:1 fips land_type using `rent', keep(master match) gen(_m)
gen byte rent_matched = _m == 3
drop _m

quietly count if rent_matched
local n_match = r(N)
quietly egen byte _tag = tag(id) if rent_matched
quietly count if _tag == 1
local n_resp = r(N)
drop _tag

gen double ln_rent = ln(rent) if rent_matched
gen double ln_ratio = ln_offer - ln_rent

tempname post
tempfile coefs
postfile `post' str16 model str16 term double(b se) long(n clusters) using `coefs'

logit accept ln_ratio contract10 pasture switchgrass if rent_matched, vce(cluster id)
foreach t in _cons ln_ratio contract10 pasture switchgrass {
    post `post' ("RATIO_ONLY") ("`t'") (_b[`t']) (_se[`t']) (e(N)) (e(N_clust))
}

logit accept ln_offer ln_rent contract10 pasture switchgrass if rent_matched, vce(cluster id)
foreach t in _cons ln_offer ln_rent contract10 pasture switchgrass {
    post `post' ("OFFER_PLUS_RENT") ("`t'") (_b[`t']) (_se[`t']) (e(N)) (e(N_clust))
}
test ln_offer + ln_rent = 0
local p_ratio = r(p)
post `post' ("OFFER_PLUS_RENT") ("p_ratio_restr") (`p_ratio') (.) (e(N)) (e(N_clust))
postclose `post'

use `coefs', clear
replace term = "intercept" if term == "_cons"
replace term = "contract_10yr" if term == "contract10"
replace term = "ln_offer_rent_ratio" if term == "ln_ratio"
export delimited using "$RESULTS_P/transport_coefficients.csv", replace

display as result "PASS 05: transport sensitivity on `n_match' rent-matched choices (`n_resp' respondents)."
display as text "  ratio restriction p = " %6.4f `p_ratio'
