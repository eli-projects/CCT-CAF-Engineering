# Observed CCT CAF XML organization (research notes v0.1)

**Scope:** empirical findings from the AHU-1 CCT files in this repository. Not official Johnson Controls XML documentation. Terms like "must" below mean a check required by our current observed model, not a proven universal CCT constraint. Evidence is `data/example-manifest.json` plus `docs/EXPERIMENT-LOG.md`.

## Archive container

- A tested AHU-1 `.caf` is a ZIP archive with **one XML member**, named `AHU-1_Average_3Inputs_CCT.caf.xml` in the latest examples. Don't assume other CCT releases use identical archive structures.
- Main namespace for observed object elements: `http://johnsoncontrols.com/MetasysIII/2002/3/Core`.
- Direct child `<object>` elements have `ref`, `classid`, and other attributes. The **complete `ref`** is the important identifier. Numeric IDs alone can recur across scopes/classes.
- An observed object reference example: `8-1/575_1.536_86471` (root application diagram plus the `AVG-ZN-T` Activity). An internal Average block: `8-1/575_1.536_86471.561_265195`.
- Key property values are represented as `<property id="...">` containing a `<data>` child, with typed nodes (`<array>`, `<listof>`, `<struct>`, `<BACoid>`, `<unsignedShort>`, `<string>`, etc.).

## Main application diagram

Diagram root: `8-1/575_1`, class `575`. The following IDs have been *observed*:

| Property | Our working interpretation | Checked invariant |
|---|---|---|
| `3375` | BACoid block references | Same number of elements as `3117` and `3383` |
| `3117` | block indices/display order | Indices collectively match the diagram's block indices |
| `3383` | block locations | One position per block |
| `3118` | connections | One four-value struct per connection |
| `3384` | connection metadata | One entry per connection |
| `3184` | Activity and calculation ports, when present | Preserve CCT-produced order; port numbers not sorted by convention |
| `2390` | module/point display label, if present | Not every module is named in its object |

The observed connection struct means `[source_block_index, source_port_ID, destination_block_index, destination_port_ID]`. **Indices depend on the current target diagram**: `105` refers to `AVG-ZN-T` only in this AHU-1 snapshot, not in all CAF files. The observed outgoing float port for these points and Activities is `8000`; averaging Activity input IDs in this example are `7000`, `7001`, and `7002`.

Use a byte-preserving patch for changes to known connection records. The successful edit of six temperature/humidity control edges changed exactly six wire records and no other objects. Never assume reserializing the entire XML is harmless.

## Native three-input AVG-ZN-T Activity (CCT-authored)

The authoritative before/after comparison is:

- `examples/ahu-1/AHU-1_CCT_AVG_2Inputs.caf`
- `examples/ahu-1/AHU-1_CCT_AVG_3Inputs.caf`

The user followed two required CCT GUI operations: **Average block Details > I/O Modifications > add Float input**, then **Clone Ports** to create the matching Float Activity Input. Comparing files shows:

- Two additional object records (class 526) for the internal Average input and the Activity-level input.
- Activity ref `8-1/575_1.536_86471`; calculation ref `...561_265195`.
- Input 3 internal object ref `...561_265195.2_300179`.
- Activity Input 3 ref `...536_86471.2_300181`.
- Activity block + calc port list `3184` **order is not numerically sorted**: Activity `7000, 7001, 8000, 7002`; inner Average `7000, 7001, 85, 7002`.
- CCT edited Activity props `3117`, `3118`, `3184`, `3375`, `3383`, `3384`, and `3373`; inner calculation props `3184` and `2390`; and provided additional point properties including `117`, `661`, `3113`, `3365`, `3670`, `75`, `32527`, `3807` as applicable. **Do not omit these just because a port seems to render in an XML inspection.**
- Other CCT-save differences include save metadata `3632` and the override time `3113` changing back to 3600 sec; these are **not** established requirements for cloning a port.

The prior hand-generated third port used different metadata and ordering and **failed to open** (internal tool error). The data does not isolate the single cause; the safe template is the CCT-generated result.

## Cloning a complete native three-input averaging Activity

