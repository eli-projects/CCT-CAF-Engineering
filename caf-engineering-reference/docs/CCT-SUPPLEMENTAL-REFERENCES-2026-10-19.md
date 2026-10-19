# CCT supplemental reference notes

Reviewed 26 supplied files on October 19, 2026. These references add CCT class and signal definitions, release metadata, simulator component identities, perspective layouts and a module/point catalog to the existing CAF examples.

**What the files provide**

| Source | Verified content | Use in CAF work |
|---|---|---|
| 15 `.pml` files | XML perspective layouts containing widgets, UI-column criteria and, in the focused views, explicit BACoid filters | Organize inspection by equipment function and reproduce readable review views |
| `Perspectives_Active_Modules.xlsx` | 14 worksheets with 623 ID references, including flow-detail and tuning widgets; 426 distinct instance numbers across the collection | Identify named native modules and the views that include them |
| `Perspectives Description.docx` | Describes each perspective and explains the Module-Logic selection behavior | Choose a suitable review view |
| `CCT_README(1).html` | General CCT overview; Help LIT-12011147, installation LIT-12011529 and licensing Help LIT-12012389 references | Locate the related documentation and patch portal |
| `2026F29 Reference(1).pdf`, page 1 | Points to Flash Sheet 2026F29 about CCT 18.0.3.5 | Establish which Flash Sheet to consult; the supplied page does not contain the patch fixes or compatibility details |
| `classCache.xml` | 132 object classes; 2489 direct property declarations, inheritance, constraints, views and commands | Check CAF class identities and property serialization against the supplied release definitions |
| `signals.xml` | 15 classes and 59 signal definitions, including sensor/control-point port mappings and per-signal defaults | Check I/O signal and port construction |
| `meta.xml` and `release.xml` | Package identity and release/database/ACS/DMCS settings | Keep the construction references tied to their release mode |
| Three `cctsimmce-*.dll` files | Native 32-bit Windows Field Controller Simulator components with version resources and exports | Identify the supplied simulator components and a possible future integration surface |

**Checks and application to the current AHU**

All 15 PML files parse as perspective XML. All 623 workbook ID references were located in the corresponding PML widget, allowing for spacing differences in the tuning-widget labels. The instance portion of each packed PML BACoid was compared with the workbook number; where checked against the AHU CAF, both object type and instance were matched.

The PML files contain display definitions. They supply no executable module internals, parameter tables or block wiring for constructing a CAF. Continue to derive those details from known-good native CAF examples and the Controller Tool Help, and verify the resulting program in CCT.

The focused AHU views use explicit IDs for Setpoint/Miscellaneous, State Generation and Output Control. They do not include custom activities 400008, 500019, 500762 or 600151 in those ID lists. An omitted block in one of these views therefore does not establish that the block is missing from the CAF.

`Module-Logic.pml` uses UI-column criteria for these groups instead of fixed BACoid lists. It puts modules above logic/system information. The description document instructs users to leave **Freeze Selection unchecked** so selecting a module updates the lower logic view. Open the parent activity to inspect nested activity 600151 under 500019.

In the corrected AHU review file, exact type-and-instance matches to listed native modules total 13 for AHU-Cooling, 16 for AHU-Heating, 16 for AHU-Fan and 6 for AHU-Econ. The other listed objects cover equipment options and configurations; these counts do not establish an error or prove control behavior.

The native occupancy module is listed as **Occupancy Mode Determination**, instance **51131**, and matches `8-1/575_1.524_51131` in the AHU. Custom zone-occupancy activity 400008 and its Mux 400030 require inspection within the custom program. The new references supply no additional evidence about that Mux mapping.

**Release definitions and simulator components**

The package metadata explicitly labels this set **10.8 / Firmware 12.0**. This is the package's release-mode label; it does not establish the installed CCT application version or the firmware currently running in a field controller.

