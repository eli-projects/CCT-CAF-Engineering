# Module reference catalog — growing, evidence-tagged

The purpose of this catalog is to let an assistant choose **known CCT module names** and, where supported, instantiate them from validated CAF patterns. It is not a complete library of Johnson Controls module internals; CCT Help documents their functional purpose but not the XML generator schema.

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
| **Occupancy Mode Determination / occupancy override path** | State Generation > State Determination (CCT Help) | An existing temporary-occupancy port was connected by one known four-field wire edit | **Existing wiring edit simulated**: ZN1-TOCC caused Bypass; complete 3-stat OR not implemented |
| **DA-T Unocc Status Determination v100** | Existing AHU Activity | Ref `8-1/575_1.536_85858`; consumes averaged temperature after redirect | **Observed only**; not independently instantiated |
| **Proportional Valve Pre-Cooling Control v51** | Existing AHU Activity | Ref `8-1/575_1.536_86466`; consumes averaged humidity after redirect | **Observed only**; not independently instantiated |
| **Unocc Cooling Fan Lockout** | Existing AHU Activity | Ref `8-1/575_1.536_81052` | **Observed only** |
| **Unocc Heating Fan Lockout** | Existing AHU Activity | Ref `8-1/575_1.536_81051` | **Observed only** |
| **PID Tuning Reset** | Existing AHU Activity | Ref `8-1/575_1.536_83123` | **Observed only** |

**Additional instance registry:** `data/observed-main-modules.json` contains every observed logic-style block in the latest AHU-1 main application with its *actual* serialized class ID, reference, ID, name if present, and port list if present. **An empty label means unknown—not an invitation to guess its function.**

## Candidate future entries (CCT Help names; no XML creation method yet)

The CCT Help includes descriptions for **Status OR**, **Status AND**, **Sideloop Maximum Selector**, **Sideloop Minimum Selector**, **Sideloop Sum Inputs**, **Damper Minimum Position Reset by CO2**, **CO2 Alarming for G36**, **Unit Enable Determination**, and multiple general/state modules. These are potential modules to generate controlled before/after CCT samples for, but **none of their XML creation formats should be inferred from module names alone**.

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