Starting from the tested three-input temperature Activity and preserving its full internal object subtree, we successfully created **two new Activity copies**: `AVG-ZN-H` and `AVG-ZN-CO2`. The user opened the resulting CAF and simulated 40/50/60% RH -> 50% RH and 700/900/1100 ppm -> 900 ppm. **This is validated only for the observed class/structure and project/release.**

The observed clone procedure:

1. Copy the full **ten-object Activity subtree**, not just the visible Activity object.
2. Assign new unique Activity IDs, calculation IDs, nested point IDs and object `ref`s; inspect **all** references in the copied bytes, not just display names.
3. Update the Activity label via property `2390` (`AVG-ZN-H`, `AVG-ZN-CO2`).
4. Add a new Activity block to main `3375`, index/order `3117`, and position list `3383`.
5. Add three main diagram wires to corresponding sensor signals and **three matching `3384` metadata records**.
6. Check every cloned block's local BACoid points to actual unique objects; verify XML + ZIP, then **open/simulate** in CCT.

Observed in the source target: `AVG-ZN-T` block index 105; cloned `AVG-ZN-H` index 106; cloned `AVG-ZN-CO2` index 107. These are examples, not constants. Source sensor indices by project: humidity `86,90,94`; CO2 `85,89,93` (each uses output port `8000`). All three Average Activity destination ports are `7000,7001,7002`.

A historical script implementing this specific transformation is in `scripts/research/create_ahu_humidity_co2_average_clones.py`. It has absolute paths and assertions tailored to the AHU-1 snapshots; it is research evidence, **not** a general-purpose generator.

## Rewiring existing control consumers

The user opened the latest `AHU-1_latest_AvgControlRedirect_VERIFIED-OPEN.caf` and reported it appears to work. Only six existing outgoing main-diagram wires were changed from original `ZN-T` and `ZN-H` to new average output blocks. No original sensor objects were removed. The six changes are recorded in `docs/PROJECT-AHU-1.md`.

## Open research questions / limitations

- General algorithm to allocate unique IDs and position new modules for *any* CAF, CCT release, and hardware package; IDs from an example cannot be copied blindly.
- CCT validation of deletions, equipment definitions, SA Bus address reassignment, and full parent/child removal.
- Differences between built-in state generation modules, mathematical Activities, and other classes beyond the averaging Activity.
- Logic-block library class IDs, port data types, ENUM details, property `3670` and `3807` semantics, diagram rendering invariants, and reliability/fault handling.
- Some analysis originally **mistook an internal Boolean block's numeric ID** as proof of a ZN-T temperature input inside `Unit Enable Determination`. That is **not confirmed**. Do not encode this supposed dependency as a fact or automate a redirect from that claim.

A mechanical ZIP/XML pass **never proves that CCT accepts the file**. Use the experimental log and validation hierarchy.

## 2026-10-17 native-library evidence and rendering failure

Four new source collections contain 47,235 objects and 520 top-level blocks. Consult `data/module-library-manifest.json`, `data/native-modules/INDEX.md` and `docs/NATIVE-MODULE-REVIEW-2026-10-17.md` for exact references, detailed port/configuration data and evidence limits.

- Property `3383` includes a category code as well as coordinates. Code values differ by class, role and diagram context. The failed integrated CAF assigned code 10 to 166 internal blocks where the native observations use other codes: Boolean/reliability 2, comparison 4, timer 15, math 8/14, with 65535 also appearing in native records. Copy the matching native record, not a global replacement code. The failure audit additionally found 21 discrepancies in main-diagram point/proxy records.
- A CAF's source hash is part of its namespace for cross-file analysis. The same full object ref appears in different libraries with different functions. Do not match functions by numeric instance or full ref alone across files.
- Three one-block native Activities omit both connection properties `3118` and `3384`. Preserve this observed representation; it is not automatically malformed. When one exists without its counterpart or existing connections have mismatched metadata, investigate.
- The four main library diagrams have no connections. Their internal module connections provide serialization evidence, not a complete application wiring example.
- The integrated specimen is now **FAILED CCT compatibility** following the user's blank-Control-tab report. The category mismatches are demonstrated; the causal fix is still unverified. Offline/model passes cannot promote its construction method.

