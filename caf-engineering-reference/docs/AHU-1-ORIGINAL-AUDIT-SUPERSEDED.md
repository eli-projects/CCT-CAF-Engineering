# AHU-1 — Unnumbered ZN sensor dependency audit

**Status:** Audit only. **No deletion, readdressing, averaging logic, or additional CAF change has been made.**

**Source:** `AHU-1_Phase1_ZN1_TOCC_Redirect_TEST.caf`, the last file the user confirmed opens and performs occupancy bypass in CCT. SHA-256 `f0419110c9a40758fe86c6bba5a0ae78ea7b76fa9ae13d28d27499da78cbbd7f`. 2,137 CCT XML objects; 105 main-diagram blocks; 131 main-diagram connections. Reviewed alongside MCCD Ag AHU-1 HW submittal, drawing 1.14, page 9.

## Existing SA-Bus devices (unchanged)

| Sensor | CCT device object | Current address | Planned address | Decision |
|---|---|---:|---:|---|
| Unnumbered `ZN` | Zone NS8000 | 199 | Remove | **Not safe yet: active temperature/humidity links** |
| `ZN1` | NS8000 (ZN1-) | 200 | 199 | Retain |
| `ZN2` | NS8000 (ZN2-) | 201 | 200 | Retain |
| `ZN3` | NS8000 (ZN3-) | 202 | 201 | Retain |

The intended addresses become collision-free only after `ZN` at 199 is removed. The future HMI address 202 in the drawing should also be checked before commissioning.

## Nine child objects under `ZN` (device class 910, object ID 10000)

| Name | Type | Object ID | Main-control use | Deletion considerations |
|---|---|---:|---|---|
| Zone NS8000 | SA-Bus device | 10000 | Parent | Device feature and point metadata must be removed by CCT |
| `ZN-T` | analog value | 10002 | **3 outgoing main diagram connections**, plus **1 nested Unit Enable connection** | Remap all before deletion |
| `ZN-T Offset` | analog value | 10003 | No main diagram block | Device feature/calibration child |
| `ZN-H` | analog value | 10006 | **3 outgoing main diagram connections** | Remap all before deletion |
| `ZN-H Offset` | analog value | 10007 | No main diagram block | Device feature/calibration child |
| `ZN-CO2` | analog value | 299726 | Main diagram block, **no control connection** | Existing DCV logic cannot be assumed complete |
| `ZN-CO2 Offset` | analog value | 299729 | No main diagram block | Device feature/calibration child |
| `OCC-MODE` | multistate value | 2086 | **1 incoming main diagram connection** | Redirect occupancy display to retained sensor(s) |
| `ZN-TOCC` | binary value | 300140 | Main diagram block, **no connection** after Phase 1 | Already redirected to `ZN1-TOCC` (object 300143) |

Note: object IDs are not globally unique across distinct Metasys classes; references above were identified by full object paths and CCT class IDs, not by numeric ID alone.

## Exact active diagram wiring needing replacement

| Old point | Path / diagram edge | Connected block | Connection ports | Current impact |
|---|---|---|---|---|
| `ZN-T` | Main #108 | `Unnamed module 83757` (ID 83757) | `8000 → 7001` | Zone temperature input |
| `ZN-T` | Main #109 | `DA-T Unocc Status Determination v100` (ID 85858) | `8000 → 7000` | Zone temperature input |
| `ZN-T` | Main #110 | `Unnamed module 83759` (ID 83759) | `8000 → 7000` | Zone temperature input |
| `ZN-H` | Main #111 | `Unnamed module 83798` (ID 83798) | `8000 → 7003` | Zone humidity input |
| `ZN-H` | Main #112 | `Unnamed module 82885` (ID 82885) | `8000 → 7000` | Zone humidity input |
| `ZN-H` | Main #114 | `Proportional Valve Pre-Cooling Control v51` (ID 86466) | `8000 → 7003` | Zone humidity input |
| `OCC-MODE` | Main #113 | `Unnamed module 51131` (ID 51131) | `50032 → 7000` | Occupancy display output |
| `ZN-T` | Nested **Unit Enable Determination** #1 | internal block `299718` | `85 → 513` | Temperature signal also used inside nested module |