| Field | Supplied value | AHU comparison |
|---|---|---|
| Package name | 10.8 / Firmware 12.0 | CAF root release-mode string is 10.8 |
| Package build | 1.6.0.112; build date 2026-06-03T08:26:36 | Package metadata only; no installation comparison performed |
| DatabaseVersion | 10.8.0.60 | Retained as a release reference |
| AcsVersion | 68 | CAF root property 4128 is 68 |
| DmcsVersion | 65 | CAF root property 4129 is 65 |
| DefaultDeviceClass | 862 | Default metadata only; the actual AHU root class is 194 |
| ProtocolRevision | 19 | Declared release value |
| SimulateAllObjects | true | Configuration flag; no simulation was run |
| FcCommunicationModeSwitchPossible | true | Configuration flag |

The class cache contains 132 classes and 2489 direct property declarations. Every declared superclass is present, and all inheritance chains are acyclic. Both AHU CAFs contain 3,411 objects using 49 distinct classes; every class and class version matches a definition in this cache. These checks cover class identity and version only. They do not establish full CAF schema validity, control behavior, hardware suitability or successful CCT import.

Mux 400030 belongs to class **562**. The supplied declarations add these specific checks:

| Property | Declaration | Consequence for CAF checks |
|---|---|---|
| 2381, selection table | List of unsignedShort values | Serialize the map as a list with unsigned-short elements |
| 3122, default input | unsignedShort; allowed range 0–1000; cache default 1 | Explicit values must have the declared type and range; do not confuse the cache default with an explicit CAF setting |
| 2380 | unsignedShort; range 2–1000; cache default 2 | Additional declared Mux constraint |
| 961, 7000 and 85 | numeric | These port/output declarations are generic numeric definitions |

All 83 Mux objects in each compared CAF pass the limited stored-field checks for property 2381 element types and property 3122 type/range. The edited CAF's 400030 stores map `[0, 1, 0]` and default input `2`; the previously prepared correction stores `[1, 2]` and `0`. Both representations satisfy these metadata checks. The class XML does not explain selection-table indexing or fallback execution, so this review adds no new runtime proof to the earlier Mux correction.

The native occupancy class **524** declares property **3110** with enumeration set **649** and output **50032** with set **345**. These declarations help preserve the distinction between the temporary-occupancy input and effective-occupancy output when constructing and checking ports.

All 15 classes listed in `signals.xml`, including their referenced port classes, are present in the class cache. Signal definitions include sensor port classes **527/529** and control-point port classes **526/528**, along with signal IDs, type codes, coupling flags and optional property defaults. The signal file is a construction reference; it does not describe the AHU's application wiring or confirm physical terminal assignments.

All three DLLs identify themselves in their version resources as **Field Controller Simulator**, company **Johnson Controls Inc**, internal name **cctsimmce.dll**, product **Universal Field Controller**, file/product version **6.0.0.84**. Their PE headers identify native **32-bit x86 Windows DLLs** with no CLR runtime header. They import Windows components and Visual C++ runtime libraries. The IP, MSTP and Generic binaries are distinct; all three expose the same 251 export names.

Examples of exported simulator-related names are `fnMCEStartup`, `fnMCEStartupNew`, `fnMCEShutdown`, `fnMCETimeStep`, `fnMCESetSimulationNonRealTime`, `fnReadAttributes`, `fnWriteAttributes`, `fnDownloadData` and `fnMatLabSimColdStart`. Their names suggest a possible route for future native simulator integration. This is an inference from exported symbols. Function signatures, calling conventions, ownership rules, startup requirements and application loading procedures were not established by this review, and no functions were invoked.

This environment has no Windows runtime or CCT installation. No native simulation was performed. The DLL resource version is a component version, separate from package build 1.6.0.112 and release-mode label 10.8.

The package's FilePattern also references `FDB_Control.bak` and a `10.8-translations.zip`, which were not supplied in this batch. Those files were not inspected and their contents are not assumed. The package's short Hash field was recorded as provided; its hash scope/algorithm and package authenticity were not verified. Individual source SHA-256 values are recorded below.

**Perspective catalog**

Counts below are explicit BACoid references in each PML, including repeated references used by detail widgets. They are not counts of active modules in a particular CAF.

