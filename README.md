# CCT CAF Engineering Reference

A version-controlled, **experimental engineering reference** for understanding and modifying Johnson Controls Controller Configuration Tool (CCT) **Controller Application Files (`.caf`)**. Its purpose is to preserve tested CAF examples, document observed XML structures, and build a reusable catalog of module-creation patterns for future engineering work with ChatGPT.

**Status:** Reference library v0.2.0. This is an empirical research project, **not** an official Johnson Controls CAF specification or an independently certified CAF generator.

**2026-10-17:** The integrated AHU-1 attempt failed in CCT with a blank Control tab. Four native module collections are now preserved and indexed: 520 top-level blocks, 47,235 objects and 18,763 internal connections. Read [the in-depth review and failure analysis](caf-engineering-reference/docs/NATIVE-MODULE-REVIEW-2026-10-17.md) before future CAF construction. The audit found 187 display-code discrepancies in the failed file; this is a diagnosis to test, not a verified repair.

An [R2 full-sequence rebuild](caf-engineering-reference/docs/AHU-1-SEQUENCE-R2.md) now copies native graphical records and corrects those 187 fields. It has no observational display-code mismatches; **CCT rendering, resource checks and native simulation remain pending**. The earlier user-opened AHU remains the accepted opening baseline.

## Start here

The library is currently stored in [`caf-engineering-reference/`](caf-engineering-reference/).

| Resource | What it contains |
|---|---|
| [CAF XML format reference](caf-engineering-reference/docs/CAF-FORMAT.md) | Observed file structure, object references, port IDs, connections, and serialization rules |
| [CCT module catalog](caf-engineering-reference/docs/MODULE-CATALOG.md) | Known modules, creation patterns, and evidence/validation status |
| [Complete native module index](caf-engineering-reference/data/native-modules/INDEX.md) | All 520 top-level native blocks, exact refs, subtrees and detailed port catalogs |
| [Selected native interfaces](caf-engineering-reference/docs/NATIVE-MODULE-INTERFACES.md) | Detailed interfaces for AHU-relevant modules |
| [Native source CAFs](caf-engineering-reference/examples/modules/) | Four untouched user-supplied module collections |
| [Experiment log](caf-engineering-reference/docs/EXPERIMENT-LOG.md) | Successful tests, failures, and lessons learned |
| [AHU-1 project notes](caf-engineering-reference/docs/PROJECT-AHU-1.md) | Current application state and remaining work |
| [Validation protocol](caf-engineering-reference/docs/VALIDATION-PROTOCOL.md) | Static checks, CCT opening, simulation, and independent review |
| [Example manifest](caf-engineering-reference/data/example-manifest.json) | CAF filenames, SHA-256 checksums, object counts, and testing evidence |
| [CAF examples](caf-engineering-reference/examples/ahu-1/) | Six original, CCT-authored, and modified AHU-1 CAF snapshots |
| [Failed candidate ledger](caf-engineering-reference/data/failed-candidates.json) | Explicit failure status, hashes and the archived blank-Control-tab specimen |
| [Inspection and diff scripts](caf-engineering-reference/scripts/) | Read-only tools for understanding new examples |
| [Full library README](caf-engineering-reference/README.md) | Detailed instructions for future ChatGPT or Work sessions |

## Current AHU-1 starting point

[**Latest AHU-1 averaged-control redirect CAF**](caf-engineering-reference/examples/ahu-1/AHU-1_latest_AvgControlRedirect_VERIFIED-OPEN.caf) is the current **project-specific** baseline. The user reported that it opens in CCT and the connections appear correct; **complete downstream sequence behavior and field operation have not been validated**. It is *not* a universal blank CAF template.

The preceding [three-averaging-module example](caf-engineering-reference/examples/ahu-1/AHU-1_3Averages_VERIFIED.caf) was opened and simulated in CCT: 60/70/80°F averaged to 70°F, 40/50/60% RH averaged to 50%, and 700/900/1100 ppm CO₂ averaged to 900 ppm.

## Starting a new ChatGPT or Work session

1. Give the assistant access to this **private** GitHub repository and ask it to read the [full library README](caf-engineering-reference/README.md), XML format reference, module catalog, and validation protocol.
2. Have it consult the [manifest](caf-engineering-reference/data/example-manifest.json) and actual CAF examples **before** generating or changing XML. Distinguish CCT-generated, simulation-tested, and unverified examples.
3. Make one isolated modification at a time; preserve the original CAF; compare changes and verify all IDs and port references.
4. Open and simulate each generated CAF in CCT. Record observed results, failures, checksums, and new schema findings in this repository.

The repository is the durable source of reference information. ChatGPT does **not** permanently learn the file format from a session; future sessions must retrieve the latest repository content.

## Safety and confidentiality

CAF files can contain proprietary or customer-specific controls information. Maintain appropriate authorization and restricted access. **Do not download experimental CAFs to operating field controllers** without authorized engineering review, safety checks, and commissioning. ZIP/XML integrity or successful CCT simulation does not by itself establish safe operation.

