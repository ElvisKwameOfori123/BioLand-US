version 18.5
clear
set more off

********************************************************************************
* 01  IMPORT THE RAW KBS SURVEY AND BUILD THE CANONICAL CHOICE FILE
*
* Input  : $KBS_ZIP (raw KBS LTER archive, knb-lter-kbs.124.2)
* Outputs: $RESTRICTED/kbs_respondents.dta   one row per returned questionnaire
*          $RESTRICTED/kbs_choices_long.dta  four perennial choices per respondent
*          $RESULTS_P/sample_flow.csv        non-disclosive sample counts
*
* Decisions encoded here (see docs/DECISIONS.md, B01-B05):
*   B01  Perennial choices only: switchgrass and poplar x cropland and pasture.
*        Corn, prairie and "other land" questions are not used.
*   B02  Eligibility: Q1 = 1 (owns >10 rural acres) and Q2 = 1 (main decision maker).
*   B03  Decision code 1 = accept; 0, 3, 4 = reject; 2 = "does not own that land
*        type" and leaves the choice set.
*   B04  A literal "x" in an acreage item means "marked, amount unknown": the
*        acreage is missing (never zero) and the land denominator is flagged.
*   B05  Crop denominator  = corn + soybeans + wheat + other row crops + fruit
*                            trees + vegetables (A8a-A8f).
*        Pasture denominator = grassland/pasture + hay/alfalfa (A8g-A8h).
********************************************************************************

confirm file "$KBS_ZIP"

local extract "$RESTRICTED/kbs_extract"
capture mkdir "`extract'"

local here "`c(pwd)'"
quietly cd "`extract'"
unzipfile "$KBS_ZIP", replace
local survey : dir "." files "Landowner*"
local nsurvey : word count `survey'
if `nsurvey' != 1 {
    quietly cd "`here'"
    display as error "BLOCKED: expected one survey data file in the KBS archive."
    exit 601
}
local survey_file : word 1 of `survey'
copy "`survey_file'" "kbs_survey_raw.csv", replace
quietly cd "`here'"

********************************************************************************
* 1. Locate the header row (the file starts with an EML comment block).
********************************************************************************

tempname fh
file open `fh' using "`extract'/kbs_survey_raw.csv", read text
local line_no = 0
local header_row = 0
file read `fh' line
while r(eof) == 0 {
    local ++line_no
    if substr(`"`macval(line)'"', 1, 3) == "id," {
        local header_row = `line_no'
        continue, break
    }
    file read `fh' line
}
file close `fh'

if `header_row' == 0 {
    display as error "BLOCKED: no header row starting with id, found."
    exit 601
}

import delimited using "`extract'/kbs_survey_raw.csv", ///
    varnames(`header_row') rowrange(`=`header_row'+1') ///
    stringcols(_all) encoding("utf-8") clear

* The row after the header is an all-empty "#" separator.
drop if strtrim(id) == "#" | strtrim(id) == ""

capture rename van_buren vanburen
capture rename vanbuthe vanburen

isid id
display as result "Imported " _N " returned questionnaires."

********************************************************************************
* 2. Safe numeric parsing. Every nonnumeric token is either an explicit
*    decision below or a hard stop.
********************************************************************************

local acreage_items corn soybeans wheat other_row_crops fruit_trees vegetables ///
    grassland_pasture hay forest shrub other_farmable other_rural crp

ds zoning, not
foreach v of varlist `r(varlist)' {
    quietly {
        replace `v' = strtrim(itrim(subinstr(`v', ",", "", .)))
        gen byte xmark_`v' = lower(`v') == "x"
        gen byte qmark_`v' = `v' == "?"
        gen double num_`v' = real(`v')
        count if missing(num_`v') & `v' != "" & !xmark_`v' & !qmark_`v'
    }
    if r(N) > 0 {
        display as error "BLOCKED: unexpected nonnumeric token(s) in `v':"
        list id `v' if missing(num_`v') & `v' != "" & !xmark_`v' & !qmark_`v', noobs
        exit 459
    }

    * "x" is only meaningful in acreage items (B04).
    quietly count if xmark_`v'
    if r(N) > 0 & !`: list v in acreage_items' {
        display as error "BLOCKED: literal x outside acreage items in `v'."
        exit 459
    }
    * "?" is accepted as missing only for the self-reported rental rate a5.
    quietly count if qmark_`v'
    if r(N) > 0 & "`v'" != "a5" {
        display as error "BLOCKED: '?' token in `v'."
        exit 459
    }

    quietly count if xmark_`v'
    if r(N) == 0 drop xmark_`v'
    drop qmark_`v' `v'
    rename num_`v' `v'
}

label variable zoning "E7 zoning (multi-select, raw text)"

********************************************************************************
* 3. Coding invariants (missing allowed; unexpected codes are not).
********************************************************************************

