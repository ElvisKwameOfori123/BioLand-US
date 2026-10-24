version 18.5
clear
set more off

********************************************************************************
* 02  EXTENSIVE MARGIN: CONTRACT PARTICIPATION
*
* Input  : $RESTRICTED/kbs_choices_long.dta
* Outputs: $RESULTS_P/participation_coefficients.csv   all models, b / se / p
*          $RESULTS_P/participation_margins.csv        p at the four offers
*          $RESULTS_P/participation_loco.csv           leave-one-county-out
*
* M1 CATEGORICAL  i.offer (randomized; experimental identification)
* M2 SMOOTH       ln(offer) (national transport function, decision B06)
* M3 ACRE_WEIGHT  M2 weighted by owned acres of the offered land type:
*                 person-to-acreage sensitivity (decision B07)
* LOCO            M2 refitted dropping one survey county at a time
*
* All models cluster standard errors by respondent.
********************************************************************************

use "$RESTRICTED/kbs_choices_long.dta", clear
keep if analysis == 1

tempname post
tempfile coefs
postfile `post' str16 model str16 term double(b se p) long(n clusters) using `coefs'

capture program drop _post_model
program define _post_model
    args post model
    local n = e(N)
    local cl = e(N_clust)
    tempname B V
    matrix `B' = e(b)
    matrix `V' = e(V)
    local names : colnames `B'
    local k = colsof(`B')
    forvalues j = 1/`k' {
        local t : word `j' of `names'
        if strpos("`t'", "b.") | strpos("`t'", "o.") continue
        local se = sqrt(`V'[`j', `j'])
        local z = `B'[1, `j'] / `se'
        post `post' ("`model'") ("`t'") (`B'[1, `j']) (`se') ///
            (2 * normal(-abs(`z'))) (`n') (`cl')
    }
end

* M1 categorical randomized offer
logit accept ib50.offer contract10 pasture switchgrass, vce(cluster id)
_post_model `post' CATEGORICAL
margins offer, post
matrix M1 = r(table)

* M2 smooth log-dollar transport model
logit accept ln_offer contract10 pasture switchgrass, vce(cluster id)
estimates store smooth
_post_model `post' SMOOTH
test ln_offer
local p_ln_offer = r(p)

* M3 acreage-weighted smooth model
gen double w_acres = denom_acres if denom_acres > 0 & denom_xflag == 0
quietly count if missing(w_acres)
local n_no_weight = r(N)
logit accept ln_offer contract10 pasture switchgrass [pweight = w_acres], ///
    vce(cluster id)
_post_model `post' ACRE_WEIGHTED

* Leave one survey county out (respondents in several or other counties stay in).
levelsof fips if fips != "", local(fipsvals)
foreach f of local fipsvals {
    quietly logit accept ln_offer contract10 pasture switchgrass ///
        if fips != "`f'", vce(cluster id)
    _post_model `post' LOCO_`f'
}
postclose `post'

preserve
    use `coefs', clear
    replace term = "intercept" if term == "_cons"
    export delimited using "$RESULTS_P/participation_coefficients.csv", replace
restore

* Predictive margins at the randomized offers: categorical vs smooth.
estimates restore smooth
margins, at(ln_offer = (`=ln(50)' `=ln(100)' `=ln(200)' `=ln(300)'))
matrix M2 = r(table)

preserve
    clear
    set obs 4
    gen double offer = .
    gen double p_categorical = .
    gen double p_smooth = .
    local offers 50 100 200 300
    forvalues j = 1/4 {
        replace offer = `: word `j' of `offers'' in `j'
        replace p_categorical = M1[1, `j'] in `j'
        replace p_smooth = M2[1, `j'] in `j'
    }
    gen double smooth_minus_categorical = p_smooth - p_categorical
    gen double ll_categorical = .
    gen double ul_categorical = .
    forvalues j = 1/4 {
        replace ll_categorical = M1[5, `j'] in `j'
        replace ul_categorical = M1[6, `j'] in `j'
    }
    export delimited using "$RESULTS_P/participation_margins.csv", replace
restore

* Smooth participation curve across the tested offer range (figure 1a).
local grid ""
forvalues k = 0/24 {
    local grid "`grid' `=ln(50) + `k' * (ln(300) - ln(50)) / 24'"
}
estimates restore smooth
margins, at(ln_offer = (`grid'))
matrix MC = r(table)
preserve
    clear
    set obs 25
    gen double offer = .
    gen double p_smooth = .
    gen double ll = .
    gen double ul = .
    forvalues k = 1/25 {
        replace offer = exp(ln(50) + (`k' - 1) * (ln(300) - ln(50)) / 24) in `k'
        replace p_smooth = MC[1, `k'] in `k'
        replace ll = MC[5, `k'] in `k'
        replace ul = MC[6, `k'] in `k'
    }
    export delimited using "$RESULTS_P/participation_curve.csv", replace
restore

display as result "PASS 02: participation models estimated."
display as text "  ln(offer) test p = " %6.4f `p_ln_offer'
display as text "  choices without a usable acreage weight (dropped in M3): `n_no_weight'"
program drop _post_model
