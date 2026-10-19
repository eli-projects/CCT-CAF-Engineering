# Submittal-only CAF generation: retained profiles and capability growth

The user's target is to supply a hardware submittal and receive a project CAF without supplying a new CAF for every job. The installed CCT CAF Engineer skill now retains native construction resources and has a self-contained build path for bounded recipes. **This removes repeat-upload dependence for the covered cases. It does not yet implement arbitrary complete controller applications.**

The versioned skill source is under [`skills/create-cct-caf`](../../skills/create-cct-caf/). Its installed copy is saved separately to the user's Skills workspace. Do not return a skill ZIP or ask the user to recreate the installed skill.

## Retained resources

| Model / release | Native source SHA-256 | Coverage |
|---|---|---|
| M4-CGE09090-0 / 10.8 | `e896bab23c944d08b3eb3e309cd813cd66b4b7ab0b22d3c2a4476c754eef76d2` | CT CHWS dual-pump/dual-HX partial builder, XPMs SA4/5/6 |
| M4-CGM09090-0 / 10.8 | `078e1aa20f084e82212f205480f858bb17fad45a81081a74f74e4d429530bd26` | Native AHU/primitive source and XPM SA4/5 profile; no arbitrary AHU recipe |
| M4-CGM04060-0 / 10.8 | `2fb00145238b2b8348d1377017ad4d4a80cada322558ee420f9e68c68e4eab78` | Bounded on/off fan, proof alarm, runtime/limit alarm, 0–10 V pressure monitor |

The skill bundles the original native bytes, release class cache and pinned constructor/model scripts. It hash-checks these assets and stages a minimal isolated reference tree at build time. The two current recipes require no project CAF argument, repo checkout or network. The larger 520-module reference catalog remains available for extending the compiler.

Controller/profile existence, bounded recipe support and native acceptance are separate fields. Do not substitute a profile for a complete sequence. Retain source/candidate hashes and leave historical failed specimens and withdrawn Mux results unchanged.

## Workflow

1. Read the actual submittal/sequence/drawings. Extract source-located requirements and all physical/network points.
2. Match exact model, release, topology and available native signal/object formats to `assets/native-library.json`.
3. Create a fresh typed `cct-caf-spec-v1` project spec. Read the recipe's point-role/terminal/kind mapping. Supply names, confirmed scalar settings, source hashes and requested features; explicitly defer unimplemented features with reasons/requirement IDs for a partial build.
4. Run `plan` and build from retained resources. No new CAF upload is required for a matching recipe. Do not force a different hardware layout into the recipe.
5. Run preflight, object/property/binding review and supported actual-graph model cases. Prepare native CCT tests; keep those results separate.
6. Deliver the actual candidate with scope, remaining work and hash-specific evidence. Both current recipes retain `PARTIAL_CANDIDATE_CCT_NOT_EXECUTED` and `complete_submittal_implemented=false`.

```sh
python3 skills/create-cct-caf/scripts/caf_from_spec.py catalog
python3 skills/create-cct-caf/scripts/caf_from_spec.py plan /absolute/path/project-spec.json
python3 skills/create-cct-caf/scripts/caf_from_spec.py build /absolute/path/project-spec.json /absolute/path/fresh-output
python3 -m unittest discover -s skills/create-cct-caf/tests -v
```

The factory validates unique point roles/names, exact recipe bindings, topology, allowed features/settings, numeric ranges and the supported fan pressure electrical format. An unsupported model, extra point, changed terminal/kind, unaccounted feature or signal variant is reported rather than silently converted. Explicitly deferred functions stay incomplete. Unapplied controller identity/display fields are recorded; native identity remains retained and must be configured/reviewed separately. Stored CT enables remain False; the fan schedule is stored Off.

Scoped property edits preserve other native bytes and ZIP metadata. A regression during development exposed duplicate XML properties after reparsing an object fragment without its inherited default namespace. The patcher now reparses fragments under the native namespace and rejects duplicate properties; tests inspect actual values and preserved hardware/registries, not just a structural pass. Superseded scratch test builds are not accepted examples. The fresh-agent test also found Python replacing original zero ZIP external attributes with default permissions. The factory now restores original-source ZIP metadata after writing the payload and before writing the central directory; both CT and fan preservation tests cover this. Manifests distinguish historical constructor-reference commit, retained-library reference commit and factory code hash.

## Evidence and limits

- Thirteen new retained-workflow tests exercise asset integrity, model/release/profile/recipe selection, hardware/electrical/feature mismatches, explicit partial deferral, unapplied identity, invalid settings/duplicates, no-output-on-mismatch, fan reproducibility/native hardware preservation and CT naming/settings/guards.
- CT builds run the reviewed independent model against 25 groups of the actual serialized custom logic. Native sequencers, PIDs, runtime totalizers, memory scan order and hardware are not executed.
- Fan builds currently have structural/property/binding checks only. Native status/runtime alarm functions and totalization are not independently executed.
- The existing 15 reference tests remain distinct. The combined reference suite imports the 13 skill tests through `tests/test_retained_skill.py`.
- A fresh-agent forward test uses only the raw CT hardware PDF plus the skill's internal resources, not the prior generated CAF/reports. Record its artifacts/results in the companion evidence file.
- Native CCT opening, Control/Logic rendering, compile/resource checks, Simulation, restart/communications and commissioning remain unexecuted for these new factory outputs. A blank Control tab fails compatibility.

## Development priorities

| Capability | Current state | Next implementation |
|---|---|---|
| Internal controller profiles | Three retained native layouts | Retain each new exact model/release/layout once and reuse it |
| Module composition | Two bounded recipes plus 520-module external catalog | Typed reusable composition for additional supported sequences |
| Physical I/O allocator | Existing native objects can be reused; general allocation incomplete | Native AI/BI/UI/output/proxy/paired-registry creation and replacement with meaningful tests |
| Platinum RTD | Unimplemented | Establish and retain exact native 1k Platinum configuration |
| Calendar / BTU / integrations | External contracts or missing in CT recipe | Implement approved persistence, host mappings, calculations and freshness behavior |
| Native acceptance | Not executed | Hash-specific CCT opening, compilation/resources, Simulation and restart results |

For a missing capability, search retained assets/definitions/Help and implement supported extensions first. If serialization is unobserved, obtain the smallest native before/after probe or supported definition that isolates it. Retain it with constructor/tests so later jobs do not ask for it again. A large pile of controller CAFs alone is insufficient; signal formats, hardware allocation, modules, sequence composition and validation all need coverage.

The earlier per-job instruction to require a freshly supplied starter is superseded for retained compatible resources. Preserve the source requirement for genuinely unobserved formats; do not weaken evidence integrity or relabel incomplete candidates as complete.

## Completed forward-test rerun

[Evaluation evidence](../data/submittal-only-2026-10-19/evaluation.json) retains the fresh source-located project spec/record, current audits/model checks and both specimen hashes. The fresh agent generated a CAF using only the submittal as user input, without another CAF or external access. Current output SHA-256 is `35aaef73c5ca1188eb91761ac66a67cdeb309f7914887bcfa1b2ba80aacb3f7f`. The initial/current XML payloads are identical; the archive-attribute correction changes the CAF hash and restores source external_attr=0. Current preflight, observational display audit, 25 scoped custom-model groups and independent source/default/registry/ZIP audit pass. All 28 combined regressions pass. Native CCT remains unexecuted and the output remains incomplete.