foreach v in question_1 question_2 a3 farmer male {
    assert inlist(`v', 0, 1, .)
}
foreach v in switch_cropland_d switch_pasture_d poplar_cropland_d poplar_pasture_d {
    assert inlist(`v', 0, 1, 2, 3, 4, .)
}
foreach v in switch_price poplar_price {
    assert inlist(`v', 50, 100, 200, 300, .)
}
foreach v in switch_contract poplar_contract {
    assert inlist(`v', 5, 10, .)
}
foreach v of local acreage_items {
    assert `v' >= 0 if !missing(`v')
}
assert total_acres >= 0 if !missing(total_acres)

********************************************************************************
* 4. Survey county (Michigan FIPS). Respondents may tick several counties.
********************************************************************************

local counties allegan barry branch ionia isabella lenawee livingston ///
    newaygo saginaw sanilac tuscola vanburen
local fipslist 26005 26015 26023 26067 26073 26091 26093 26123 26145 26151 26157 26159

egen byte county_n_named = rowtotal(`counties')
gen str5 fips = ""
forvalues j = 1/12 {
    local c : word `j' of `counties'
    local f : word `j' of `fipslist'
    replace fips = "`f'" if `c' == 1 & county_n_named == 1
}
label variable fips "Survey county FIPS (single named county only)"
label variable county_n_named "Number of named survey counties ticked"

********************************************************************************
* 5. Eligibility (B02) and land denominators (B05).
********************************************************************************

gen byte eligible = question_1 == 1 & question_2 == 1 ///
    if !missing(question_1, question_2)
label variable eligible "Q1 = 1 and Q2 = 1"

egen double crop_acres = rowtotal(corn soybeans wheat other_row_crops ///
    fruit_trees vegetables), missing
egen double pasture_acres = rowtotal(grassland_pasture hay), missing

gen byte crop_denom_xflag = 0
foreach v in corn soybeans wheat other_row_crops fruit_trees vegetables {
    capture confirm variable xmark_`v'
    if !_rc replace crop_denom_xflag = 1 if xmark_`v' == 1
}
gen byte pasture_denom_xflag = 0
foreach v in grassland_pasture hay {
    capture confirm variable xmark_`v'
    if !_rc replace pasture_denom_xflag = 1 if xmark_`v' == 1
}

egen double land_components_sum = rowtotal(`acreage_items'), missing
gen byte components_gt_total = land_components_sum > total_acres ///
    if !missing(land_components_sum, total_acres)

label variable crop_acres "Crop denominator A8a-A8f (acres)"
label variable pasture_acres "Pasture denominator A8g-A8h (acres)"

compress
save "$RESTRICTED/kbs_respondents.dta", replace

********************************************************************************
* 6. Long perennial choice file (B01): 4 rows per respondent.
********************************************************************************

keep id eligible fips county_n_named a3 a4 a5 farmer age male ///
    household_members income education total_acres crop_acres pasture_acres ///
    crop_denom_xflag pasture_denom_xflag components_gt_total ///
    switch_price switch_contract switch_cropland_d switch_cropland_a ///
    switch_pasture_d switch_pasture_a ///
    poplar_price poplar_contract poplar_cropland_d poplar_cropland_a ///
    poplar_pasture_d poplar_pasture_a

expand 4
bysort id: gen byte choice = _n

gen str11 experimental_feedstock = cond(choice <= 2, "Switchgrass", "Poplar")
gen str7  land_type = cond(inlist(choice, 1, 3), "Crop", "Pasture")

gen double offer = cond(choice <= 2, switch_price, poplar_price)
gen double contract_years = cond(choice <= 2, switch_contract, poplar_contract)

gen double raw_decision = .
replace raw_decision = switch_cropland_d if choice == 1
replace raw_decision = switch_pasture_d  if choice == 2
replace raw_decision = poplar_cropland_d if choice == 3
replace raw_decision = poplar_pasture_d  if choice == 4

gen double stated_acres = .
replace stated_acres = switch_cropland_a if choice == 1
replace stated_acres = switch_pasture_a  if choice == 2
replace stated_acres = poplar_cropland_a if choice == 3
replace stated_acres = poplar_pasture_a  if choice == 4

gen double denom_acres = cond(land_type == "Crop", crop_acres, pasture_acres)
gen byte denom_xflag = cond(land_type == "Crop", crop_denom_xflag, pasture_denom_xflag)

drop switch_* poplar_* crop_denom_xflag pasture_denom_xflag

label define decision 0 "no, none ticked" 1 "yes" 2 "does not own land type" ///
    3 "no at any payment" 4 "no, would at higher rent"
label values raw_decision decision

* B03
gen byte accept = raw_decision == 1 if inlist(raw_decision, 0, 1, 3, 4)

gen str24 sample_status = ""
replace sample_status = "not_eligible"     if eligible != 1
replace sample_status = "decision_missing" if sample_status == "" & missing(raw_decision)
replace sample_status = "does_not_own"     if sample_status == "" & raw_decision == 2
replace sample_status = "design_missing"   if sample_status == "" & ///
    (missing(offer) | missing(contract_years))
replace sample_status = "analysis"         if sample_status == ""

gen byte analysis = sample_status == "analysis"
assert !missing(accept) if analysis

gen double ln_offer = ln(offer)
gen byte contract10 = contract_years == 10 if !missing(contract_years)
gen byte pasture = land_type == "Pasture"
gen byte switchgrass = experimental_feedstock == "Switchgrass"

label variable analysis "Choice in the experimental analysis sample"
label variable accept "Accepted the offered perennial contract"
label variable denom_acres "Owned acres of the offered land type (B05)"

isid id choice
compress
save "$RESTRICTED/kbs_choices_long.dta", replace

********************************************************************************
* 7. Non-disclosive sample flow.
********************************************************************************

preserve
    gen long choices = 1
    collapse (sum) choices, by(sample_status)
    export delimited using "$RESULTS_P/sample_flow.csv", replace
restore

quietly count if analysis
local n_choice = r(N)
quietly egen byte _tag = tag(id) if analysis
quietly count if _tag == 1
local n_resp = r(N)
quietly count if analysis & accept == 1
local n_acc = r(N)
drop _tag

display as result "PASS 01: `n_choice' analysis choices, `n_resp' respondents, `n_acc' accepts."
