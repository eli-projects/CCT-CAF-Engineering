# Engineering reference

Use the private repository `eli-sep/CCT-CAF-Engineering`:
https://github.com/eli-sep/CCT-CAF-Engineering

Use connected GitHub tools for reads and authorized writes. Verify source/Git blob hashes when downloading. Compare local content to the relevant remote commit. Use bundled profiles/recipes when access is unavailable. Request a specific external reference only if an essential capability is absent from both the bundle and accessible sources; continue independent work.

Retrieve the paths needed for the task rather than every repository file. If a generated index is absent locally, retrieve it at the same commit or inspect the exact verified native CAF subtree with the repository inspector. Preserve source identity and leave unknown labels unknown.

The retained runtime sources are pinned through commit `2082a82adcb2022649935d5855bfd05336f33947` on 2026-10-19. The local `assets/native-library.json` hashes define bundled source identity; use the current repo for additional evidence. Read current status. Paths below are relative to `caf-engineering-reference/`, except the repository-root AGENTS file.

| Need | Read |
|---|---|
| Retained controller profiles / recipes | Skill `assets/native-library.json`; `references/submittal-only-workflow.md`; repo retained-library documentation |
| Instructions and status | Repository-root `AGENTS.md`; `docs/WORK-HANDOFF.md` |
| Format/identity/cloning | `docs/CAF-FORMAT.md` |
| Module discovery | `docs/MODULE-CATALOG.md`; `data/module-library-manifest.json`; `data/native-modules/INDEX.md` |
| Native implementations | `examples/modules/*.caf`; inspect exact source hash/full ref |
| Definitions/limits | `docs/BUILTIN-MODULE-DEFINITIONS-2026-10-19.md`; `docs/CCT-SUPPLEMENTAL-REFERENCES-2026-10-19.md` |
| Release class/signal data | `examples/cct-references/2026-10-19/classCache.xml`, `signals.xml`, `meta.xml`, `release.xml` |
| Perspective mappings | `data/cct-perspective-index.json`; original `.pml` files in that source directory |
| Failed specimens | `data/failed-candidates.json`; `experiments/failed/` |
| R3/Mux review | `docs/AHU-1-R3-EDITED-LOGIC-REVIEW-2026-10-19.md`; `data/sequence-r3-review-status.json` |
| CIP external contract | `docs/AHU-1-SEQUENCE-R3.md`; read its erratum and integration limits |
| Acceptance hierarchy | `docs/VALIDATION-PROTOCOL.md`; `docs/EXPERIMENT-LOG.md` |

From a local `caf-engineering-reference/` directory, inspect the actual CLIs before using them:

```sh
python3 scripts/caf_inspect.py --help
python3 scripts/caf_module_catalog.py --help
python3 scripts/caf_diff.py --help
python3 -m unittest discover -s tests -v
```

The standard-library catalog inspector can inspect complete modules and audit observed display combinations. Its XML renderings are not byte-identical replacement fragments.

Use `scripts/research/verify_custom_graph.py` only for supported reviewed graphs/manifests. The old `validate_ahu_integrated_candidate.py` has incorrect Mux selection and withdrawn behavioral passes. R2 builders and `repair_reviewed_mux_maps.py` have exact project/source-hash constraints; the repair is not a generic Mux migration.

The actual CCT Help PDF and project submittals may need separate attachment. Read the particular module/version's section. Do not infer behavior from names, numeric roles or cached summaries. PMLs are views. The one-page 2026F29 reference does not supply patch fixes. Inspected DLL exports do not provide an established automation contract or proof of native simulation.
