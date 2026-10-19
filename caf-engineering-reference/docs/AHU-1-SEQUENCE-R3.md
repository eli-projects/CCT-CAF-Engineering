# AHU-1 R3: readable Activities and CIP restoration interface

**October 19 erratum:** This document describes the original R3 design. The user subsequently edited and simulated R3, with no detailed pass/fail results supplied. The edited-file review found 36 reversed custom Mux maps inherited from the generated file. Earlier model passes are withdrawn. Use [the reviewed correction and evidence](AHU-1-R3-EDITED-LOGIC-REVIEW-2026-10-19.md); its own native CCT acceptance remains pending. Historical opening claims below are time-scoped to the initial delivery.

**Candidate:** `AHU-1_Sequence_R3_CCT_TEST.caf`
**SHA256:** `dd96ed08ac8557635b19db812f62aea760a2dbefd9c5323f53c9e651198a3648`
**Evidence:** Offline checks only. R3 has not been opened, compiled, or simulated in CCT. The user reports that source R2 build 2.1 opens and its custom logic is visible; they have not simulated R2.

## What changed

The two broad custom diagrams are now `AHU SYSTEM CONTROL` and `AHU OUTPUT PERMISSION`. Their work is divided into smaller Activities: temperature demand, humidity/CO2 demand, CIP recovery, safety status, input health, setting checks, timed overrides, run permission, recovery targets, refrigeration request, desiccant request, and mode indicators. Input health has smaller zone, equipment, operator, and setting checks. Output permission separates fan quality, fan proof, fan/coil permission, and valve outputs.

Saved block positions use dependency columns with input pins on the left and output pins on the right. There are no backward signal edges in these custom graphs and no overlaps between the estimated block rectangles. CCT still controls final wire routing and actual block dimensions; this is not a claim of a verified CCT rendering.

The non-CIP primitives retain their native configuration and port defaults. A hierarchy-flattening regression check verifies their original input connections and the existing published outputs after routing through the new Activity boundaries. Sensor/hardware configuration, averages, three-zone temporary occupancy, and the paired hardware registry are preserved. R3 changes three original diagram objects and preserves 2,268 other original objects byte-for-byte; the old custom internals are replaced with cloned primitives and typed boundary ports.

## CIP behavior and its required external work

**This CAF does not provide standalone durable CIP storage.** It supplies a restoration interface for a separately implemented and commissioned SNE/supervisor record. Without that integration it remains blocked, rather than guessing that a previous cleaning cycle finished. Do not transfer it for operational use as a completed retention solution.

CCT Help, Timer, printed pp. 1698-1700, explicitly says the Timer resets on power failure, controller restart, and disable/re-enable. “On Delay with Memory” describes a latch while executing; it does not provide persistence. Official reference: <https://docs.johnsoncontrols.com/bas/r/Metasys/en-US/Controller-Tool-Help/17.0/Logic/Timing/Timer>.

CCT Help also documents **Restore Command Priority** for AV/BV objects and **Restart Options > Default** for preserving network-input commands (printed pp. 365, 1605, 1622). Those options do not demonstrate retention of a timer's internal state or a logic-generated cleaning/recovery record. R3 does not invent unobserved CAF properties to enable that behavior.

| Restored record | R3 behavior |
|---|---|
| Confirmed clear; no active cleaning or recovery | Ordinary startup can run through existing safeties and demand logic; there is no new one-hour CIP startup delay. |
| CIP still active | Remain off. A real transition to cleaning complete starts the full local recovery hour. |
| Recovery incomplete | Remain off for the restored recovery interval; no fresh hour is started solely because the controller restarted. |
| Record unknown, incomplete, or unreliable | Remain off until authoritative data is supplied. This is not an hour timer and will not clear itself after an hour. |

The local Off Delay is driven by confirmed cleaning after record restoration. It enforces at least 3,600 seconds from a real CIP completion. Repeated cleaning restarts the local hour at the latest completion. Startup uncertainty does not manufacture a cleaning event. A remaining-time value of zero cannot release the unit while the restored block remains true.

## Three new supervisor inputs

| Input | Default | Required contract |
|---|---:|---|
| `CIP-MEM-VALID` | False | Fresh confirmation for this startup that the cleaning/recovery record is authoritative and all related values have been restored. |
| `CIP-MEM-BLOCK` | True | Maintained lockout derived from the retained cleaning state and recovery record. |
| `CIP-MEM-LEFT` | 0 seconds | Remaining recovery time for display; use 0 while cleaning is active or when confirmed clear. |

`CIP-MEM-FAULT` is a new published output on `AHU SYSTEM CONTROL`; it reports an unconfirmed or unreliable restoration record. Existing `CIP-BLOCK`, `CIP-TIME-LEFT`, `EF-PURGE-REQ`, and `EF-PURGE-%` retain their names. `CIP-TIME-LEFT` is the maximum of local and restored remaining time; 0 does not mean the unit is permitted to run.

### SNE implementation contract — not yet configured

