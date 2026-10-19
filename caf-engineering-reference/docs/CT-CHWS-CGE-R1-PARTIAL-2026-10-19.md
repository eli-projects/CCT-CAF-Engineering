# CGE09090 CT CHWS native evidence and R1 partial construction

**PARTIAL_CANDIDATE_CCT_NOT_EXECUTED.** The newly supplied `CT CHWS.caf` resolves the target-controller starter prerequisite. It does not establish native acceptance of this generated candidate. The source native is now also retained in `skills/create-cct-caf/assets/native/CGE09090_CT_CHWS_10.8.caf`; the candidate bytes remain in the user's project files. See SUBMITTAL-ONLY-GENERATION-2026-10-19.md for the later internal-profile workflow.

## Native evidence

| Item | Observed value |
|---|---|
| Source | CT CHWS.caf |
| Source SHA-256 | `e896bab23c944d08b3eb3e309cd813cd66b4b7ab0b22d3c2a4476c754eef76d2` |
| Controller | M4-CGE09090-0 |
| CCT saved version / controller release | 10.8.0.60 / 10.8 |
| ACS / DMCS | 68 / 65 |
| Native records | 2,085 objects, 20 graphs, 885 connections |
| Hardware | XPM09090 at SA4; XPM04060 at SA5; XPM09090 at SA6 |
| Display | MS-DIS1710-0 at SA3; differs from specified M4-DLK0350-0 |
| Hardwired source objects | 20: 10 AI, 2 DI, 4 DO, 4 AO |
| Source registry | 24 paired unique entries, includes four AO readbacks |
| Required project I/O | 35: 19 AI, 8 DI, 4 DO, 4 AO |

The native source is an existing chiller/pump/two-zone-mixing program. Controller/expansion/display object records and main paired hardware registry are retained exactly. The builder reuses the 20 physical objects at the scheduled terminals and retargets their existing proxies; it does not invent missing physical objects or registry identities. There are **15 missing physical inputs**, exposed as named SIM-* inputs for offline tests only.

Eight reused physical RTDs have setup property 518 = 3, identified as **Nickel** by the supplied release definitions. The drawing calls for 1k Platinum. No Platinum numeric setup is guessed. The DP electrical format is copied from an observed native AHU 4–20 mA physical input; its retained 0..25 psi span remains provisional. Flow remains source 0–10 V / 0..100 pending the submittal's Vdc/current conflict and missing full scale.

## Scoped construction

- Native sequencers: pump `8-1/575_1.571_80431`, HX `8-1/575_1.571_80099`; only devices 1/2 enabled and demand 0/1. Native sequencing/minimum-time behavior is not executed here.
- Proven pump hours use native class 591 totalizers `8-1/575_1.591_80421` and `.591_80424`, period 3600; HX duty hours use `.591_80466` and `.591_80467`. Pump hours provide runtime ranks. HX lower-duty-hours preference is provisional. Weekly/monthly rising-edge inputs are external contracts; calendar schedules and persistence acceptance are absent.
- Retained DP PI: `8-1/575_1.536_83041`. A complete native CGE PI subtree is cloned for header LWT cooling, with provisional water process/range/tuning. Source 10 psi DP SP and 65 F LWT SP are not approved design settings.
- New Activities: CT PUMP CONTROL, CT HX TRANSFER AND FAULTS, CT BUILDING VALVE OUTPUTS, CT PROCESS ALARMS. Fault/maintenance immediately gates pump output off. Speed clamp 20..100%; the 20% native minimum is observed at `8-1/575_1.536_81398.2_207362`, retained provisionally.
- Custom logic includes separate 300 s HX overlap, 30 s isolation-end mismatch and 120 s / >=10% valve deviation functions, with manual isolation and previous-scan availability memories. Source mismatch definitions are preserved; both/neither end-switch policy is incomplete.
- LWT PI requires at least one isolation command with open-only proof. Pump startup is not interlocked to a proven HX path; approved startup, rollback, unavailable and bad-quality policies remain incomplete.
- Specified temperature and DP alarm thresholds/default delays are implemented. Low flow stays disabled at LOWFLOW-SP=0. BTU measurement/average/validity and adjustable-margin comparator are interfaces only; calculation/trending/averaging and VFD kW integration remain absent.
- All eight physical-output wires are redirected to the CT path. Legacy modules remain for comparison; legacy diagnostics do not validate the CT sequence. SYSTEM-EN=False and CONFIGURATION-READY=False remain stored defaults.

The reviewed Mux rule is used for all new custom selectors: Selection [1,2], Default Input 0. Historical inverted Mux maps and their withdrawn model passes are not construction evidence. Boolean and enum 647 off/on signals remain distinct.

CCT Help references: Sequencer pages 1504–1510, Totalization pages 1568–1569. These describe expected native behavior; they are not execution results.

## Reproducible tools

