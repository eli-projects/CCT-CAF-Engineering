# Review of four native module CAFs — October 17, 2026

The delivered `AHU-1_Integrated_Sequence_CCT_TEST.caf` **failed CCT compatibility**. The user reports that everything in the Control tab is blank. Its hash is `5180b9ea0fe254d844f5385882c547afc74f165fc898f022750dd38957708a88`. Earlier ZIP/XML and behavior-model passes remain historical results; they do not establish a working CAF. The failed specimen is retained under `experiments/failed/` and must not become a programming baseline.

The most recent user-reported CCT-open AHU-1 baseline remains `examples/ahu-1/AHU-1_latest_AvgControlRedirect_VERIFIED-OPEN.caf`. Its complete AHU sequence has not been validated. The intervening sensor-cleanup and three-zone occupancy compositions have no independent CCT acceptance report and must not be silently promoted either.

## Sources and depth of review

Original uploaded bytes are preserved under `examples/modules/`. Spaces were replaced by underscores in the repository filenames; the archive member filenames and file contents are unchanged. SHA256 values and counts are in [the module manifest](../data/module-library-manifest.json).

| Source CAF | Objects | Top-level blocks | Internal connections | Diagrams |
|---|---:|---:|---:|---:|
| Output Control Modules 1 | 15,849 | 110 | 6,610 | 139 |
| Output Control Modules 2 | 9,618 | 103 | 3,794 | 99 |
| Setpoint-Misc Modules | 16,071 | 210 | 6,206 | 274 |
| State Generation Modules | 5,697 | 97 | 2,153 | 91 |
| **Total** | **47,235** | **520** | **18,763** | **603** |

All four main diagrams have **zero top-level connections**. Their modules contain substantial internal wiring. These are source libraries for individual modules, not evidence of a connected AHU application sequence. Their metadata records the same `3671` value, `10.8.0.60`, as the AHU baseline. That is a serialized format value, not verification of the currently installed CCT/device-package versions.

The read-only review indexed every top-level block, its exact full reference, class/role fields, direct ports, ordered exports, typed defaults, unit enums, enum definitions, publication field, simulation properties, complete-subtree object count/fingerprint, nested graph/connection counts, and external attribute references. It also inspected all available diagrams for reference/index and parallel-array consistency. The source libraries contain no problems under those limited checks.

Use [the complete block index](../data/native-modules/INDEX.md), [selected detailed interfaces](NATIVE-MODULE-INTERFACES.md), and the four JSON catalogs for lookup. **304 of the 520 top-level blocks have no nonempty explicit `2390` name.** Their class/role/reference is recorded without inventing a label. A numeric role match can help find a reference, but it does not prove two modules have identical behavior or construction.

## Concrete discrepancy in the failed CAF

Property `3383` stores more than coordinates: each observed position record also has an `unsignedShort` category code associated with how the block is represented. The failed builder assigned **10 to every internal primitive**, while the supplied native modules use different codes for several classes. The discrepancy is in rendering metadata and would not be detected by a numeric behavior interpreter.

| Serialized class | Working identification | Failed code | Native observed codes in nested graphs | Affected failed blocks |
|---:|---|---:|---|---:|
| 559 | Boolean operators | 10 | 2, 65535 | 102 |
| 539 | Reliability checks | 10 | 2, 65535 | 36 |
| 561 | Mathematical calculations | 10 | 8, 14, 65535 | 15 |
| 560 | Numeric comparisons | 10 | 4, 65535 | 10 |
| 558 | Timers | 10 | 15, 65535 | 3 |
| **Subtotal** | | | | **166** |

The last CCT-open AHU provides additional evidence for **21 main-diagram discrepancies**: 19 new operator input points were given code 6 where the corresponding native class observations use code 0, and two new hardware proxies were given code 6 where native proxies use 11. The combined audit therefore records **187** discrepancies. It compares class and role where available, falling back to class only when necessary. See [the exact object-level audit](../data/failed-integrated-display-audit.json).

These are demonstrated structural differences and a **plausible cause** of the blank Control tab. There is no isolated CCT before/after test proving causation, and other defects may remain. Changing these numbers alone must not be described as a verified repair. In particular, mathematical code 8 versus 14, Activity placement codes, and `65535` need their native context; a single global class-to-code dictionary is not a general specification.

The successful averaging clone preserved the complete native subtree and its display categories. The failed integrated builder synthesized new diagram positions with a common code and changed point metadata broadly. Future construction must preserve a matching native record's complete metadata, then modify only the explicitly tested fields.

## Findings for future CAF construction

### Identity is scoped to a source file

All four libraries reuse references such as `8-1/575_1.536_10004`. That ref identifies Blocking Protection in Output Control 1, Preheat Proportional Valve with Return Water Control in Output Control 2, 3rd Party Enable in Setpoint-Misc, and Dehumidification Sequencing in State Generation. Lookup identity must include **source CAF hash plus full object reference**. Numeric object IDs, class alone, or a reference copied across files cannot identify a function.

### A visible module is a complete object hierarchy

Examples range from the 8-object, two-input Sideloop Average to hundreds of records for complex output modules. Some contain nested Activities, FSMs, PIDs, calculators, enum comparison tables and separate port objects. Copying a top-level Activity or its port list alone omits required records. The original CAF is authoritative; JSON catalogs are inspection aids, not independently importable CCT module files.

The new `module` inspection command exports all objects and internal graphs for an exact source ref. Its XML strings are parser renderings for review, not byte-identical replacement fragments. Construction should preserve the original CAF bytes wherever feasible.

### Order and graphical metadata remain part of the evidence

The two-input native Average exports `7000,7001,8000`. The previously CCT-authored three-input Average exports `7000,7001,8000,7002`. Sorting ports would alter the observed representation. Preserve diagram order/positions, port order, role/setup properties, enum descriptors and grouping fields together.