The source CAF does not supply descriptive names for every internally serialized module. Unnamed modules above are intentionally shown by stable CCT object ID instead of guessing their function. Some displayed module labels are also missing in the CAF; inspect the CCT Features → Connections view before final remap.

## Other references affected by deletion

The device's nine hardware objects are tied to five corresponding application proxy blocks: `ZN-T` (`556_10002`), `ZN-H` (`556_10006`), `ZN-CO2` (`556_299726`), `ZN-TOCC` (`556_300140`), and `OCC-MODE` (`555_2086`). The proxy references point to the actual hardware objects through properties `3399` and `3672`. There is also a nested temperature input block inside `Unit Enable Determination` (`552_10002`). CCT diagram arrays (`3375`, `3117`, `3383`, `3118`, `3384`, and related indexes) must stay consistent if objects are deleted. The older experimental CAF errors demonstrate why raw XML deletion of these objects alone is unsafe.

## Main diagram numbered-sensor inputs, as found

| Retained sensor points | Main diagram block presence | Incoming/outgoing connections currently present |
|---|---|---|
| `ZN1-T`, `ZN1-H`, `ZN1-CO2` | Yes | None |
| `ZN2-T`, `ZN2-H`, `ZN2-CO2` | Yes | None |
| `ZN3-T`, `ZN3-H`, `ZN3-CO2` | Yes | None |
| `ZN1-TOCC` | Yes | **Connected** to Occupancy Mode Determination temporary-occupancy input (main edge #130) |
| `ZN2-TOCC`, `ZN3-TOCC` | No | Not yet present; future feature addition requires additional CCT diagram metadata |
| `ZN1/2/3-OCC-MODE` | Yes | None |

This establishes that `ZN` is the current source for the operative temperature and humidity control chain; deleting it without new paths will likely break temperature control, humidity control, and display, even though temporary occupancy now originates from `ZN1`.

## Recommended safe sequence

1. **Confirm control strategy for 3 zone-sensor readings.** Should AHU-1 use one designated reference sensor, average/selection logic, or another defined sequence for temperature, humidity, and CO₂? Drawing 1.14 calls for zone/space sensors but does not specify how three samples must be combined.
2. **Reassign operating measurements before deletion.** In a test CAF, redirect all temperature and humidity paths, including the nested Unit Enable path. Route occupancy-mode display to the intended retained sensor(s). Reevaluate CO₂/DCV when implemented.
3. **Test the non-destructive remap in CCT.** Inspect Connections and simulate representative occupied, unoccupied, humidity-demand, temperature-demand, and occupancy-bypass inputs. This test remains offline/bench-only.
4. **Delete obsolete NS8000 and associated children using CCT where possible**, allowing CCT to update all object and diagram indexes. If manipulating the CAF directly, verify every remaining reference and serialized list, then validate in CCT before using it.
5. **Readdress only after old address 199 is vacant:** `ZN1` 200→199; `ZN2` 201→200; `ZN3` 202→201. Verify the HMI assignment and actual physical sensor addresses.
6. Later, add missing `ZN2-TOCC` and `ZN3-TOCC` and OR the three temporary occupancy requests while preserving the existing timed bypass behavior.

## Decision needed before any control-wiring remap

**Are the three physical zone sensors intended to be averaged for AHU temperature and humidity control, or is one specific sensor (e.g. ZN1) the primary control reference?** We should not silently select ZN1 for all active loops simply because it has the working occupancy-request connection.

**This is an application-structure/dependency audit, not an operational validation. Do not download any experimental CAF to a field controller until the complete controls and safeties have been independently validated in CCT and on the intended bench setup.**


> **SUPERSEDED WARNING (2026-10-16):** This initial audit assumed `Unit Enable Determination` had an active `ZN-T` dependence solely from object ID `10002`. Later analysis retracted that claim: a Boolean internal block shared the numeric ID but did not prove temperature wiring. Read `docs/EXPERIMENT-LOG.md` for the correction. Sensor averaging and control redirects have also subsequently been completed; this older document is preserved only for provenance.
