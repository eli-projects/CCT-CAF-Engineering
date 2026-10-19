---
name: create-cct-caf
description: Build, modify, and review Johnson Controls CCT CAF candidates from hardware submittals and sequences. Use for creating CAFs from scratch, programming controllers, selecting modules or verifying logic. Start from retained controller/module assets so supported projects need no new CAF upload; extract typed requirements and I/O, construct with supported native patterns, test and retain new capabilities. Keep incomplete hardware/functions and native CCT acceptance explicit.
---

# CCT CAF Engineer

Treat a hardware-submittal-only request as the normal creation workflow. Use retained controller, I/O and module resources internally; do not make a new project CAF upload a routine prerequisite. Produce a traceable offline candidate, extend supported construction capabilities and keep incomplete functions explicit. Use the existing assistant and tools; do not imply a separate trained model or native CCT runtime.

Read [references/submittal-only-workflow.md](references/submittal-only-workflow.md) for the retained inventory, typed project specification, offline build commands and capability-development loop. Current bundled coverage is three native controller profiles and two bounded recipes; this is not yet an arbitrary-controller/full-sequence compiler.

## 1. Load the engineering reference

Read `assets/native-library.json` and [references/repository-guide.md](references/repository-guide.md). Match the hardware against retained profiles before requesting any new native input. Use the bundled resources directly for their supported recipes. Retrieve the approved engineering repository for additional modules/status through its GitHub connection or a verified checkout. Record the reference/skill commits and obey applicable `AGENTS.md`. A repository-access failure does not erase bundled capabilities.

Use the bundled inventory, pinned runtime and [references/construction-rules.md](references/construction-rules.md) for unchanged bundled recipes. Before creating or modifying construction logic, read the current handoff, CAF format, module catalog, built-in-definition guide and validation protocol from the approved repo. Load detailed source modules and the matching CCT Help sections as needed. If repository access is unavailable, continue supported bundled builds and record that external status was not refreshed; do not invent unsupported extensions.

Treat the supplied 10.8 / Firmware 12.0 references as release-specific evidence. Verify installed CCT/device-package versions and the actual controller model separately. Do not treat a release label, numeric role or module name as proof of compatibility across hardware/releases.

## 2. Extract the submittal into requirements

Use the applicable PDF/document/spreadsheet skill to read the actual supplied files. Inspect drawings and terminal schedules visually where extraction omits relationships. Verify ambiguous numeric values, degree symbols, differentials and timing units against the page image before encoding settings. Record filenames, SHA-256, revisions, PDF pages, drawing/sheet numbers and sequence paragraphs.

Follow [references/project-contract.md](references/project-contract.md) to record:

- Equipment and controller/expansion models, I/O capacities, terminals, signal types, units, ranges and bus addresses.
- Atomic conditions/actions, mode priorities, thresholds, hysteresis, timers, reset/restart rules, fault/reliability behavior and commanded outputs.
- Occupancy, operator requests, displays, alarms/trends, supervisory handshakes and external equipment interfaces.
- Conflicts, omissions, provisional settings and constraints that prevent implementation.

Use the approved sequence for control intent and wiring/controller schedules for physical assignments. Record conflicts rather than silently resolving them from a familiar template. Separate explicit user decisions from assumptions and source requirements. Do not assume fail-closed behavior: trace the specified failure response and native protection priorities.

Ask only for missing facts that materially affect the next implementation. Continue independent intake, module selection and test planning while awaiting an answer. Do not request a second authorization for work already requested.

## 3. Select the native baseline and module plan

Select a matching retained controller profile by actual model, release, topology and I/O evidence. Reuse its native asset automatically; a CAF already retained in this skill/repo satisfies the native-source prerequisite. Preserve its original bytes/hash and distinguish source evidence from generated-candidate acceptance.

For a supported recipe, extract a fresh project spec from the submittal and run `scripts/caf_from_spec.py plan SPEC.json`, then `build SPEC.json FRESH_OUTPUT`. These commands require no uploaded source CAF or external checkout. Use the point-role/setting/feature inventory to detect unimplemented work; do not force a different sequence into a bounded recipe.

For an unsupported model, hardware format or control function, first search retained assets, the approved native-module library and supplied definitions/Help. Implement supported extensions and continue independent work. Record a narrow missing capability and obtain the smallest native construction probe only where evidence is genuinely unavailable. Retain it once for future use rather than requiring the user to build/upload every new project. Do not replace one controller model with a different model string or fabricate undocumented formats.

