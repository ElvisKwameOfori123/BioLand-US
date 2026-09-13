version 18.5
clear
set more off

********************************************************************************
* Regression tests against the frozen validated behavioural analysis.
********************************************************************************

use "$FROZEN_R/behaviour_analytic_RESTRICTED.dta", clear

count
assert r(N) == 1270

egen byte tag_id = tag(id)
count if tag_id
assert r(N) == 403
drop tag_id

count if acc == 1
assert r(N) == 356

logit acc ln_offer contract10 pasture switchgrass, vce(cluster id)

assert abs(_b[_cons]       - (-6.017543)) < 1e-6
assert abs(_b[ln_offer]    - 0.943158)    < 1e-6
assert abs(_b[contract10]  - (-0.081661)) < 1e-6
assert abs(_b[pasture]     - 0.0214773)   < 1e-6
assert abs(_b[switchgrass] - 0.746083)    < 1e-6

margins, at(offer=(50 100 200 300)) expression( ///
    invlogit(_b[_cons] + _b[ln_offer]*ln(offer) + ///
    _b[contract10]*contract10 + _b[pasture]*pasture + ///
    _b[switchgrass]*switchgrass) ///
)
matrix M = r(table)

assert abs(M[1,1] - 0.1258850) < 1e-6
assert abs(M[1,2] - 0.2148008) < 1e-6
assert abs(M[1,3] - 0.3407330) < 1e-6
assert abs(M[1,4] - 0.4280200) < 1e-6

quietly summarize share_central_primary if acc == 1, meanonly
assert abs(r(mean) - 0.863337) < 1e-6

display as text "================================================================================"
display as result "PASS_FROZEN: behavioural regression tests reproduce the manuscript analysis."
display as text "================================================================================"
