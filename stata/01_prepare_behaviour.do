version 18.5
clear
set more off

********************************************************************************
* Build the canonical restricted behavioural analysis file used by the paper.
*
* REQUIRED LOCAL INPUTS (not redistributed)
*   data/restricted/KBS_A_PerennialChoices_LONG_RESTRICTED.dta
*   data/restricted/KBS_A_PerennialChoices_INTENSIVE_CENTRAL_RESTRICTED.dta
********************************************************************************

local long "$RESTRICTED/KBS_A_PerennialChoices_LONG_RESTRICTED.dta"
local intensive "$RESTRICTED/KBS_A_PerennialChoices_INTENSIVE_CENTRAL_RESTRICTED.dta"

confirm file "`long'"
confirm file "`intensive'"

use "`long'", clear

foreach v in id sample_c acc offer contract land_f feedstock_f {
    confirm variable `v'
}

keep if sample_c == 1

assert inlist(acc, 0, 1)
assert inlist(offer, 50, 100, 200, 300)

gen byte contract10 = contract == 10
assert inlist(contract10, 0, 1)

capture confirm string variable land_f
if !_rc {
    gen str12 land_type = land_f
}
else {
    decode land_f, gen(land_type)
}

capture confirm string variable feedstock_f
if !_rc {
    gen str16 experimental_feedstock = feedstock_f
}
else {
    decode feedstock_f, gen(experimental_feedstock)
}

replace land_type = strtrim(land_type)
replace experimental_feedstock = strtrim(experimental_feedstock)

gen byte pasture = lower(land_type) == "pasture"
gen byte switchgrass = lower(experimental_feedstock) == "switchgrass"
gen double ln_offer = ln(offer)

tempfile candidate
save `candidate'

use "`intensive'", clear
foreach v in id feedstock_f land_f {
    confirm variable `v'
}

keep id feedstock_f land_f ///
    intensive_status ///
    share_exact_observed ///
    share_lower_frozen share_upper_frozen ///
    share_central_primary share_central_ipw

isid id feedstock_f land_f
tempfile intensive_keep
save `intensive_keep'

use `candidate', clear
merge 1:1 id feedstock_f land_f using `intensive_keep', keep(master match) nogen

assert missing(share_central_primary) if acc == 0

label variable acc "Accepted perennial-biomass contract"
label variable offer "Randomized annual offer (2012 US$/acre/year)"
label variable contract10 "Ten-year randomized contract"
label variable pasture "Pasture experimental land type"
label variable switchgrass "Switchgrass experimental treatment"
label variable ln_offer "Natural log annual offer"
label variable share_central_primary "Frozen central conditional acreage share"
label variable share_central_ipw "Frozen IPW conditional acreage share"

sort id feedstock_f land_f
compress
save "$FROZEN_R/behaviour_analytic_RESTRICTED.dta", replace

display as result "PASS: restricted behavioural analytic file prepared."
