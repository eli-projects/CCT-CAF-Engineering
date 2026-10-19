# Project contract and deliverables

Use JSON for the machine record and concise Markdown/tables for review. Create Excel verification matrices when requested or beneficial using the spreadsheet skill. Keep output proportional; fields may live in one manifest plus a report.

## Intake record

- `project`: equipment identity and requested scope.
- `sources`: source IDs, original filenames/revisions, SHA-256 and types. Locate each requirement by source ID plus PDF page/drawing/paragraph.
- `controller`: exact controller/expansion models, known CCT/device-package versions, release, addresses and capacity; use null for unknowns.
- `baseline`: path/hash and exact controller/release/acceptance evidence, not merely the newest filename.
- `requirements`: unique ID, source locator, atomic condition/action, priority, units, thresholds/differentials/timers/reset/fault behavior, status and assumptions.
- `points`: physical/network type, terminal/address, range/units, direction, enum states/set and mapping; distinguish requests, controlled outputs and proof.
- `module_plan`: requirement IDs, exact native source hash/full ref, variant, ports/settings and necessary construction probe.
- `gaps`: ID, affected requirements, missing/conflicting fact, impact, whether hardware construction or a function is blocked, and next step.
- `decisions`: explicit user/designer decisions/source/date, separate from provisional assumptions.
- `verification`: test ID, requirements, actions, expected observable values/status/timing/reset, evidence, actual result and tested CAF hash.

Use requirement statuses `implemented_candidate`, `pending_input`, `external_integration`, `deferred`, or `not_applicable` with a reason. Candidate implementation does not mean acceptance.

## Construction-ready checks

Establish controller/release, compatible native baseline, I/O assignments needed by the change, complete templates, type/enum mappings and supported serialization. Make mode/safety priorities explicit.

When the target model/release and matching native starter are established, record an unknown installed CCT/software version as an acceptance gap rather than automatically blocking an offline candidate for that target. Do not infer a different target firmware or upgrade format from a package label. Keep hardware/serialization prerequisites distinct from tests performed after generation.

A matching retained native asset satisfies the source prerequisite; a newly uploaded CAF is not required. Missing essential construction capabilities prevent only the unsupported output. Search retained profiles/modules and definitions, finish independent work and identify the smallest missing native probe rather than requesting a full project CAF by default. Functional gaps may remain in an explicitly partial CAF when changes are independent and inactive/unimplemented functions are clear. Do not fabricate a controller, dummy CAF, terminal or module internals to appear complete.

## Delivery record

For an actual candidate provide:

1. A new CAF, preserving sources.
2. Reproducible input-hash-guarded build/patch script; source/output hashes, repository commit, versions, native identities and change scope.
3. Requirements/point/module traceability and unresolved settings/integration work.
4. Static/preflight/diff results with limits; model results and unsupported functions where applicable.
5. CCT rendering, compile/resource, Simulation, failure/priority and restart/integration test steps.

Use `CANDIDATE_CCT_NOT_EXECUTED` without native testing; `PARTIAL_CANDIDATE_CCT_NOT_EXECUTED` when functions remain unimplemented; `BLOCKED_CONSTRUCTION_INPUTS` when available native evidence cannot support any CAF generation. Keep user-reported opening, specific Simulation results, assistant models, static checks and commissioning as separate hash-scoped records.

For intake/preflight-only requests, do that stage and name its next prerequisite. Do not start live transfers or supervisory changes as part of offline CAF generation.
