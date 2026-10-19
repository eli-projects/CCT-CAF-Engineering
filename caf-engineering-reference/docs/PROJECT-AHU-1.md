# AHU-1 project status

## Current review — October 19, 2026

The user reports R2 opens and subsequently edited/simulated R3. Detailed native simulation results were not supplied. Review found 36 inverted custom Muxs inherited from the generated logic; historical model passes are withdrawn. The correction changes only 72 properties and retains the user's layouts, wiring and other settings. Its 28 independent-model scenario groups and eight occupancy combinations pass; native CCT compile/resource/runtime acceptance is pending. See [the full review](AHU-1-R3-EDITED-LOGIC-REVIEW-2026-10-19.md), [R3/CIP interface design](AHU-1-SEQUENCE-R3.md) and [status/hashes](../data/sequence-r3-review-status.json).

CIP memory is an external restoration contract, not durable storage implemented by this CAF. Unknown memory blocks until authoritative restoration; there is no automatic one-hour release for unknown state. Exhaust, refrigeration, desiccant, supervisory freshness and HMI integration remain unfinished. The fixed fan/coil settings are provisional.

## Historical averaged-control snapshot — October 16–17

The remaining snapshot below documents earlier isolated accepted edits and the original construction baseline. Its pending/current statements are historical, superseded by the October 19 review above.

**2026-10-17 failure report:** The integrated CAF failed: the user reports everything in the Control tab is blank. It is archived at `experiments/failed/AHU-1_Integrated_Sequence_CCT_TEST.caf`; see [the native-module review and failure analysis](NATIVE-MODULE-REVIEW-2026-10-17.md). Its offline/model passes did not establish CCT acceptance. The last user-reported CCT-open baseline remains the file below; neither the sensor-cleanup nor the three-request override composition has independent CCT acceptance evidence.

**R2 candidate, final build 2.1:** `AHU-1_Sequence_R2_CCT_TEST.caf`, SHA256 `04463326b0822eeedc3cfdd3caa548bef78ca1144886010825d71c0950ff3bde`. Rebuilt from the user-opened baseline with 187 graphical category fields corrected and the paired hardware registries repaired; no intended logic changes versus the failed full sequence. [R2 notes and rebuild commands](AHU-1-SEQUENCE-R2.md). Opening/compilation/resources/native simulation remain pending.

**Current project working candidate:** `examples/ahu-1/AHU-1_latest_AvgControlRedirect_VERIFIED-OPEN.caf` — most recent version the user reported opens and "appears to be working". **It has not passed full sequence verification or live-controller commissioning.**

## Sensor and averaging configuration

| Point group | Present and wired to average? | Control consumption |
|---|---|---|
| `ZN1/2/3-T` | Yes, each to `AVG-ZN-T` | Average output redirected to three existing main-control inputs |
| `ZN1/2/3-H` | Yes, each to `AVG-ZN-H` | Average output redirected to three existing main-control inputs |
| `ZN1/2/3-CO2` | Yes, each to `AVG-ZN-CO2` | Average output **not** yet connected to CO2 ventilation control |
| `ZN1-TOCC` | Yes, directly to existing Occupancy Mode Determination temporary occupancy input | Single-stat bypass exists; three-stat OR not yet implemented |

Averaging is required by the user's AHU submittal sheet **1.10**, saying zone temperature, humidity and CO2 sensors are for averaging. Use the actual approved document to resolve exact operational requirements.

## Main diagram block indices (this snapshot ONLY)

| Block | Point/Activity |
|---:|---|
| 63 | Original `ZN-T` |
| 64 | Original `ZN-H` |
| 65 | Original `OCC-MODE` display |
| 85 / 89 / 93 | `ZN1/2/3-CO2` |
| 86 / 90 / 94 | `ZN1/2/3-H` |
| 87 / 91 / 95 | `ZN1/2/3-T` |
| 98 | `Unit Enable Determination` |
| 99 | `UNITEN-MODE` |
| 102 | Original `ZN-TOCC` |
| 103 | `ZN1-TOCC` |
| 105 | `AVG-ZN-T` |
| 106 | `AVG-ZN-H` |
| 107 | `AVG-ZN-CO2` |

**Six source-index substitutions (in connection array `3118`):**

| Edge zero-based index | Old source | New source | Destination block and port |
|---:|---|---|---|
| 108 | `63` ZN-T | `105` AVG-ZN-T | `19 / 7001` |
| 109 | `63` ZN-T | `105` AVG-ZN-T | `58 / 7000` |
| 110 | `63` ZN-T | `105` AVG-ZN-T | `60 / 7000` |
| 111 | `64` ZN-H | `106` AVG-ZN-H | `33 / 7003` |
| 112 | `64` ZN-H | `106` AVG-ZN-H | `62 / 7000` |
| 114 | `64` ZN-H | `106` AVG-ZN-H | `68 / 7003` |

All those edges retain source port `8000`; unchanged 134 other main connections. The average output wiring to the sensors is unchanged.

## Sensor hardware/address cleanup still pending

- **Do not yet delete** unnumbered `ZN` NS8000 at SA Bus address 199; its parent, hardware child point records, application proxies and `OCC-MODE` consumer require separate inspection.
- Current `ZN1 = 200`, `ZN2 = 201`, `ZN3 = 202`. Planned **after freeing 199**: `ZN1 = 199`, `ZN2 = 200`, `ZN3 = 201`.
- The existing `OCC-MODE` unnumbered display still receives one connection. Determine how to expose effective occupancy to the retained devices/desired UI before deletion.
- `ZN2-TOCC` and `ZN3-TOCC` application points are not present in this snapshot; plan to create/expose them and use a validated Boolean OR pattern to combine all three requests.
- The Unit Enable Determination supposed `ZN-T` internal dependency was a **false-positive hypothesis**. Do not assume one exists; inspect typed references and signal logic if needed.
- CO2 demand-control sequence, alarms, sensor-reliability handling, commissioning and verified fail-safe behavior remain future scope.
- Temporary occupancy timeout is **3600 seconds** in the latest working candidate. Tests previously used 30 seconds as a temporary value; do not reintroduce inadvertently.

## Validation note

For further offline tests, start from this exact snapshot; create new filename + manifest entry every time; use CCT on an offline/bench controller; don't transfer into active AHU hardware until complete safety and site approval.

