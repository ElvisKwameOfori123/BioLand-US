# Clean analysis scripts

The public repository will contain a deliberately short set of executable stage scripts.

```
01_prepare_behaviour.py
02_prepare_polysys.py
03_prepare_land.py
04_prepare_rents.py
05_build_behavioural_access.py
06_run_mobilization.py
07_run_bootstrap.py
08_run_structural_sensitivity.py
09_build_spatial_outputs.py
10_make_figures.py
run_pipeline.py
```

These are **not** intended to mirror every development-stage script.

Reusable scientific logic belongs in `src/bioland_us/`. Stage scripts should mainly:

1. load configuration;
2. validate inputs;
3. call package functions;
4. save frozen outputs;
5. write a compact manifest;
6. exit with a clear PASS or error.

## Migration rule

A validated development script is not copied blindly into this folder.

For each stage we will:

- identify the final authoritative input;
- identify the final frozen output;
- remove obsolete branches and debugging code;
- replace absolute paths with repository-relative paths;
- move repeated logic into package functions;
- keep scientifically meaningful assertions;
- add a minimal automated test;
- compare the clean output against the frozen validated output.

Only after that comparison passes is the clean stage considered migrated.
