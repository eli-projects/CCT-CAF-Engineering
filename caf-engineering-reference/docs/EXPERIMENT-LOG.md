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

## Important error correction

An earlier audit asserted a nested temperature dependence in **Unit Enable Determination** based on object ID `10002`. Further inspection found the suspicious internal block produced a **Boolean** and the numeric match did not demonstrate a live `ZN-T` temperature connection. **That claimed dependency is unconfirmed** and must not be used to justify changes. User's connected network input `UNITEN-MODE` and output `UNITEN-STATE` reflect the intended State Generation logic.

## Conditions for promoting an experiment

1. CCT opens with the complete Application Control diagram (not blank/empty).
2. Added module and connection details are visible.
3. CCT Simulation is exercised with expected inputs and outputs; include failure and boundary values when relevant.
4. No unintended hardware address, state-table, default parameter, or safety-interlock changes.
5. Record CCT version/device package, input CAF SHA256, resulting CAF SHA256, exact delta and user-reported acceptance.
