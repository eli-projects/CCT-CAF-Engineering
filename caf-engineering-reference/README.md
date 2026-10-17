# CCT CAF Engineering Reference (experimental)

**Purpose.** An evolving, **version-controlled reference for creating and modifying Johnson Controls CCT Controller Application Files (`.caf`)** from empirical, reproducible examples. It is intended for a coding assistant to consult at the beginning of every new session, alongside CCT Help. This is *not* an official CAF specification and does not replace CCT validation or commissioning.

## Where to start in a new chat or ChatGPT Work task

1. Read `docs/CAF-FORMAT.md`, `docs/MODULE-CATALOG.md`, `docs/VALIDATION-PROTOCOL.md` and `docs/PROJECT-AHU-1.md`.
   Also read `docs/NATIVE-MODULE-REVIEW-2026-10-17.md` and `data/failed-candidates.json`: the integrated candidate failed with a blank Control tab despite offline/model passes.
2. Load `data/observed-properties.json`, `data/observed-main-modules.json` and `data/example-manifest.json`.
3. For new programming, use **`examples/ahu-1/AHU-1_latest_AvgControlRedirect_VERIFIED-OPEN.caf`** as the latest **project** baseline, not as a universal blank template.
4. Consult the two **CCT-authored** examples and the user-tested three-average example before writing modules. Verify all IDs/refs against each target CAF; never reuse IDs blindly.
5. Make one logically isolated change. Compare it with the baseline and validate in CCT. Update this repository only after recording results.

## Reference structure

| Path | Purpose |
|---|---|
| `docs/CAF-FORMAT.md` | Observed ZIP/XML organization, references, ports, serialization, invariants |
| `docs/MODULE-CATALOG.md` | Built-in module names, evidence, and observed creation patterns |
| `docs/EXPERIMENT-LOG.md` | CCT-successes and failures, including known invalid generated files |
| `docs/PROJECT-AHU-1.md` | Current working state and open requirements for AHU-1 |
| `docs/VALIDATION-PROTOCOL.md` | Mandatory static/CCT/offline/bench testing hierarchy |
| `data/*.json` | Machine-readable catalog and example manifest |
| `data/native-modules/INDEX.md` and adjacent JSON | All 520 top-level source-library blocks with ports, defaults, enum descriptors and exact refs |
| `examples/modules/*.caf` | Four preserved native module collections; independent behavioral simulation not reported |
| `docs/NATIVE-MODULE-INTERFACES.md` | Selected AHU-relevant native interface records |
| `experiments/failed/` | Known failed integrated CAF, retained for regression investigation |
| `examples/ahu-1/*.caf` | CCT-authored, user-tested, and latest project CAF snapshots |
| `scripts/caf_inspect.py` | Read-only CAF inspection and connection lookup |
| `scripts/caf_diff.py` | Read-only semantic diff between CAF snapshots |
| `scripts/caf_module_catalog.py` | Read-only source inventory, complete module inspection and observational display-code audit |
| `scripts/research/` | Historical experimental scripts; not portable production tools |

## Evidence policy

R2 rebuilds and their regression tests require the lxml version recorded in `requirements.txt` (`python3 -m pip install -r requirements.txt`). The read-only `caf_module_catalog.py` inspector uses the Python standard library.

- **CCT created** = saved by the user in CCT; does not by itself prove simulated behavior.
- **CCT simulation PASS (reported)** = user explicitly opened and simulated the listed behavior in CCT.
- **CCT open/connections PASS (reported)** = CCT opened and user observed expected connections; not proof of complete control-sequence behavior.
- **Static checks PASS** = ZIP/XML consistency only; never sufficient to claim a valid application.
- **FAILED CCT compatibility (reported)** = the exact specimen failed rendering/opening, regardless of offline checks. Do not use it as a working baseline.
- **Hypothesis / unverified** = does not become a schema rule until tested against a CCT-authored comparison.

## Safety and sharing

These CAFs may contain project or employer-specific control information. **Check Johnson Controls/customer permissions and confidentiality requirements before uploading to any external repository, including a private GitHub repo.** Until approved, use the archive locally or an authorized organization-controlled private repository. Never place credentials, IP addresses, or live-site secrets in examples. Never transfer an experimental CAF to a live controller before independent safety/sequence review and authorized commissioning.

## Planned growth

Add each CCT-generated minimal before/after sample (new module, port, input/output, logic block, sensor, deletion, state table, etc.), record an explicit structural diff, test in CCT, then promote only validated patterns into `docs/CAF-FORMAT.md` and `docs/MODULE-CATALOG.md`.

This repository stores knowledge **in files**, not in the AI model's weights or automatic permanent memory. A future assistant/Work task must be given access to the repository and told to consult it. The repository history is the durable source of truth.