| Perspective | ID references | Intended review focus |
|---|---:|---|
| AHU-Cooling Control | 36 | Staged or chilled-water cooling |
| AHU-Econ Damper Control | 52 | Economizer control; outdoor-air flow detail |
| AHU-Fan Control | 72 | Supply, return and relief fans |
| AHU-Heating Control | 171 | Staged, hot-water/steam and gas heating |
| Fan Coil-Cooling Control | 21 | Fan-coil cooling |
| Fan Coil-Heating Control | 21 | Fan-coil heating |
| HP-Cooling Control | 16 | Heat-pump cooling |
| HP-Heating Control | 20 | Heat-pump heating and supplemental heat |
| Module-Logic | UI columns | General module and selected-logic inspection; UI-column filters |
| UV-Cooling Control | 26 | Unit-ventilator cooling; ASHRAE cycles 1, 2, 3 and W |
| UV-Heating Control | 28 | Unit-ventilator heating; ASHRAE cycles 1, 2, 3 and W |
| VAVDD-CD Damper Control | 34 | Dual-duct cold-deck control and flow detail |
| VAVDD-HD Damper Control | 43 | Dual-duct hot-deck control and flow detail |
| VAVSD-Damper Control | 34 | Single-duct damper control and supply-flow detail |
| VAVSD-Heating Control | 49 | Box/supplemental heating and tuning information |

**Importing a view**

The supplied Controller Tool Help, printed page 114, gives this sequence: **Settings → Perspective Management → Import**, choose the PML file, then **Open**. Import and rendering in a running CCT installation were not exercised in this review. Printed page 115 also notes that custom sizing and layouts are not preserved when a perspective is exported.

**Useful AHU module mappings**

Names below come from the supplied workbook and were matched to exact object identities in `AHU-1_R3_MUX_Correction_CCT_TEST.caf`. Instance numbers alone should not be treated as a complete object identity.

| Module | Instance | CAF object identity |
|---|---:|---|
| Occupancy Mode Determination | 51131 | `8-1/575_1.524_51131` |
| ZN-T Setpoint Determination | 52062 | `8-1/575_1.523_52062` |
| Discharge Air Setpoint Determination | 69909 | `8-1/575_1.536_69909` |
| 100 OA Start Stop Sequencing | 62854 | `8-1/575_1.536_62854` |
| 100 OA Single Duct Sequencing | 62996 | `8-1/575_1.536_62996` |
| Cooling Availability Determination | 67893 | `8-1/575_1.536_67893` |
| Reheat Availaility Determination | 68046 | `8-1/575_1.536_68046` |
| Loss of Air Flow Sequencing | 68962 | `8-1/575_1.536_68962` |
| Unocc Heating Fan Lockout | 81051 | `8-1/575_1.536_81051` |
| Unocc Cooling Fan Lockout | 81052 | `8-1/575_1.536_81052` |
| PID Tuning Reset | 83123 | `8-1/575_1.536_83123` |
| Zone Sequencing v51 | 83759 | `8-1/575_1.536_83759` |
| Proportional Valve Cooling Control v51 | 83798 | `8-1/575_1.536_83798` |
| Proportional Valve Reheat Control v51 | 83810 | `8-1/575_1.536_83810` |
| DA-T Unocc Status Determination v61 | 85858 | `8-1/575_1.536_85858` |

**Source identity**

SHA-256 values record exactly which supplied files were inspected.

