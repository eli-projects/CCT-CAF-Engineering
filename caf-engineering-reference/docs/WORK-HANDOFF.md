# How to continue this CAF research in a new chat or ChatGPT Work

Use ChatGPT Work for longer research/repository tasks, if enabled in your account. Have Work access the repository with its browser or connected GitHub; do not assume this conversation's temporary filesystem or full reasoning automatically follows you. A new regular chat also works if its files/repository are attached or accessible.

**Suggested opening message:**

> We're developing an empirical Johnson Controls CCT CAF XML reference. Read the repository README, docs/CAF-FORMAT.md, docs/MODULE-CATALOG.md, docs/EXPERIMENT-LOG.md, docs/VALIDATION-PROTOCOL.md and data/example-manifest.json. Treat `examples/ahu-1/AHU-1_latest_AvgControlRedirect_VERIFIED-OPEN.caf` as the latest AHU-1 candidate. Use the CCT-authored two- and three-input CAF templates as structural references. Never infer that ZIP/XML validation implies CCT compatibility. For each change, generate a new offline CAF, report object/property/connection diffs, and wait for CCT simulation feedback before promoting an XML pattern as validated. Update the docs after every test.

**Update cycle:** CCT generates an isolated before/after sample → assistant diffs it → `MODULE-CATALOG.md` and `CAF-FORMAT.md` get a versioned evidence entry → static checks → user tests CCT → record result in `EXPERIMENT-LOG.md` and manifest → commit to approved repository. Preserve failed specimens locally or in an approved restricted location for comparison.

**Critical caution:** Always comply with employer/customer licensing and confidentiality rules before externally sharing CCT CAF files or CCT-derived proprietary information. A private GitHub repository is not automatically organization-approved.