1. Keep a durable per-AHU record containing record identity/version, state (`CLEAR`, `CLEANING`, or `RECOVERY`), the latest confirmed CIP state, cleaning-completion time, effective hold duration, and release time. Store state changes durably; a trend/history sample alone is insufficient. Verify actual storage and restart semantics on the chosen SNE/server implementation.
2. Persist `CLEANING` before accepting a new cleaning command. Command and maintain `CIP-REQ=True`. On confirmed cleaning completion, persist `RECOVERY` and its release time before allowing `CIP-REQ=False`. Never infer completion from an offline controller or an uninitialized False value.
3. At controller startup/reconnection, invalidate the handshake. Restore the authoritative `CIP-REQ`, `CIP-MEM-BLOCK`, and `CIP-MEM-LEFT`; write `CIP-MEM-VALID=True` last. In CCT, ensure that a stale True command to `CIP-MEM-VALID` is **not restored** by either Default or Operator Override restart options. Verify its actual startup False state on hardware; the configured default alone is not proof.
4. During `RECOVERY`, keep `CIP-MEM-BLOCK=True` and update remaining seconds from the stored release time. At safe expiration, persist `CLEAR`, write remaining time 0, and release `CIP-MEM-BLOCK`. Do not release before the configured minimum or while cleaning is active. Changing the hold time must never shorten an in-progress committed interval; extend the durable release time if the local effective interval is extended.
5. If a completion event was missed during an outage, retain `CLEANING` until a fresh, authoritative completion is confirmed. Then apply a full hour from that confirmation. If the record or clock cannot be trusted, invalidate the handshake and retain the lockout. On total supervisor/controller restart, restore the durable record before authorizing the handshake.
6. Define the treatment of downtime explicitly. A UTC release timestamp implements elapsed time after confirmed cleaning completion. The sequence also calls for the dedicated exhaust fan during cleaning and the following hour. Exhaust operation, availability/proof, and the treatment of an exhaust power outage must be resolved as part of that external integration; R3 contains request signals, not exhaust proof or a purge-runtime accumulator.
7. Verify communications-failure handling and reconnection. R3 has no new network heartbeat detector; a previously reliable True handshake can become stale unless the configured integration invalidates it. Do not treat this interface alone as a complete communications watchdog.

No SNE application has been installed or modified by this work. Its target objects, durable storage and heartbeat strategy still require site-specific implementation.

## First CCT tests

1. Open in Configuration mode; verify the main diagram and all nested custom Activities render. Run compile/validation and device memory checks for the installed CGM/XPM packages. R3 has more boundary ports and Activities than R2, so resource acceptance must be checked.
2. In Simulation, initially expect `CIP-MEM-FAULT=True` and `CIP-BLOCK=True`. For a **simulated known-clear record only**, set `CIP-REQ=False`, `CIP-MEM-BLOCK=False`, `CIP-MEM-LEFT=0`, and then `CIP-MEM-VALID=True`. A cooling demand should now run without waiting an hour, subject to existing master/safety/fan logic. Do not use a permanently forced Valid value as an operational fix.
3. Assert CIP; keep it true longer than an hour. Clear CIP and verify a full new hour. Repeat cleaning during recovery. Check purge requests throughout, including missing-memory state. These checks do not prove that the separate exhaust actually runs.
4. Simulate restart into an authoritative 1,500-second recovery record: restore block True, remaining 1,500 and Valid True. Decrease remaining according to the supervisor clock, retain the block until expiry, then clear it. Verify no additional hour is imposed. Power-cycle the actual controller and supervisor to test the integration; stopping/restarting a local timer model is not hardware evidence.
5. Repeat with active cleaning, missing record, bad-quality inputs, stale handshake, clock faults, prolonged exhaust outage, and repeated restarts. Then exercise the prior thermal/RH/CO2, override, mode, fan-proof and safety cases against native outputs.

The prior external exhaust, refrigeration, desiccant, display/HMI and provisional coil/fan settings still need the integration and design review recorded in the R2 notes.

## Offline evidence and reproducibility

`AHU-1_R3_Manifest.json`, `AHU-1_R3_Layout.json`, `AHU-1_R3_Behavior_Checks.json`, and `AHU-1_R3_Display_Audit.json` accompany the CAF. Behavior checks execute an independent interpreter of the serialized custom graph: they do not execute CCT, existing AHU FSMs/PIDs, supervisory logic, or actuator responses. Restored records are test inputs, not proof of persistence.

From `caf-engineering-reference/` (or the equivalent root in the test package):

```sh
python3 scripts/research/revise_ahu1_r3.py candidates/ahu-1/r2_1/AHU-1_Sequence_R2_CCT_TEST.caf candidates/ahu-1/r3
python3 scripts/research/validate_ahu_integrated_candidate.py candidates/ahu-1/r3/AHU-1_Sequence_R3_CCT_TEST.caf candidates/ahu-1/r3/AHU-1_R3_Manifest.json candidates/ahu-1/r3/AHU-1_R3_Behavior_Checks.json
```

The historical build commands above describe the original test package. The repository now preserves the original, edited and corrected review CAFs and the corrected-model reproduction commands in the October 19 review. Do not use the historical incorrect-Mux interpreter as validation. Promotion still requires native CCT and power-cycle evidence.
