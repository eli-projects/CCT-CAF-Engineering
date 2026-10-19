# AHU-1 edited R3 logic review

## Main finding

The original generated R3 copied a MUX configuration that reverses the intended Boolean selection. The defect appears in **36 custom MUX blocks**: 19 in AHU SYSTEM CONTROL, 16 in AHU OUTPUT PERMISSION, and MUX 400030 in ZONE-TOCC-OR. It predates the user's layout edits.

The earlier verifier interpreted the selection table as zero-based input indexes and ignored Default Input. That interpretation was wrong. The earlier R3 modeled passes must not be treated as validation of the uploaded file's actual selector behavior.

A separate correction candidate fixes only the mode map and Default Input on those 36 MUXs. It preserves every saved position, block order, connection, wire metadata record, point/default setting, hardware binding, and object identifier from the uploaded file. No live controller or supervisory application has been changed.

## Files and evidence levels

| File | SHA256 | Evidence |
|---|---|---|
| Original generated R3 | `dd96ed08ac8557635b19db812f62aea760a2dbefd9c5323f53c9e651198a3648` | Earlier generated file; its old model used an incorrect MUX interpretation. |
| Uploaded Edited(1) | `d8554931f40cc2d69f515c004964281b6f0c9e1e9dcacf7d1a984e4ac914fe51` | User reports editing positions and using CCT Simulation. Specific input/output test results were not supplied. |
| MUX correction candidate | `46b41438f157068c5546210a54f733859df617abcc2f83a2e6f99ba4afd86a64` | Structural preservation checks, 8 occupancy combinations, release transitions, output-gate probes, and 28 scenarios in the corrected independent model pass. **CCT opening, compilation, native simulation and commissioning remain unverified for this candidate.** |

Each file contains 3,411 serialized objects. The candidate changes exactly properties 2381 and 3122 on the 36 selected MUX objects; all other serialized objects/properties are preserved. The uploaded CAF remains unchanged.

## The three layout Activities

| Activity | Name | Review |
|---|---|---|
| 500762 | AHU OUTPUT PERMISSION | Position and display-order changes retained. Its selector-map defect is covered by the correction. |
| 500019 | AHU SYSTEM CONTROL | Position and display-order changes retained. Its selector-map defect is covered by the correction. |
| 600151 | RUN PERMISSION | Positions retained. The two inputs of OR 600659, Native Safety Control Permission, were interchanged. This preserves the Boolean result: run permission OR safety trip. Four MUXs here require the selector correction: 600643, 600651, 600663 and 600668. |

The original/edited comparison finds 58 changed objects: layout records on 27 diagrams, display-order records on four objects, 27 saved simulation values, one save record, the OR input interchange, and an internal flag on three occupancy-display proxies. Several changes can occur when CCT saves diagrams after layout/simulation work; the comparison alone does not identify which were explicit user actions.

The 27 simulation values are numerically the same as the corresponding configured defaults. The three occupancy-display proxy records 300059/300074/300089 change property 4127 from True to False. Their bindings and occupancy wires are preserved. The meaning of that internal flag has not been established; it is not labeled as a logic defect or silently reset. The correction preserves the user's CCT-saved values.

Actual wire routing and visual overlap require CCT display inspection; a CAF-coordinate comparison is not a screenshot review.

## Activity 400008 and MUX 400030

The path is:

`ZN1/ZN2/ZN3 temporary-occupancy requests -> enum-to-Boolean translations -> OR -> MUX 400030 -> native Temporary Occupancy input`

The request enumeration is **Inactive=0, Active=1**. It is a request to the native occupancy resolver, not the Occupied/Unoccupied/Bypass/Standby state itself. The translated requests and two OR gates implement the intended any-zone Boolean condition.

MUX 400030's unwired data inputs intentionally supply constants:

- **Input 1 default value: Inactive (0)**
- **Input 2 default value: Active (1)**

That is a valid way to translate a Boolean into a two-state enumeration. The error is in selecting those constants.

| Any-zone Boolean mode | Uploaded MUX map | Corrected MUX map |
|---|---|---|
| False | Mode 0 is unassigned; Default Input 2 supplies **Active** | Input 1 supplies **Inactive** |
| True | Mode 1 selects Input 1, supplying **Inactive** | Input 2 supplies **Active** |