`scripts/research/build_ct_chws_candidate.py` requires the exact source CAF, lxml and the pinned repository references at `c715dbfe9f3f9bb2a38dbd631b797d8afbfbd598`. It hash-guards the source, native AHU primitive source and helper scripts; preserves ZIP metadata/comment/member; allocates unique refs; preserves native port order and unknown metadata; refuses an existing candidate path. This is a project-specific builder, not a universal CAF generator.

```sh
python3 caf-engineering-reference/scripts/research/build_ct_chws_candidate.py /absolute/path/CT_CHWS.caf /absolute/path/CCT-CAF-Engineering /absolute/path/fresh-output
python3 caf-engineering-reference/scripts/research/verify_ct_chws_candidate.py /absolute/path/fresh-output/CT_CHWS_R1_PARTIAL_CCT_TEST.caf /absolute/path/fresh-output/CT_CHWS_R1_Manifest.json /absolute/path/CCT-CAF-Engineering /absolute/path/model-checks.json
```

The source path may differ in filename; its bytes must match the pinned source hash. The verifier exercises the actual serialized custom Activities with the reviewed independent interpreter. Native sequencers/PIDs/totalizers/memories and physical I/O are explicit unsupported boundaries.

## Actual results

| Check | Result / scope |
|---|---|
| Candidate SHA-256 | `8bdd1aae8732a4aec7426fa73f77f3cfc700fe494bdfbe6ad88518449b15d6aa` |
| Source diff | 860 new objects, 64 changed source objects, 2,021 source objects unchanged after known ref relocations; no source objects deleted or class IDs changed |
| Preflight | PASS for structural subset: 2,945 objects / 45 matched classes / 25 graphs / 1,265 connections |
| Observational display audit | No reported structural/registry issues, unobserved display combinations or uncovered classes |
| Independent custom model | 25 scenario groups pass; scoped serialized custom logic only |
| Reproduction | Two fresh builds are byte-identical; source hash unchanged |
| Existing repository regression suite | 15 tests pass; separate from CT candidate behavior |
| CCT open / compile / resources / Simulation | NOT EXECUTED |
| Field acceptance / transfer | NOT EXECUTED |

The 25 model groups cover the configuration guard, speed bounds/standby zero, proof failure and manual reset, immediate VFD/maintenance exclusion, all-pumps-unavailable outputs, hand alarm, HX permission, mismatch/deviation boundaries, overlap/close-timer separation, manual isolation, valve gating, temperature/DP thresholds, adjustable DP delay, low-flow settings and external BTU validity/margin. Native selection and PI values are substituted inputs; the model does not prove automatic transfer or closed-loop performance.

The project record retains source-located R01–R35 requirements, P01–P35 points and 17 unexecuted native CCT test cases. Current requirement status counts are 14 implemented_candidate, 16 pending_input and 5 external_integration. Candidate status is not acceptance.

## Completion and native validation

1. Obtain a CCT-saved source copy with all 35 physical inputs/outputs at the scheduled terminals, specified Platinum sensor curves, correct discrete/current/voltage setup, proxy/registry metadata and confirmed display. Rebase the custom logic onto that observed native configuration rather than manufacturing identities.
2. Resolve LWT SP from T5-M6.2.1; DP SP/span; flow signal/full scale/units; pressure-transmitter hardware; terminal callout conflicts; output and contact polarities; pump/VFD limits and proof delay; reset/bad-quality/startup/transfer/unavailable priorities.
3. Complete weekly/monthly schedule ownership and restart handling, BTU calculation/average/baseline, low-flow threshold and VFD kW object/network bindings.
4. Open unchanged source then exact candidate hash in compatible CCT. Record CCT/device-package versions. Verify Configuration/Control/Logic rendering; a blank Control tab fails. Run compile/resource checks.
5. Simulate native least-runtime sequencing/ties/exclusions, weekly/monthly edge triggers, min-on/off behavior, actual PID action/limits/override tracking, memory scan order and totalizer persistence. Exercise all timer boundary/rollback/availability/reset cases, both/neither proof, missing quality, communication loss and restarts. Restore offline defaults and record hash-scoped results. Do not promote static/model passes to native acceptance.

Existing AHU failures and R3 review statuses remain independent; this addition does not supersede their evidence or turn this CGE partial candidate into an accepted baseline.

## Later archive/provenance clarification

The submittal-only factory forward test found that Python `writestr` substitutes default permissions when source ZIP external_attr is zero. Earlier R1 scripts did not restore this attribute; their broad ZIP-metadata preservation claim has that exception. The current retained-profile factory restores source archive attributes before closing and tests them. This correction changes archive bytes/hash, not the XML control graph, and does not establish CCT acceptance. Its manifest also separates the historical constructor/helper reference commit c715dbf from the retained-library reference commit 2082a82 and records the factory hash.
