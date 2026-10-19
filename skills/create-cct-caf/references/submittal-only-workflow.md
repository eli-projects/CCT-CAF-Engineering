# Build from a hardware submittal using retained construction resources

## Goal and current coverage

Accept the hardware submittal/sequence as the user's normal input. Retrieve controller, physical-I/O and module construction resources internally. Do not require the user to upload another CAF when a retained matching asset already exists. A one-time native evidence sample becomes a reusable capability; repeated uploads are not the intended workflow.

`assets/native-library.json` is the executable inventory. Scope every capability by exact native source hash, controller model, release, topology and recipe. A retained native is construction evidence; each generated application still needs its own native CCT acceptance.

| Retained profile | Recipe coverage | Limits |
|---|---|---|
| M4-CGE09090-0, release 10.8, XPMs SA4/5/6 | Dual pump / dual HX CT CHWS partial candidate | 20 mapped native hardwired objects; 15 inputs remain SIM only. Platinum, final settings, display, calendars, BTU and integrations incomplete. |
| M4-CGM04060-0, release 10.8, no expansions | Bounded on/off exhaust fan, proof alarm, runtime/limit alarm and 0–10 V pressure monitor | Exact BI1/UI1/BO1 layout only. Native functions are not independently executed; schedule/identity and project policies need review. |
| M4-CGM09090-0, release 10.8, XPMs SA4/5 | Retained native and primitive/module construction reference | No general AHU compiler recipe. Compose a supported new recipe from the native module catalog; do not claim an arbitrary AHU is implemented. |

The small retained library is bundled with the skill and works without a repository checkout or network for these recipes. The approved engineering repository supplies the larger 520-module library and research history. Do not infer model support from similar names or change a CGM model string to CGE.

## Submittal to typed specification

1. Read the actual PDF and drawings using the PDF skill. Extract source-located atomic requirements and the full point schedule. Keep approved values separate from native defaults/provisional assumptions.
2. Create a JSON specification in scratch. Use schema `cct-caf-spec-v1`, `project.name`, `controller.model`, optional `controller.release`, explicit `controller.expansions` list, `recipe`, `sources`, `points`, `settings` and `requested_features`.
3. Use each source's actual filename/SHA-256. Retain page/drawing/paragraph locators on the corresponding requirement/point. The companion project record carries the full requirement/verification matrix; a recipe feature list is not complete sequence traceability.
4. Use `assets/native-library.json` to discover exact recipe point-role keys, fixed terminal/device/kind combinations and supported features. Point names are project inputs. Refer to [ct-chws-example-spec.json](ct-chws-example-spec.json) for the source-located CT schedule, and [single-fan-example-spec.json](single-fan-example-spec.json) for a synthetic bounded fan example. Re-read current submittal values instead of copying the example as the project specification.
5. Run `plan`. It rejects unsupported controller/release/topology/roles/features and electrical variants instead of silently fitting an unrelated application. For an intentionally partial build, keep the full requested feature list and give each unimplemented feature an explicit entry in `deferred_features` with `feature`, `reason` and requirement IDs. Deferring a function does not permit a mismatched physical terminal/topology. Omitted release selects a unique retained authoring release and records an assumption, not installed firmware compatibility.

```sh
python3 scripts/caf_from_spec.py catalog
python3 scripts/caf_from_spec.py plan /absolute/path/project-spec.json
python3 scripts/caf_from_spec.py build /absolute/path/project-spec.json /absolute/path/fresh-output
```

These commands have no source CAF argument. Resolve `scripts/` relative to this skill. Build verifies all retained native/runtime asset hashes, constructs in an isolated temporary reference tree, uses complete native patterns and patches scoped project properties. Restore original source ZIP attributes before central-directory writing; Python otherwise substitutes permissions for a zero external_attr. Record historical constructor-reference commit separately from retained-library reference commit and the factory code hash. It writes a new CAF, manifest, build result and preflight. CT builds also run 25 independent checks of the actual serialized custom logic. The fan build is static-only; no native FSM/totalizer execution is implied.

`new_CAF_upload_required=false` describes recipe input routing. `complete_submittal_implemented=false` and `PARTIAL_CANDIDATE_CCT_NOT_EXECUTED` describe the present builders' output limits. Do not substitute the routing flag for an implementation or acceptance claim. Current builders remain partial, including the fan recipe because native/project policy work is not verified.

Supported scalar settings are explicitly allowlisted in `ct_settings()` and `ef_settings()`. Preserve source signal scaling unless changed through a supported typed setting. The fan pressure input supports observed 0–10 V, scaled in inches water column; default native span 0..1 is provisional if not supplied by the submittal. Output and proof polarity remain review items. Native device/network identity is retained; any controller fields beyond model/release/expansions are reported as unapplied settings. Project identity configuration and uniqueness remain incomplete, even when the name is changed. Keep SYSTEM-EN/CONFIGURATION-READY False for CT and EF-SCHED Off for the fan; restore offline test defaults after Simulation.

## Grow missing capabilities

Treat a mismatch as a specific engineering development item, not an automatic request for a complete project CAF:

- Search bundled profiles, the approved repo, class/signal definitions and CCT Help for the exact missing construction evidence.
- Implement a supported extension using existing complete native patterns; add explicit type/topology/identity validation and a reproducible build path.
- For an unobserved format, request or produce the smallest native definition/probe that isolates it: for example adding one Platinum input, one UI dry contact, an expansion address, an alarm object or one module variant. A probe may be a saved CAF difference, definition or supported export. Ask for a complete project application only when that is the actual necessary evidence.
- Retain each useful native sample once, including original hash, model/release, complete object subtrees, expected behavior and exact acceptance evidence. Add it to the capability inventory and the relevant tests so later projects reuse it automatically.
- Never reuse a failed blank-Control specimen as an accepted shell. Preserve historical failures and withdrawn Mux model passes.

Next priorities are CAP-03 (general physical I/O/proxy/paired-registry allocation), CAP-04 (Platinum signal encoding), broader module composition/recipes, calendar/BTU/integration contracts and CAP-06 (native CCT validation). Do not label the skill a universal compiler until these paths work across representative hardware and sequences. Native examples for many models alone do not supply every signal/module behavior.

## Forward tests

Verify from an empty output directory with only a submittal-derived spec as the build input. Check source hashes, renamed points, changed settings, correct physical bindings, preserved registries/ZIP metadata, defaults off and exact generated output hash. Exercise unknown models/releases, extra points, different terminals/topology, unsupported electrical types, invalid values and duplicate names. Reject mismatches without writing a misleading CAF.

Then have an independent agent use the skill with a raw submittal and no project CAF, without giving it expected answers. Inspect its requirement extraction, routing, output artifacts and claims. Native CCT opening/compile/resources/Simulation/restart remains a separate test stage; static/model success cannot promote a generated profile or recipe to native acceptance.
