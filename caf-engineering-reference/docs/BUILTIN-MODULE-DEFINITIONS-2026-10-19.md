# Where the built-in CCT modules are defined

The supplied files define different parts of a module. Use their evidence together when creating a CAF.

| Source | What is defined | Construction use and limit |
|---|---|---|
| `classCache.xml` | 132 object classes and 2,489 direct property declarations, superclass relationships, typed defaults, ranges, enum-set references, structured fields, views and commands | Primary supplied class/interface definition. It is not source code for control algorithms or a complete CAF-generation specification. Many labels depend on translations. |
| CCT Help | Module purpose, inputs/outputs, states, priorities, settings and failure/reliability behavior | Functional definition; check the particular module/version. The Help does not publish the complete serialized CAF format. |
| Four native module CAF collections | Actual object hierarchies, port descriptors, order, diagram records and internal logic/wiring for the saved standard-module variants | Empirical construction examples. The existing index covers 520 top-level blocks. Preserve complete source subtrees, identify each by CAF hash plus full ref and review project settings. |
| `signals.xml` | 59 signal definitions for 15 classes, sensor/control-point port classes, type/coupling settings and optional property defaults | I/O construction metadata; application wiring and terminal suitability still require separate checks. |
| PML files and active-module workbook | Saved views and lists of module/point identifiers | Module discovery and review organization. They contain no executable control-block wiring. |
| Simulator DLLs | Compiled Field Controller Simulator components and exported entry points | Static component inspection establishes identity and interfaces by name. Calling conventions/startup contracts and per-module compiled behavior were not established or executed here. |
| `meta.xml` and `release.xml` | Release-mode/package/database/ACS/DMCS settings | Tie the references to 10.8 / Firmware 12.0. This label does not prove installed CCT version or live-controller firmware. |

## Three concrete module examples

**Mux, class 562.** The cache declares selection property 2381 as a list of unsignedShort and default-input property 3122 as unsignedShort, range 0–1000, cache default 1. Input-count property 2380 is range 2–1000, default 2. These declarations validate data shape and selected ranges. They do not explain selection-table indexing. The saved native two-input Mux 265243 and the Help mode/default behavior support the reviewed 1-based data-input interpretation; see [the full R3 review](AHU-1-R3-EDITED-LOGIC-REVIEW-2026-10-19.md). Both the original inverted map and the correction pass these limited metadata checks.

**Occupancy Mode Determination, class 524 in the AHU.** Property 3110 uses enum set 649, and effective-occupancy output 50032 uses set 345. Preserve those distinct interfaces. The Help describes bypass/priority behavior; the CAF supplies this instance's configured timeout and wiring. A 0/1 request is not itself an effective occupancy state.

**Activity, class 536.** This class defines the container/interface for many different standard and custom modules. It does not identify a unique control function. Different Activities use different ports, nested blocks, FSM/PID objects, diagram records and role/setup values. The detailed implementation for a composite module must come from its saved CAF subtree. Class 536 and a module name alone are insufficient to construct it.

## Findings now checked

- All superclass chains in the supplied cache are complete and acyclic.
- Every class and class version used by the 3,411 objects / 49 distinct classes in each reviewed AHU CAF is present in the cache.
- The AHU root release string 10.8 and ACS/DMCS values 68/65 agree with the supplied release metadata.
- All 83 Mux objects in each reviewed CAF pass the limited stored-field checks for 2381 element types and 3122 type/range. This does not establish correct selection or control behavior.
- All 623 workbook ID references match the corresponding perspective widgets. The focused AHU filters omit the custom activity IDs; use Module-Logic for the broader module view and leave Freeze Selection unchecked.
- Each simulator binary is a native 32-bit Windows DLL with resource version 6.0.0.84; all three expose the same 251 names. No DLL was loaded or executed.

The class cache now reduces guesswork about valid classes and properties. Full construction still requires the class/interface definition, a matching complete native CAF example, documented behavior and native CCT acceptance.

## Reference files

- [Original supplied reference files and hashes](../data/cct-reference-sources-2026-10-19.json)
- [Class/property type index, signal mappings and simulator identities](../data/cct-release-10.8-index.json)
- [Perspective/widget/module index](../data/cct-perspective-index.json)
- [Detailed supplemental review](CCT-SUPPLEMENTAL-REFERENCES-2026-10-19.md)
- [Complete existing native module index](../data/native-modules/INDEX.md)

The source PDFs used for behavior review remain the user-supplied Controller Tool Help and AHU submittal identified in the review. The one-page 2026F29 reference points to a Flash Sheet; it does not supply the actual patch fixes, and no patch behavior is inferred from it.

## Repository verification

All 15 regression tests pass, including exact candidate reproduction, rejection of a wrong input file, preservation of every non-Mux field, eight zone-request combinations, the native two-input selection record and 28 corrected-model scenario groups. All 23 preserved non-DLL reference hashes match. [Recorded verification](../data/reference-review-2026-10-19.json) keeps these checks separate from pending native CCT acceptance.