Distinguish isolated accepted examples from newer files with known defects. Consult the failure ledger/current review status. Do not use the blank-Control-tab specimen, historical R2/original R3 Mux maps, or an old model pass as an accepted construction baseline.

Map implementable requirements to exact native source CAF hashes/full refs, variants, ports, typed defaults, settings and tests. Inspect complete subtrees: nested Activities, PIDs/FSMs, ports, enums, diagram metadata and external references. Use class definitions for interfaces/constraints, CCT Help for behavior and the CAF for saved implementation.

Class 536 is an Activity container, not a unique algorithm. If a variant or serialization is unsupported, record the gap and create an isolated native probe where feasible. Do not invent a schema. Implement independent supported requirements; enumerate a partial candidate's missing behavior.

## 4. Construct the candidate

Create a new project-specific output filename. Keep retained sources untouched. Use or write a reproducible hash-guarded compiler/recipe driven by the extracted project spec. Parameterize supported names, bindings/settings and module composition explicitly. Never silently ignore additional points, different terminals/topology, electrical formats, requested features or network identity. Adapt complete supported native patterns; do not call a bounded project recipe a universal generator.

Preserve complete native subtrees and unknown metadata. Allocate unique full refs, remap internal references, retain port order/enums and update connection and graphical records together. Preserve ZIP metadata/members. Prefer scoped byte-preserving edits over broad reserialization.

Apply the detailed construction rules, especially Mux numbering/defaults, Boolean versus enum ports, hardware-registry pairing, graphical categories and timer non-persistence. Preserve user layouts/unrelated settings. Arrange new logic in small named Activities, inputs left and outputs right; verify final rendering/readability in CCT separately.

Implement only documented external mappings. A request does not operate or prove another controller's equipment. A timer/restart option does not establish durable process history. Expose integration contracts and defaults without presenting unfinished persistence/communications logic as completed functionality.

## 5. Verify with distinct evidence levels

Run the bundled read-only preflight, resolving `scripts/` relative to this skill directory:

```sh
python3 scripts/caf_preflight.py /absolute/path/candidate.caf --class-cache /absolute/path/classCache.xml --report /absolute/path/preflight.json
```

The preflight checks only its reported structural subset. It cannot approve control behavior, rendering, memory, hardware bindings or deployment. Both the known inverted-Mux specimen and its correction can pass structural checks.

Also run applicable repository inspectors/diff, observational display audit and regression tests. Verify ports, enum sets, native settings, unexpected differences, hardware mappings and publication. Do not infer a general schema from one file. Run repository-required tests after changing its inspection logic/reference data.

Derive independent cases from requirements: boundaries, hysteresis, any/all requests, override priority, bad quality, missing proof, native safety protection, timer reset/expiry and restart/communications. Exercise actual serialized logic with the reviewed model only where supported. Keep expected results independent of the implementation; mark unsupported native functions as not executed.

Prepare CCT opening/rendering, compile/resource, Simulation and controller/supervisor restart tests. Specify observable points, actions, expected values/status/timing, reset and pass/fail criteria. An empty Control view fails compatibility. Class-cache passes, DLL exports and independent models do not establish native CCT execution. Tie user feedback to the exact tested CAF hash.

## 6. Deliver and retain provenance

Deliver the CAF when construction is supported, source/output-hash manifest, requirement/point/module traceability, concise change/gap report and CCT test steps. Use `CANDIDATE_CCT_NOT_EXECUTED` when native testing has not occurred. Do not imply full sequence or field acceptance.

When a critical capability is missing, deliver the completed independent work and a precise capability gap/probe specification. Search the retained library before asking for a file. Do not produce a placeholder `.caf`, present an unchanged unrelated application as the requested program, or claim full generation from a profile/plan alone. Distinguish this from an actual partial CAF with enumerated missing behavior.

Save user-facing deliverables through the environment's artifact persistence workflow, except files already backed by an external Git project. Update an approved project repo when authorized. Preserve original/failed specimens, hashes, evidence, decisions and handoff. Do not transfer to live equipment as part of CAF generation.

## 7. Retain and expand construction capability

Use the capability inventory in `assets/native-library.json` to turn each unsupported format into a bounded development item. Add native evidence, a reusable constructor/recipe, typed validation and meaningful regression cases. Keep schemas, signal definitions, hardware/proxy/registry allocation, control-module composition and native validation as distinct coverage. After substantial skill changes, forward-test with a raw submittal and no project CAF.

Persist approved reference changes and this installed skill through their Git repositories. Preserve the native-source hashes, skill/repo revisions, test results and unresolved capability list. Do not mark a capability native-accepted until a hash-specific CCT result exists.
