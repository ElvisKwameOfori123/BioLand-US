version 18.5
clear all
set more off
set linesize 255

********************************************************************************
* BIOLAND-US BEHAVIOURAL PIPELINE (Study A, KBS 2012 landowner survey)
*
* Run from the repository root:
*     cd "...\BioLand-US"
*     do stata/00_run_behaviour.do
*
* Starts from the raw KBS archive only:
*     data/raw/knb-lter-kbs.124.2.zip
*
* Respondent-level files are written under data/restricted, data/frozen/restricted
* and results/restricted. All three are git-ignored and must never be committed.
********************************************************************************

capture confirm file "pyproject.toml"
if _rc {
    display as error "Run Stata from the BioLand-US repository root."
    exit 601
}

global ROOT       "`c(pwd)'"
global RAW        "$ROOT/data/raw"
global RESTRICTED "$ROOT/data/restricted"
global FROZEN_R   "$ROOT/data/frozen/restricted"
global FROZEN_P   "$ROOT/data/frozen/public"
global RESULTS_R  "$ROOT/results/restricted"
global RESULTS_P  "$ROOT/results/behaviour"
global LOGS       "$ROOT/logs"

global KBS_ZIP    "$RAW/knb-lter-kbs.124.2.zip"

foreach d in RESTRICTED FROZEN_R RESULTS_R RESULTS_P LOGS {
    capture mkdir "${`d'}"
}

set seed 20260912

capture log close _all
log using "$LOGS/stata_behaviour.log", replace text name(behaviour)

do "$ROOT/stata/01_import_kbs.do"
do "$ROOT/stata/02_estimate_participation.do"
do "$ROOT/stata/03_conditional_acreage.do"
do "$ROOT/stata/04_export_behaviour.do"

display as text "================================================================================"
display as result "BIOLAND-US STATA BEHAVIOURAL PIPELINE COMPLETE"
display as text "================================================================================"

log close behaviour