In the uploaded serialized record, the mode table is `[0,1,0]` and Default Input is 2. The table addresses data inputs by **1-based input number**; 0 invokes Default Input. The correction sets `[1,2]` and Default Input 0, meaning no fallback is needed because both Boolean modes are explicitly assigned.

This interpretation is supported by the CCT-authored Boolean MUX 265243 in the same file: it has exactly two data inputs, table `[1,2]`, and Default Input 0. A zero-based interpretation would wrongly select a nonexistent third data input for True. This is an empirical CAF-format finding; CCT Help describes MUX mode/default behavior but does not publish this XML schema. Confirm the visible Input 1/Input 2 Mode buttons in CCT when opening the candidate.

### Occupancy truth table

0 means Inactive; 1 means Active. These are corrected-model results, not newly observed CCT runtime values.

| ZN1 | ZN2 | ZN3 | Uploaded output | Corrected output |
|---:|---:|---:|---|---|
| 0 | 0 | 0 | Active | Inactive |
| 0 | 0 | 1 | Inactive | Active |
| 0 | 1 | 0 | Inactive | Active |
| 0 | 1 | 1 | Inactive | Active |
| 1 | 0 | 0 | Inactive | Active |
| 1 | 0 | 1 | Inactive | Active |
| 1 | 1 | 0 | Inactive | Active |
| 1 | 1 | 1 | Inactive | Active |

All three isolated button pulses and returns to Inactive pass in the corrected model. A maintained OR does not create a second rising edge when another button is pressed while one request remains Active; the physical buttons should release as momentary requests. Test an unavailable sensor separately in CCT; the model is not proof of native reliability/rearm behavior.

The activity output is correctly wired to the native occupancy resolver, object 51131, Temporary Occupancy port 3110. Its effective occupancy feeds the three sensor displays and AHU SYSTEM CONTROL. The native bypass setting remains **3,600 seconds**.

For a CCT bypass test, set `OCC-SCHEDULE=Unoccupied` and `OCC-OVERRIDE=Not Set`, then pulse each TOCC Active -> Inactive. The saved schedule currently defaults to **Occupied**, which prevents the native bypass timer from operating. A higher-priority explicit occupancy override can also prevent bypass. Effective Bypass does not itself guarantee fan operation in this demand-cycling application.

## Other logic: the output gates are the most serious consequence

The same reversed MUX map appears in the output permission Activities. In an isolated model probe with run permission=False, safety trip=False, native fan command=On, proof=On and raw outputs 50/100/70/80/60%, the uploaded graph passes the commands shown below:

| Output | Uploaded graph, run permission False | Corrected graph, run permission False |
|---|---:|---:|
| Fan command | On | Off |
| Fan speed | 50% | 0% |
| OA damper | 100% | 0% |
| Cooling valve | 70% | 0% |
| Pre-cooling valve | 80% | 0% |
| Heating valve | 60% | 0% |

These are modeled graph outputs with explicitly injected native signals. They are not measurements from CCT or real equipment. The finding is sufficient to withhold operational acceptance of the uploaded configuration and prioritize a native CCT shutdown test.

After the map correction, the model verifies normal output permission, coil shutdown on absent/unreliable fan proof, and reliable shutdown during CIP. A confirmed safety trip stops fan/damper while retaining the existing native safety-valve command path. That protection path intentionally has different priority from ordinary demand control and must be exercised against the real native FSMs.

The 28 corrected-model scenario groups also cover cooling/heating hysteresis, RH and CO2 demand, unoccupied operation, manual On/Off/Cancel priority and expiry, special-mode requests, input/parameter faults, desiccant rotation fault, local CIP recovery, repeated cleaning, restored recovery, and unknown memory. Existing native PIDs/FSMs and the physical sensor averages are not executed by this interpreter.

## Remaining sequence/integration items

