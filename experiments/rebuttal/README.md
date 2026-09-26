# Rebuttal / contract experiment launchers

Scripts keep the `tmp_*` names used on the eval host so logs stay comparable.

Override locations with environment variables (`CKT_WORK`, `CKT_PROJECT`, `LAKE_DIR`, `LLM_ENV`). Do not commit API keys.

Formal-contract loop:

1. `tmp_launch_contract_gen_ve12.py` — NL → observational Lean
2. `tmp_launch_contract_check_ve12.py` — syntax / soundness / completeness
3. `tmp_launch_contract_regen_ve12.py` — checker-in-the-loop regeneration
