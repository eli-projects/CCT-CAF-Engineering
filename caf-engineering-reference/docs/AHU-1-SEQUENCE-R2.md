# AHU-1 sequence R2 — October 17, 2026

**CAF:** `AHU-1_Sequence_R2_CCT_TEST.caf`  
**SHA256:** `23ab292b4bcffabbc32ef7b4a6e5acc90e1dde039b85a15a0afebaa32873c5cd`  
**Status:** Revised full-sequence candidate. CCT opening, compilation/device resources and native simulation remain pending.

R2 rebuilds from `AHU-1_latest_AvgControlRedirect_VERIFIED-OPEN.caf` (SHA256 `078e1aa20f084e82212f205480f858bb17fad45a81081a74f74e4d429530bd26`). It reapplies sensor cleanup, three-zone occupancy requests and the sequence integration. The failed CAF is used only for comparison, never as build input.

Every new block's graphical position record is now copied from its actual native source, with only coordinates adjusted. Comparison with the failed CAF shows **exactly 187 category-field corrections in property 3383 across three diagram objects**, with no added/removed objects or functional wiring changes. The failed specimen remains a failed specimen. R2 has no unobserved category combinations in the native-source audit; this is an offline result, not proof that CCT renders it.

## Sequence implemented

| Function | Intended behavior in the CAF |
|---|---|
| Three room sensors | Temperature/RH/CO2 averages retained; NS8000 addresses 199/200/201; all three temporary-occupancy requests combine into the native 3,600-second bypass input. |
| Cooling | Initial cooling SP 40°F. Starts at 42°F and releases below 38°F with the native comparison boundary behavior. |
| Heating | Initial heating SP 35°F. Starts at 33°F and releases above 37°F. |
| Humidity | RH SP 85%; starts at 90%, releases below 85%; inner recovery target 84.5%. |
| CO2 | Occupied/Bypass demand starts at 1,000 ppm, releases below 900 ppm; uses the native 100% OA fan/damper path. |
| Demand cycling | Stop when eligible demands are satisfied and publish `REFRIG-REQ`. Unoccupied thermal/RH demand may run; CO2 alone does not start an unoccupied unit. |
| CIP | Maintained `CIP-REQ = True` stops normal AHU operation. Clearing it means cleaning complete and begins a minimum 3,600-second hold. Repeated CIP restarts that hold from the latest completion. |
| Restart | A conservative full one-hour hold also applies after every restart because prior cleaning history is not retained. `EF-PURGE-REQ` and `EF-PURGE-% = 100` are published throughout CIP/hold. |
| Unit override | Pulse `UNIT-ON-REQ` or `UNIT-OFF-REQ` True then False; initial duration 3,600 seconds, adjustable by `UNIT-OVRTIME`. Simultaneous requests give Off priority; subsequent On can cancel prior Off; `UNIT-OVR-CANCEL` resets both. |
| Special modes | Maintained Warmup/Cooldown/Setup requests force fan operation using the common thermal settings. Distinct mode targets/exit rules remain unspecified in the sequence. |
| Interlocks | Normal coils require permission, native fan On command, reliable fan proof and applicable demand. Confirmed native safety valve protection retains priority; fan/damper stop. |
| Connections | Smoke input to native emergency safety path; actual pre-cooling temperature to pre-cooling controller; actual discharge temperature to reheat low-limit path. |

The printed 35–40°F range is interpreted as heating 35°F/cooling 40°F in every occupancy mode, with a central reference of 37.5°F. Occupied demand cycling follows the specific refrigeration/CIP recovery paragraphs and the previously agreed interpretation of the continuous-fan conflict. The temperature request retains its state at the exact 38°F/37°F reset edge; use 37.9°F/37.1°F when testing release.

## Settings requiring design/commissioning review

| Setting | Initial value |
|---|---:|
| `SF-RUN-%` | 50% fixed adjustable VFD run speed |
| `PCC-T-SP` | 41°F |
| `DAT-CLG-SP` / `DAT-HTG-SP` | 35°F / 60°F |
| `DAT-LOW-LIM` / `DAT-LL-BAND` | 34°F / 1°F |

