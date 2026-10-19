# Chronological CAF experiment log

Tested behavior is based on the user's explicit CCT opening/simulation reports. Dates refer to the October 2026 collaboration. **Never upgrade "static-pass" into "works in CCT" without a user test.**

| Experiment | Input/reference | Outcome | Lesson |
|---|---|---|---|
| Existing temporary occupancy wire | Original AHU-1 + one wire to OCC input | **CCT opened; user simulated bypass** | Byte-level edits of existing diagram wire entries can work. |
| Move occupancy request from `ZN-TOCC` to `ZN1-TOCC` | `AHU-1_Phase1_ZN1_TOCC_Redirect_TEST.caf` | **CCT opened; user reported bypass simulation** | Existing wire source index 102 -> 103. |
| Hand-built `AVG-ZN-T PROTOTYPE` | `AHU-1_AVG-ZN-T_Experimental_Probe.caf` | **Invalid/empty Application Control display** | Well-formed XML is not sufficient for a native Activity. |
| Native third port hand-added to two-input Activity | `AHU-1_Native_AVG-ZN-T_3Input_Probe_TEST.caf` | **Failed to open: internal tool error** | Complete CCT-created port/point metadata and port ordering matter. |
| CCT created two-input averaging module | `AHU-1_CCT_AVG_2Inputs.caf` | **CCT-authored** | Baseline for accurate construction diff. |
| CCT-created third input and cloned Activity input | `AHU-1_CCT_AVG_3Inputs.caf` | **CCT-authored** | I/O Modifications and Clone Ports are distinct changes; two new point objects. |
| Wire three temperature sensors to CCT Activity | `AHU-1_3Sensor_Temp_Average_VERIFIED.caf` | **CCT simulation PASS** | 60,70,80 F gave 70 F average. |
| Clone complete 3-input Activity twice and connect H/CO2 | `AHU-1_3Averages_VERIFIED.caf` | **CCT simulation PASS** | RH 40/50/60 -> 50%; CO2 700/900/1100 -> 900; temperature remains 70. |
| Redirect six consumer wires from ZN-T/ZN-H to averages | `AHU-1_latest_AvgControlRedirect_VERIFIED-OPEN.caf` | **CCT opened and user reports it appears working** | All 2167 original objects/108 blocks/140 wires remain, only six wire sources changed. Full downstream sequences not independently signed off. |
| Remove extra sensor and retain three sensors at 199/200/201 | `AHU-1_Sensor_Cleanup_CCT_TEST.caf` | **Static checks only; CCT pending** | Hardware/proxy cleanup and occupancy-display fanout are separate from earlier CCT-open evidence. |
| Combine all three temporary-occupancy requests | `AHU-1_Three_Zone_Override_CCT_TEST.caf` | **Static/documented-behavior model checks only; CCT pending** | Complete native table/OR/MUX/port subtrees; enum requests translated before Boolean OR; native 3600-second timeout retained. |
| Integrate supported AHU sequence after user authorized broad implementation | `experiments/failed/AHU-1_Integrated_Sequence_CCT_TEST.caf` | **FAILED CCT compatibility: user reports blank Control tab (2026-10-17)** | Earlier graph/model checks passed but did not predict rendering. Archived hash `5180b9ea0fe254d844f5385882c547afc74f165fc898f022750dd38957708a88`; do not use as a working baseline. |
| Review four native module collections | `examples/modules/` | **Native references preserved; independent simulation not reported** | Indexed 520 top-level blocks / 47,235 objects / 18,763 internal wires. Found 187 category-code discrepancies in the failed CAF (166 nested primitives, 21 main blocks). This is a plausible cause to isolate in CCT, not a verified fix. See `NATIVE-MODULE-REVIEW-2026-10-17.md`. |
| Rebuild full AHU-1 sequence R2 using native graphical records | `AHU-1_Sequence_R2_CCT_TEST.caf`; rebuild script in `scripts/research/` | **Zero observational category mismatches; 22 modeled groups pass; CCT pending** | Built from last user-opened baseline. Only 187 category fields in three diagram objects differ from failed CAF; no functional differences. Hash `23ab292b4bcffabbc32ef7b4a6e5acc90e1dde039b85a15a0afebaa32873c5cd`. See `AHU-1-SEQUENCE-R2.md`. |
| Complete final R2 build 2.1 registry pairing | Same CAF filename, final hash `04463326b0822eeedc3cfdd3caa548bef78ca1144886010825d71c0950ff3bde` | **Registry pairing and category checks pass; CCT pending** | Supersedes the graphical-only draft. Also repairs the main `3926`/`3927` pairing from 70/69 to 69/69, preserving each original reference's native registry value and copying the source value for new NS8000 requests. No sequence/wire changes. |

## October 19 evidence update

| Experiment | Exact reference | Outcome and limit |
|---|---|---|
| R2 opening feedback | Final R2 hash `04463326b0822eeedc3cfdd3caa548bef78ca1144886010825d71c0950ff3bde` | User reports opening/custom logic visible; no R2 simulation results supplied. |
| R3 readability and memory interface | Original R3 hash `dd96ed08ac8557635b19db812f62aea760a2dbefd9c5323f53c9e651198a3648` | Nested Activities and external CIP restoration contract; original model passes later withdrawn. |
| Edited R3 review | Edited hash `d8554931f40cc2d69f515c004964281b6f0c9e1e9dcacf7d1a984e4ac914fe51` | User reports layout edits/Simulation. 58 objects differ from original; saved layout/simulation fields plus OR-input interchange and internal flags are itemized. No detailed native behavioral results supplied. |
| Mux review and correction | Correction hash `46b41438f157068c5546210a54f733859df617abcc2f83a2e6f99ba4afd86a64` | 36 selector corrections / 72 properties, preserving all other edited fields; 28 corrected-model groups and eight occupancy combinations. Native CCT acceptance pending. |
| Class/signal/release references | 132 classes, 2,489 direct properties; 15 signal classes / 59 definitions | All 49 AHU classes/versions covered. Mux type/range checks pass both the inverted and corrected maps; no behavioral acceptance follows. |
| Perspective references | 15 PMLs, 14 worksheets / 623 ID references | Widget mappings agree. Focused AHU views omit custom IDs; Module-Logic is broader. |
| Simulator DLL inspection | Three Field Controller Simulator components, resource version 6.0.0.84 | Native 32-bit Windows components, same 251 export names. Static inspection only; no functions invoked. |

**Model erratum:** The earlier interpreter treated Mux map values as zero-based data-input offsets and omitted Default Input. Its R2/R3 behavioral passes are withdrawn. Historical builders/files remain reproducible; use the corrected interpreter for the reviewed candidate, then run native CCT tests independently. A zero-error metadata audit never ruled out the inversion.

## Important error correction

An earlier audit asserted a nested temperature dependence in **Unit Enable Determination** based on object ID `10002`. Further inspection found the suspicious internal block produced a **Boolean** and the numeric match did not demonstrate a live `ZN-T` temperature connection. **That claimed dependency is unconfirmed** and must not be used to justify changes. User's connected network input `UNITEN-MODE` and output `UNITEN-STATE` reflect the intended State Generation logic.

## Conditions for promoting an experiment

1. CCT opens with the complete Application Control diagram (not blank/empty).
2. Added module and connection details are visible.
3. CCT Simulation is exercised with expected inputs and outputs; include failure and boundary values when relevant.
4. No unintended hardware address, state-table, default parameter, or safety-interlock changes.
5. Record CCT version/device package, input CAF SHA256, resulting CAF SHA256, exact delta and user-reported acceptance.