Three native Activities contain a single block and omit **both** `3118` and `3384`: `Output_Control_Modules_1.caf` ref `8-1/575_1.536_10225`; `Setpoint-Misc_Modules.caf` ref `8-1/575_1.536_10278`; `State_Generation_Modules.caf` ref `8-1/575_1.536_10041`. Their omission is recorded as an observation, not incorrectly rejected by a universal “all diagrams must have wire arrays” rule. When connections exist, their metadata must be consistent.

### Boolean, binary enum and operating mode are different interfaces

The native Sideloop Interlock Binary To Binary has an enum input at `7000` and an enum output at `8000`; Binary To Analog also uses enum command/mode inputs. The word “binary” in a module name does not establish a Boolean data type. Native Boolean operators require Boolean signals. Preserve enum set `931`, state count `74`, labels `110`, typed defaults and translations; connecting ports only because their values happen to be 0/1 is insufficient.

### Template settings are observations, not approved AHU settings

The supplied Damper Minimum Position Reset by CO2 has a **90%** high-position default at `7004`. The CCT Help example lists **100%**. Both facts can coexist: one is this saved CAF's actual setting; the other is a documented default. The catalog preserves 90 rather than silently replacing it with the help value. Its 800/1000 ppm reset band and minimum-damper-position output describe a mixed-air reset module. AHU-1's demand-driven, 100% OA operation still needs its own reviewed application logic.

Most output modules also contain comfort-temperature defaults. Cloning their structure does not justify carrying those values into the 35–40°F room. In Cooling Proportional Valve with Dehumidification, ports `7012/7013/7014` correspond to outdoor-air temperature, low-OA temperature setpoint and differential in the native protection path; their 41/41/4°F values should not be misidentified as a normal discharge-air cooling low limit. This mapping was checked against CCT Help pp. 1374–1376, Tables 1142–1144.

### Unit Enable is a resolver with defined failure behavior

`State_Generation_Modules.caf`, ref `8-1/575_1.536_10122`, is a complete **38-object** Unit Enable Determination reference. Its ports include Network Mode (`7000`, enum 349), Hardware Mode (`7001`, enum 349), power-fail restart enable (`7002`, Boolean), restart time (`7003`, seconds), Resolution Mode (`7004`, enum 385), and state (`8000`, enum 349). CCT Help pp. 1133–1135, Tables 907–910, specifies Enable when both mode inputs are unreliable after timer permission. It is not a universal fail-closed block. No temperature input is established by a reused internal numeric ID.

### Warmup/Cooldown names do not establish AHU applicability

The supplied WarmupCooldown Determination and WarmupCooldown Sequencing are documented for VAV applications (CCT Help pp. 723–725 and 1162–1164). Determination evaluates supply/zone temperatures and a network command; Sequencing handles VAV heating stages/statuses. Their names do not supply the missing occupant-selected AHU-1 mode targets, entry/exit rules or heating priorities. Do not substitute them blindly for the AHU's requested operational modes.

### Matching existing AHU modules needs more than a name

[The baseline match inventory](../data/ahu-native-module-matches.json) records class/role matches without asserting semantic identity. Useful exact class/role matches include Unit Enable, Unoccupied Cooling/Heating Fan Lockouts, PID Tuning Reset, Occupancy Mode Determination, Zone Setpoint Determination and the pre-cooling Activity. The pre-cooling Activity uses class 536/role 6613 and matches the named Cooling Proportional Valve with Dehumidification reference. The AHU's final cooling Activity has role 6660 and has no corresponding exact top-level match in these four collections. Those variants must not be treated as interchangeable. Generic Activity role 1 identifies no unique function.

## Required workflow after this failure

1. Start from the last user-reported CCT-open AHU baseline. Keep the failed CAF in the failure directory and retain the exact report/hash.
2. Select one native module from its source hash/ref and inspect its complete subtree, interfaces, categories and nesting. Use CCT Help for behavior and the CAF for serialization; note application/version differences.
3. Make one small construction probe, preserving native graphical metadata and unknown properties. Check references, types, layouts and source differences. Run the observational display audit as an additional check.
4. Open that probe in CCT Configuration mode and confirm the full Control diagram renders. A blank diagram fails acceptance even if every offline test passes.
5. Only after CCT opening acceptance, test the added function in CCT Simulation, including reliability, boundaries, resets and restart behavior. Record actual CCT/device-package versions and the result.
6. Integrate sequence functions gradually, with explicit I/O mapping and design decisions. The four collections do not resolve AHU-1's missing exhaust, refrigeration, desiccant or HMI mappings.

The current update does not deliver another replacement CAF. It preserves native sources, adds reproducible inspection and regression tools, and records why the previous broad build cannot be trusted as an accepted starting point.

## Reproduce the review

Run from `caf-engineering-reference/` with Python 3.10+; the inspector uses the standard library:

```sh
python3 scripts/caf_module_catalog.py index examples/modules/*.caf --output-dir data/native-modules
python3 scripts/caf_module_catalog.py module examples/modules/State_Generation_Modules.caf --ref '8-1/575_1.536_10122' --output unit-enable-inspection.json
python3 scripts/caf_module_catalog.py audit-display experiments/failed/AHU-1_Integrated_Sequence_CCT_TEST.caf --reference examples/modules/*.caf examples/ahu-1/AHU-1_latest_AvgControlRedirect_VERIFIED-OPEN.caf --output data/failed-integrated-display-audit.json
python3 -m unittest discover -s tests -v
```

The audit is observational: a reported discrepancy is not itself proof of invalidity, and a clean result is not CCT acceptance. The detailed raw modules must still be reviewed before any transformation.
