version 18.5
clear
set more off

********************************************************************************
* 03  INTENSIVE MARGIN: CONDITIONAL ACREAGE SHARE s AMONG ACCEPTED CHOICES
*
* Input  : $RESTRICTED/kbs_choices_long.dta
* Outputs: $FROZEN_R/kbs_accepted_intensive.dta          choice-level shares
*          $RESULTS_P/conditional_acreage_parameters.csv  aggregate s values
*          $RESULTS_P/conditional_acreage_status.csv      status counts
*
* share = stated acres / owned acres of the offered land type (B05).
*
* Status classes for accepted choices (decision B08), mutually exclusive:
*   exact     stated > 0, denominator > 0, share <= 1, no x mark, stated <= total,
*             denominator <= total, A8 components <= total
*   range     not exact, stated > 0 and stated <= total acres:
*             s in [stated/total, 1]
*   missing   stated acres missing: s in [0, 1]
*   residual  anything else: s in [0, 1]
*
* Central rule (B09): exact shares are kept; every other accepted choice takes
* the exact-case mean projected into its own feasible interval.
* Offer response (B13): fractional logit of exact shares on the randomized design.
* IPW robustness (B10): the same projection using a stabilized inverse-
* probability-of-exactness weighted exact mean.
* Acreage-weighted s (B07): central shares weighted by the owned acres of the
* offered land type, the person-to-acreage sensitivity.
********************************************************************************

use "$RESTRICTED/kbs_choices_long.dta", clear
keep if analysis == 1 & accept == 1

gen double share_raw = stated_acres / denom_acres ///
    if stated_acres >= 0 & denom_acres > 0 & !missing(stated_acres, denom_acres)

gen byte exact = stated_acres > 0 & !missing(stated_acres) ///
    & denom_acres > 0 & !missing(denom_acres) ///
    & share_raw <= 1 & denom_xflag == 0 ///
    & !(stated_acres > total_acres & !missing(total_acres)) ///
    & !(denom_acres > total_acres & !missing(total_acres)) ///
    & components_gt_total != 1

gen byte range = !exact & stated_acres > 0 & !missing(stated_acres) ///
    & total_acres > 0 & !missing(total_acres) & stated_acres <= total_acres

gen byte num_missing = !exact & !range & missing(stated_acres)
gen byte residual = !exact & !range & !num_missing
assert exact + range + num_missing + residual == 1

gen str10 intensive_status = cond(exact, "exact", cond(range, "range", ///
    cond(num_missing, "missing", "residual")))

gen double share_exact_observed = share_raw if exact
gen double share_lower = cond(exact, share_raw, cond(range, stated_acres / total_acres, 0))
gen double share_upper = cond(exact, share_raw, 1)
assert inrange(share_lower, 0, 1) & inrange(share_upper, 0, 1)
assert share_lower <= share_upper

* B09 central rule
quietly summarize share_exact_observed
scalar MU_EXACT = r(mean)
gen double share_central = cond(exact, share_raw, ///
    min(share_upper, max(share_lower, MU_EXACT)))

* B10 stabilized IPW reference
logit exact i.offer i.contract_years pasture switchgrass i.a3 i.farmer ///
    c.age i.male c.household_members c.income c.education, vce(cluster id)
predict double p_exact if e(sample), pr
quietly summarize exact if e(sample)
scalar P_EXACT = r(mean)
gen double ipw = P_EXACT / p_exact if exact & !missing(p_exact)
quietly summarize share_exact_observed [aweight = ipw]
scalar MU_IPW = r(mean)
gen double share_central_ipw = cond(exact, share_raw, ///
    min(share_upper, max(share_lower, MU_IPW)))

* B13 offer response of the conditional share: fractional logit on exact cases.
* A flat response supports a single national s (no s(offer) function).
fracreg logit share_exact_observed i.offer i.contract_years pasture switchgrass ///
    if exact, vce(cluster id)
testparm i.offer
local p_offer = r(p)
local n_fr = e(N)
local cl_fr = e(N_clust)
margins offer
matrix FR = r(table)
preserve
    clear
    set obs 4
    gen double offer = .
    gen double share = .
    gen double ll = .
    gen double ul = .
    local offers 50 100 200 300
    forvalues j = 1/4 {
        replace offer = `: word `j' of `offers'' in `j'
        replace share = FR[1, `j'] in `j'
        replace ll = FR[5, `j'] in `j'
        replace ul = FR[6, `j'] in `j'
    }
    gen double joint_offer_p = `p_offer'
    gen long exact_choices = `n_fr'
    gen long clusters = `cl_fr'
    export delimited using "$RESULTS_P/conditional_acreage_by_offer.csv", replace
restore

* B07 acreage weight: owned acres of the offered land type when usable,
* otherwise total acres.
gen double w_acres = cond(denom_acres > 0 & !missing(denom_acres) & denom_xflag == 0, ///
    denom_acres, cond(total_acres > 0, total_acres, .))
quietly count if missing(w_acres)
local n_no_weight = r(N)

foreach v in share_lower share_central share_central_ipw share_upper {
    quietly summarize `v'
    scalar M_`v' = r(mean)
    quietly summarize `v' [aweight = w_acres]
    scalar A_`v' = r(mean)
}
quietly summarize share_exact_observed [aweight = w_acres]
scalar A_EXACT = r(mean)

quietly count
local n_acc = r(N)
quietly count if exact
local n_exact = r(N)

preserve
    contract intensive_status, freq(choices)
    export delimited using "$RESULTS_P/conditional_acreage_status.csv", replace
restore

preserve
    clear
    set obs 9
    gen str32 representation = ""
    gen double share = .
    gen str16 weighting = ""
    local i = 0
    foreach pair in "LOWER_DATA_QUALITY share_lower" "CENTRAL_PRIMARY share_central" ///
        "CENTRAL_IPW_ROBUSTNESS share_central_ipw" "UPPER_DATA_QUALITY share_upper" {
        local i = `i' + 1
        local name : word 1 of `pair'
        local v : word 2 of `pair'
        replace representation = "`name'" in `i'
        replace share = M_`v' in `i'
        replace weighting = "per_choice" in `i'
    }
    replace representation = "EXACT_CASE_MEAN" in 5
    replace share = MU_EXACT in 5
    replace weighting = "per_choice" in 5
    replace representation = "CENTRAL_PRIMARY" in 6
    replace share = A_share_central in 6
    replace weighting = "acreage" in 6
    replace representation = "LOWER_DATA_QUALITY" in 7
    replace share = A_share_lower in 7
    replace weighting = "acreage" in 7
    replace representation = "UPPER_DATA_QUALITY" in 8
    replace share = A_share_upper in 8
    replace weighting = "acreage" in 8
    replace representation = "EXACT_CASE_MEAN" in 9
    replace share = A_EXACT in 9
    replace weighting = "acreage" in 9
    gen long accepted_choices = `n_acc'
    gen long exact_choices = `n_exact'
    export delimited using "$RESULTS_P/conditional_acreage_parameters.csv", replace
restore

keep id choice offer contract_years land_type experimental_feedstock ///
    intensive_status share_exact_observed share_lower share_upper ///
    share_central share_central_ipw w_acres
compress
save "$FROZEN_R/kbs_accepted_intensive.dta", replace

display as result "PASS 03: `n_acc' accepted choices, `n_exact' exact."
display as text "  s central (per choice) = " %8.6f M_share_central
display as text "  s central (acreage)    = " %8.6f A_share_central
display as text "  s IPW                  = " %8.6f M_share_central_ipw
display as text "  accepted choices without an acreage weight: `n_no_weight'"