| File | SHA-256 |
|---|---|
| 2026F29 Reference(1).pdf | `f5a94759ff4549725b6a562870ee96b682fa944437a4ac1907c892ef58e54285` |
| AHU-Cooling Control.pml | `a09f0f50b9e6c70be34865b98435856bbb0a186d953104a1a91fde2803f096cc` |
| AHU-Econ Damper Control.pml | `240a3f6d9630297c74823d69419bcf35d54f5c94678d96f1a5ebd115a00981d6` |
| AHU-Fan Control.pml | `4e33217957887911f5886ac535de2a43572fec209ab1739f718cd4fcec6c7241` |
| AHU-Heating Control.pml | `12534fc11cb5ab9da41f0913f6eaa1e0729dfb487e24f574c26e6b6b65b7db75` |
| CCT_README(1).html | `7c5165a9061e15bdf5ff263c63d0e8cefe04e76363337928b0ad91433540062d` |
| Fan Coil-Cooling Control.pml | `c993524228191c49fb495c30ef795e8ba1c350e2cd5556a36172dd5a585c55cd` |
| Fan Coil-Heating Control.pml | `8335413050c40edf43f5c1c3c4fb43f45c7a732640eaab28aa60431cbb19cb4d` |
| HP-Cooling Control.pml | `d0ed0d6fbc870d041c796d8dd3418a7f3bc76723e9fd4fe24383d5e5b83a840d` |
| HP-Heating Control.pml | `4ace3c2c3aaa9f0f054559334aede35e07f111038b6266a55da9ebe1c24f6249` |
| Module-Logic.pml | `58e4dc70a363dba0257d53de1c6215ee61b505849f85051eb9c958488360986d` |
| Perspectives Description.docx | `5bdeda8b851812a1bdcb9ae059dcd4c2c3ad3716f1104e478dc257744c348f50` |
| Perspectives_Active_Modules.xlsx | `90424d34e673127d3f4bbecd91f01b64a2ce7d0de3fdd76a3b941f573a244c75` |
| UV-Cooling Control.pml | `2bfb5a8b7abc913fcadf6fdf56c2c977aba21cb1650f8ca6ce8651651a7f0c5c` |
| UV-Heating Control.pml | `147334f55a91c68293a8e7cb50eeda0d444e9bbce4fcd2b9e86dadc54690ea80` |
| VAVDD-CD Damper Control.pml | `c3ced3463508165d28a208b6a99674be26ad0874bb72da9a775e6bd28304da42` |
| VAVDD-HD Damper Control.pml | `8232748268082230779a1fe609fd44e9ca9fdd6d4392327bbd06c90f3c689d0b` |
| VAVSD-Damper Control.pml | `3917a97d3ce6d371887640adcd2e1ac0cfbd97c2c8784d5cbe1342039f2cfa07` |
| VAVSD-Heating Control.pml | `05da5f0f5482764e931ca87702ea5869d831cb1c226dd08e1d0b6e1a5c5ae885` |
| classCache.xml | `4064e23d5633fb3e0cbe75230359042fe30cee792210c90d515b26f77291ce6f` |
| meta.xml | `0e43d60b92d3ba2d5ead2591786dcbcd1ee838f39cb0823a8ee35cb2c1df9330` |
| release.xml | `4f67b8a795578dfeacf50161a5c7fbd37104ccd7053784e73f74a60101dbba35` |
| signals.xml | `ddab93db73dc04edd9950794d98ab04e81d97345836000d9176b0b7681a9476c` |
| cctsimmce-Generic.dll | `fa8e4fbca1788c70d43d5d9105f7025c3b347ac1b36c3c9b491a248a1b8294ce` |
| cctsimmce-IP.dll | `462973be8961af616ae421387675c9713628e709adcfb4a20358292ed2d9d941` |
| cctsimmce-MSTP.dll | `b94563f58608e2e09c0bb9b73c64f66b2e7850efb6ad1d731a7fb84fda6e625a` |

AHU comparison file SHA-256: `46b41438f157068c5546210a54f733859df617abcc2f83a2e6f99ba4afd86a64`.

Supplemental import/export instructions: `01-Johnsons-Controls-CCT-Help.pdf`, printed pages 114–115. SHA-256: `68935362c85cb1879dc033cc701115e8ea7c4ecb26748f21a9ceaf0454f82903`.

Scope: static reference and limited metadata review. DLL headers, resources and exports were inspected without loading or executing them. No CAF, PML, workbook or source document was modified. No new CCT compile, native simulation, transfer or controller validation was performed.

## Repository source locations

The 23 original non-DLL references are preserved unchanged in `../examples/cct-references/2026-10-19/`. Exact source identities and paths are in `../data/cct-reference-sources-2026-10-19.json`. DLL identities/imports/exports and the limited CAF checks are in `../data/cct-release-10.8-index.json`. Perspective/module mappings are in `../data/cct-perspective-index.json`. The three AHU comparison files are in `../experiments/review/2026-10-19/`.
