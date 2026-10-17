# Research scripts (historical evidence, not production tools)

These scripts generated specific AHU-1 artifacts in the working sandbox and have **hardcoded `/mnt/data/` paths, known index numbers, specific refs and object counts**. They are retained so the engineering method is auditable. They are **not portable**: adapt/parameterize and test before running on a new CAF. Inspect `docs/CAF-FORMAT.md` and `docs/EXPERIMENT-LOG.md` first.

# AHU-1 sequence R2 (2026-10-17)

`build_ahu1_sequence_r2.py` starts from the exact last user-reported CCT-open baseline. Its SHA-guarded stages call `make_ahu_sensor_cleanup_candidate.py`, `make_ahu_three_tocc_candidate_r2.py`, and `build_ahu_sequence_r2.py`; `caf_native_builder_r2.py` copies graphical records from each actual native source. The final build 2.1 also reconstructs paired hardware registries from native source identities. Keep those dependencies beside the entry point. `--graphics-only-r2` reproduces the superseded draft without that registry repair.

`validate_ahu_integrated_candidate.py` interprets the new serialized graphs and checks structure/types. It does not execute CCT or existing AHU PID/state machines. Use `../caf_module_catalog.py audit-display` as an additional observational check.

Read `docs/AHU-1-SEQUENCE-R2.md` for commands, defaults, external integration and acceptance checks. R2 requires Python 3.10+ and lxml. Its CCT opening/resource/native simulation status is pending. The known failed integrated CAF remains in `experiments/failed/` for comparison; it is never R2 build input.

