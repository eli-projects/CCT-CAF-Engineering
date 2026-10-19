# Module reference catalog — growing, evidence-tagged

The purpose of this catalog is to let an assistant choose **known CCT module names** and, where supported, instantiate them from validated CAF patterns. It is not a complete library of Johnson Controls module internals; CCT Help documents their functional purpose but not the XML generator schema.

## Definitions added 2026-10-19

Read [where built-in modules are defined](BUILTIN-MODULE-DEFINITIONS-2026-10-19.md). The supplied class cache has 132 classes / 2,489 property declarations; the signal metadata has 15 classes / 59 definitions. The 15 perspectives and 14-sheet workbook locate module instances and review views. The complete source files, indexes and hashes are linked there. All 49 classes in the reviewed AHU are covered; this is structural metadata evidence, not control acceptance.

**Mux erratum:** 36 custom R3 Muxs invert the intended Boolean selection. The reviewed correction preserves the user's layouts and updates only 2381/3122. Earlier Mux-dependent model passes are withdrawn. See [the review](AHU-1-R3-EDITED-LOGIC-REVIEW-2026-10-19.md).

## Native collections added 2026-10-17

The user supplied four native module CAFs, preserved in `examples/modules/`. [The complete index](../data/native-modules/INDEX.md) covers 520 top-level blocks; adjacent JSON catalogs preserve exact interfaces, typed defaults, enum definitions, port order, class/role fields and subtree fingerprints. [Selected interfaces](NATIVE-MODULE-INTERFACES.md) and [the review](NATIVE-MODULE-REVIEW-2026-10-17.md) explain AHU applicability and serialization findings. Native reference presence is not evidence that a new clone opens or simulates in CCT.

| Native reference | Source and full ref | Evidence / restriction |
|---|---|---|
| Sideloop Average Inputs | `Setpoint-Misc_Modules.caf`, `8-1/575_1.536_10384` | Two inputs, 8-object complete subtree; do not replace the tested 3-input structure with this 2-input variant |
| Damper Minimum Position Reset by CO2 | `Setpoint-Misc_Modules.caf`, `8-1/575_1.536_10107` | Complete reference; saved high position 90%; mixed-air reset, not a standalone 100% OA demand sequence |
| Unit Enable Determination | `State_Generation_Modules.caf`, `8-1/575_1.536_10122` | Complete 38-object reference; enum modes; documented both-inputs-unreliable behavior is Enable |
| Dehumidification Sequencing | `State_Generation_Modules.caf`, `8-1/575_1.536_10004` | Complete native reference; inspect PID-status inputs, enum output and application before choosing |
| Cooling Proportional Valve w Dehumidification v51 | `Output_Control_Modules_1.caf`, `8-1/575_1.536_10030` | 210-object reference; class/role matches AHU pre-cooling; defaults still require project-specific review |
| Sideloop Interlock Binary To Analog / Binary To Binary | `Output_Control_Modules_2.caf`, `8-1/575_1.536_10086` / `8-1/575_1.536_10087` | Inputs use enums; names do not establish Boolean port types |
| WarmupCooldown Determination / Sequencing | `Setpoint-Misc_Modules.caf`, `8-1/575_1.536_10448`; `State_Generation_Modules.caf`, `8-1/575_1.536_10141` | Documented VAV applications; not automatically AHU occupant-mode implementations |

The integrated AHU attempt is **known failed** with a blank Control tab. Preserve native metadata in future probes and see `data/failed-candidates.json`; do not promote its broadly synthesized Activity/primitive construction.

## Status terms

- **CCT-created template** = a complete, untouched CCT-produced example exists.
- **Assistant-cloned / simulated** = created from a CCT template, opened and independently simulated by user.
- **Observed only** = present in source CAF, but construction procedure hasn't been derived or tested.
- **Documentation name only** = known module name in CCT Help, but no creation example.

## Confirmed module entries

| Module name | CCT category / role | Creation strategy | Evidence and status |
|---|---|---|---|
| **Sideloop Average Inputs / `AVG-ZN-T`** | Built-in average, represented as Activity (class 536) containing Average calc (class 561) | CCT creates two-input Activity; I/O Modifications + Clone Ports yields three; copy entire ten-object subtree | **CCT-created template + assistant clone + simulated**; in `examples/ahu-1/` |
| **`AVG-ZN-H`** | User-named clone of same averaging Activity | Full clone of CCT-authored temperature Activity with new IDs and connection/diagram records | **Assistant-cloned / simulated**: 40,50,60 -> 50% RH |
| **`AVG-ZN-CO2`** | User-named clone of same averaging Activity | Same as above | **Assistant-cloned / simulated**: 700,900,1100 -> 900 ppm |
| **Unit Enable Determination** | State Generation > State Determination (CCT Help) | Exists in AHU-1 main diagram as Activity ref `8-1/575_1.536_86467`; no new-instance cloning test | **Observed only**; original network state/control path is user-created; no confirmed ZN-T dependency |
| **Occupancy Mode Determination / occupancy override path** | State Generation > State Determination (CCT Help) | An existing temporary-occupancy port was connected by one known four-field wire edit | **Existing wiring edit simulated**: ZN1-TOCC caused Bypass; later three-request composition reviewed in R3; selector correction awaits native CCT acceptance |
| **DA-T Unocc Status Determination v100** | Existing AHU Activity | Ref `8-1/575_1.536_85858`; consumes averaged temperature after redirect | **Observed only**; not independently instantiated |
| **Proportional Valve Pre-Cooling Control v51** | Existing AHU Activity | Ref `8-1/575_1.536_86466`; consumes averaged humidity after redirect | **Observed only**; not independently instantiated |
| **Unocc Cooling Fan Lockout** | Existing AHU Activity | Ref `8-1/575_1.536_81052` | **Observed only** |
| **Unocc Heating Fan Lockout** | Existing AHU Activity | Ref `8-1/575_1.536_81051` | **Observed only** |
| **PID Tuning Reset** | Existing AHU Activity | Ref `8-1/575_1.536_83123` | **Observed only** |

**Additional instance registry:** `data/observed-main-modules.json` contains every observed logic-style block in the latest AHU-1 main application with its *actual* serialized class ID, reference, ID, name if present, and port list if present. **An empty label means unknown—not an invitation to guess its function.**

## Candidate future entries (CCT Help names; no XML creation method yet)

The CCT Help includes descriptions for **Status OR**, **Status AND**, **Sideloop Maximum Selector**, **Sideloop Minimum Selector**, **Sideloop Sum Inputs**, **Damper Minimum Position Reset by CO2**, **CO2 Alarming for G36**, **Unit Enable Determination**, and multiple general/state modules. Some now have native source references in the 2026-10-17 collections. Successful new-instance construction still requires a controlled CCT test; **XML creation formats must not be inferred from module names alone**.

## Standard new-module research record (copy for each new finding)

**Module display name:**

**CCT category / version / controller package:**

**CCT GUI creation procedure:**

**Before and after CAF paths and hashes:**

**Added and modified object refs, class IDs, property IDs:**

**Input/output port names, numeric port IDs, data types, and ordering:**

**Main and internal diagram block/connection changes:**

**Static checks:**

**CCT opening and simulation results:**

**Remaining unknowns and prohibited assumptions:**

Only label a pattern *validated* after the exact CCT test and expected output are recorded.