These values remain provisional. No modulating duct-static sensor is identified in the current drawing/CAF, so the native fan startup uses Constant Capacity and the final speed uses `SF-RUN-%`. No artificial pressure feedback was added. Native mechanical safety inputs and native protection paths are retained.

## External work still needed for the complete system

- Map `EF-PURGE-REQ` / `EF-PURGE-%` to the dedicated exhaust-fan controller and verify actual operation. Published requests alone do not operate that external fan.
- Map `REFRIG-REQ` to refrigeration supervisory control and confirm actual mode/availability feedback.
- Confirm the OEM desiccant/gas interface. `DESICCANT-REQ` is published; no physical output was invented. The drawn `DEHUMID` is an input.
- Configure room-panel/DLK mode selection, CIP and pulse handling, schedules, front-end alarms, graphics and airflow/RH/CO2 trends. Confirm the intended display address 202.
- Resolve the conflicting room label and any distinct Warmup/Cooldown/Setup or alternate unoccupied targets with the design team.

## CCT acceptance steps

1. **Open R2 in CCT Configuration mode first.** Confirm the Control tab and the `AHU DEMAND AND CIP`, `AHU OUTPUT INTERLOCKS` and `ZONE-TOCC-OR` diagrams render. Run CCT validation/compile and controller memory/resource checks with the matching CGM09090/XPM packages. A blank diagram is still a failure; retain the exact message/version if one appears.
2. In Simulation, set master `UNITEN-MODE = Enable`, required inputs reliable, safety inputs Normal, rotation Normal and actual occupancy Occupied. Check timer setup names: serialized 2 is intended Retriggerable; 4 is intended On Delay with Memory. Confirm reset/expiry and configured MUX quality propagation. CCT Help Table 1366, p.1691, documents selected-input/Mode reliability.
3. **Expect a one-hour startup hold.** `CIP-BLOCK` should be True and the AHU off with purge requested. Use simulation time acceleration; setting `CIP-HOLD-TIME` below 3,600 does not bypass the minimum. After the hold, a satisfied zone should remain off and request refrigeration.
4. Test averaged temperature **42 → 40 → 38 → 37.9°F** and **33 → 35 → 37 → 37.1°F**. Verify native thermal state, PID direction and physical output commands, not only request flags. Test RH **90 → 85.1 → 84.9%** and CO2 **1,000 → 950 → 899 ppm**. Repeat CO2 while Unoccupied.
5. Assert CIP during running, hold it active beyond an hour, clear it and verify a new full hour. Repeat CIP during that hour and restart the simulation/controller model; confirm the correct fresh hold. Verify the mapped exhaust fan throughout.
6. Exercise timed On/Off/Cancel, simultaneous On/Off, each special-mode request, all three occupancy buttons, fan-proof loss/unreliability, required-input failures, parameter faults and native smoke/low-temp/high-static safeties. Confirm normal coil shutdown and native safety valve protection. Check one failed averaging sensor and rotation-fault inhibition of the OEM request.

Offline checks cover 29 diagrams, 1,279 connections, 431 new/redirected wire types, no category mismatches and 22 documented-behavior model scenario groups. They do not execute CCT or the existing native AHU PID/FSM modules. The next decisive result is CCT rendering, followed by native simulation.

## Rebuild

The versioned source is in `scripts/research/`. Run from `caf-engineering-reference/` with Python 3.10+ and lxml:

```sh
python3 scripts/research/build_ahu1_sequence_r2.py examples/ahu-1/AHU-1_latest_AvgControlRedirect_VERIFIED-OPEN.caf candidates/ahu-1/r2
python3 scripts/research/validate_ahu_integrated_candidate.py candidates/ahu-1/r2/AHU-1_Sequence_R2_CCT_TEST.caf candidates/ahu-1/r2/AHU-1_Sequence_R2_Manifest.json candidates/ahu-1/r2/AHU-1_Sequence_R2_Behavior_Checks.json
python3 scripts/caf_module_catalog.py audit-display candidates/ahu-1/r2/AHU-1_Sequence_R2_CCT_TEST.caf --reference examples/modules/*.caf examples/ahu-1/AHU-1_latest_AvgControlRedirect_VERIFIED-OPEN.caf --output candidates/ahu-1/r2/AHU-1_Sequence_R2_Display_Audit.json
```