- **CIP retention remains external work.** `CIP-MEM-VALID=False` and `CIP-MEM-BLOCK=True` are the saved defaults. The corrected unit remains blocked until a fresh authoritative restoration is supplied. For a simulated known-clear record only: set CIP-REQ=False, MEM-BLOCK=False, MEM-LEFT=0, then MEM-VALID=True. A real cleaning cycle still starts at least a full hour of recovery at completion.
- **Durable storage and communications:** the CAF does not store a durable cleaning/release record and does not implement a new supervisory heartbeat. A stale valid/clear record must be invalidated by the commissioned integration. CCT Help documents a Supervisor Status block with one-minute communication-loss detection; it is an available design option, not functionality added in this correction.
- **Exhaust, refrigeration and desiccant:** the published requests still require external mapping and actual equipment feedback/commissioning. A request alone does not operate or prove the separate exhaust fan. The treatment of outage time during the required purge still needs resolution.
- **Fan and temperature settings:** SF-RUN-% remains a provisional fixed 50%; pre-cooling/discharge settings remain provisional. The current drawings do not identify the modulating duct-pressure feedback needed for an actual pressure loop.
- **Sequence interpretation:** the sequence contains both occupied fan-run language and a requirement to stop the AHU when conditions are satisfied. The existing agreed demand-cycling interpretation is retained. The sheet also labels the settings “vegetable and nut processing” while identifying the AHU as serving meat processing. Distinct Warmup/Cooldown/Setup targets/exit rules still require design clarification.

## CCT acceptance order

1. Open the new candidate in Configuration mode and confirm that your layouts remain. Inspect MUX 400030: Input 1 Modes=False; Input 2 Modes=True; constants Inactive and Active respectively. Both modes are explicit, with no default input required.
2. In Simulation, test all-Inactive -> each single Active -> all-Inactive while watching the OR output, MUX output, native Temporary Occupancy, and EFF-OCC. Use Unoccupied schedule and Not Set override for the bypass test.
3. With known-clear simulated memory, verify demand can enable the AHU. Set run permission False and verify the final fan/speed/damper/valve commands stop as intended. Test CIP and unreliable fan-proof/native commands independently. Then exercise native safety-valve protection.
4. Test real CIP completion, one-hour hold, repeated CIP, manual override expiry and conflicts, all special modes, and sensor/parameter failures. Perform native compile/resource checks and an authorized controller/supervisor power-cycle test before operational acceptance.

## Sources and package

- Uploaded CAF and the original R3 from the saved R3 test package; exact hashes are above.
- Johnsons Controls CCT Help.pdf: printed pp. 170 and 226-227 (MUX configuration), 1690-1691 (selection and reliability), 1129-1131 (occupancy/bypass), 1698-1700 (timer reset behavior), and 1638 (Supervisor Status).
- MCCD Ag AHU-1 HW submittal(3).pdf: PDF page 9, drawing 1.14, sequence; the bottom DCV paragraph was visually checked and specifies 100% outside air to maintain CO2 below 1,000 ppm.
- Official occupancy reference: https://docs.johnsoncontrols.com/bas/r/Metasys/en-US/Controller-Tool-Help/17.0/State-Generation-Modules/State-Determination/Occupancy-Mode-Determination/Primary-States-Occupancy-Mode-Determination

The accompanying package contains the candidate, full per-MUX change list, eight-case truth table, output probes, 28 modeled results, corrected verifier, and a minimal repair script for this exact uploaded CAF. The preserved layout is now a useful reference, but the corrected candidate needs its own CCT acceptance.

## Repository reproduction

The three exact CAFs are in `../experiments/review/2026-10-19/`. The uploaded filename's `(1)` suffix was removed in the repository; its bytes and hash are unchanged. They are review specimens, with no full-sequence operational acceptance.

From `caf-engineering-reference/`:

```sh
python3 scripts/research/repair_reviewed_mux_maps.py experiments/review/2026-10-19/AHU-1_Sequence_R3_CCT_TEST_Edited.caf /tmp/AHU-1_R3_MUX_Correction_CCT_TEST.caf
python3 scripts/research/verify_custom_graph.py /tmp/AHU-1_R3_MUX_Correction_CCT_TEST.caf data/r3-review/corrected-model-manifest.json /tmp/AHU-1_R3_Model_Checks.json
python3 -m unittest discover -s tests -v
```

The repair is restricted to the exact edited source hash. It is not a general Mux migration tool. The model does not run CCT, native PIDs/FSMs, a supervisor, or physical equipment.
