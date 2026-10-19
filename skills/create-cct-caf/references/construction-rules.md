# Native construction rules

Scope these observations to the repository's files and release, not a universal CAF specification.

## Preserve identity and structure

- Identify templates by complete source SHA-256 plus full object ref. A reused ref can mean different functions in different files.
- Copy complete hierarchies, not just Activity records/input lists. Preserve nested blocks, ports, enums, order, role/setup values, display records and unknown fields.
- Allocate/inspect full refs after cloning, including payloads, exported ports, graphs and cross-module references.
- Preserve native port order. Three-input Average Activities can export `7000,7001,8000,7002`; do not sort them.
- Preserve archive members, names, ZIP metadata/comments and source bytes.

## Graphs and hardware

| Property | Observed role / rule |
|---|---|
| 3375 | Ordered local BACoid block list; resolve within its diagram |
| 3117 / 3383 | Display order / positions; match block-list length |
| 3118 / 3384 | Four-field connections / parallel graphical records |
| 3184 | Available/exported ports; retain native order |
| 3926 / 3927 | Paired hardware registry entries/references in the reviewed application |

Preserve position-record category and shape. Do not assign one category to all primitives or derive rendering categories from class metadata alone. Use native class/role/context observations and CCT checks.

Some one-block Activities omit both 3118/3384. Preserve that observation. A lone missing counterpart or inconsistent existing array requires investigation.

Preserve registry pairing by complete proxy identity. Native files can retain inactive references without live objects; do not delete every apparently dangling row or invent GUIDs. Check actual I/O, expansion devices and bus addresses against the project separately.

## Types and Mux behavior

- Observed float inputs/outputs use classes 526/527, enum 528/529 and Boolean 530/531. Distinguish nested port descriptors from application I/O.
- A 0/1 enum is not a Boolean. Preserve set ID, state count, labels, typed defaults and translations; check both ends before wiring.
- Mux class 562 table 2381 stores data-input numbers: 1 selects Input 1 (7000), 2 selects Input 2 (7001); zero invokes Default Input 3122. Resolve omitted defaults from the matching class definition, not an assumed zero.
- A Boolean selector with Input 1=False/Inactive and Input 2=True/Active uses `[1,2]` in the reviewed examples. Do not globally rewrite native tables: different input orders/defaults can be intentional.
- Check each selector's truth table, fallback and mode/selected-input reliability. Both inverted and correct maps can pass type/range checks.
- In native occupancy class 524, request input 3110 uses enum set 649 and effective output 50032 uses set 345. An Active request is not effective Bypass or fan permission; schedule/override priority still applies.

## Application behavior

Trace shutdown, safety-valve and emergency priorities from the approved sequence/native module. Do not replace protection with a generic all-outputs-off rule. Test bad-quality proof/commands and unavailable inputs.

Do not treat a Timer's executing-state memory, network-input restart option or history sample as durable process-state storage. Define retained state, completion events, release-time/runtime rules, startup freshness, clock quality, communications and external proof. Record unfinished supervisory work.

Separate template defaults from approved project settings: temperature limits, valve direction, fan speed, addresses and OA proportions are project-specific. Warmup/Cooldown names do not establish AHU suitability or missing entry/exit targets.

Preserve user layouts when editing. Inspect custom Activities through Module-Logic with Freeze Selection unchecked; focused fixed-ID views can hide them.
