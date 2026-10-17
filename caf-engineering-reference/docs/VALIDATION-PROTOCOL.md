# CAF change and validation protocol

## Always preserve provenance

Store **both input and output CAF** under a new versioned filename, record their SHA256, CCT release, controller model, field controller/device package versions, change purpose, expected behavior, and whether validation was static, CCT-open-only, CCT Simulation, or bench commissioning.

## Stage 1: static analysis (necessary, not sufficient)

- ZIP opens; archive integrity `testzip()` passes; inspect actual member filenames.
- XML parses; unique full object refs and all intended cloned objects exist.
- Diagram `3375` (blocks), `3117` (indices), `3383` (positions) lengths match; `3118` (edges) and `3384` (connection metadata) lengths match.
- Every edge's source/target index exists; intended ports exist on the intended blocks; verify types.
- Internal Activity block references and cloned IDs do not collide; external application/hardware point bindings are valid; no dangling refs.
- Compare each new block's `3383` category code with the matching native class/role and diagram context. Preserve complete native graphical records and unknown metadata. `scripts/caf_module_catalog.py audit-display` provides an observational check; a clean result is not CCT acceptance.
- Scope cross-file identities by source CAF hash plus full ref. Keep enum/binary/Boolean types and native port order distinct. The new source collections contain some one-block Activities omitting both wire/metadata arrays; do not reject this observed omission as a universal schema violation.
- Diff precisely against baseline. Check 100% of unexpected object, property, default, address, state-table and timer changes.
- Avoid broad XML reserialization when a safe, minimal byte-preserving edit will do. Preserve complete `ZipInfo` for the known archive member when writing.

## Stage 2: CCT compatibility (mandatory)

- Open file in CCT **Configuration mode** and verify **all Application Control diagram** renders.
- Check modules, Features > Connections, internal Logic diagrams, point names and port order.
- An empty diagram or "internal tool error" is a failed experiment even when all static checks passed.

## Stage 3: CCT Simulation (mandatory for logic)

- Test expected values and output status, such as `60/70/80 F -> 70 F`, `40/50/60 %RH -> 50%`, `700/900/1100 ppm -> 900 ppm`.
- Exercise low/high limits, one unavailable sensor, zero/one/many simultaneous requests, reset and timers, operating modes, alarms and safety overrides as applicable.
- Verify downstream control inputs, state table and outputs; validating just the average result is not a full AHU validation.

## Stage 4: authorized bench / real controller

- Confirm hardware package and SA Bus addresses, sensor data quality/reliability, fallback logic and controlled transitions.
- Confirm safety interlocks, shutdown priorities, VFD and valve response, fire/smoke safeties and power restart on an approved bench before any operating equipment.
- Only authorized personnel transfer to a live controller under the site's change-management procedures.

## Separate truth levels

**User tested and simulated**, **CCT opened**, **static XML checks**, **source documentation**, and **inference** are distinct and must not be silently interchanged. Failures remain recorded rather than overwritten.

