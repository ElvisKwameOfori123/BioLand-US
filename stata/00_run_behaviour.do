version 18.5
clear all
set more off
set linesize 255

********************************************************************************
* BIOLAND-US BEHAVIOURAL ANALYSIS
*
* Run this file from the repository root:
*     cd "...\BioLand-US"
*     do stata/00_run_behaviour.do
*
* Restricted respondent-level data are never committed to GitHub.
********************************************************************************

capture confirm file "pyproject.toml"
if _rc {
    display as error "Run Stata from the BioLand-US repository root."
    exit 601
}

global ROOT "`c(pwd)'"
global RESTRICTED "$ROOT/data/restricted"
global FROZEN_R   "$ROOT/data/frozen/restricted"
global RESULTS_R  "$ROOT/results/restricted"
global LOGS       "$ROOT/logs"

capture mkdir "$FROZEN_R"
capture mkdir "$RESULTS_R"
capture mkdir "$LOGS"

do "$ROOT/stata/01_prepare_behaviour.do"
do "$ROOT/stata/02_estimate_participation.do"
do "$ROOT/stata/03_reconstruct_conditional_acreage.do"
do "$ROOT/stata/04_export_behaviour.do"
do "$ROOT/stata/05_validate_behaviour.do"

display as text "================================================================================"
display as result "BIOLAND-US STATA BEHAVIOURAL PIPELINE COMPLETE"
display as text "================================================================================"
