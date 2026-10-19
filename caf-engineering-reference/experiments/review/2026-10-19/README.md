# R3 review specimens — October 19, 2026

These are preserved experimental CAFs, not commissioned controller applications. Read [the complete review](../../../docs/AHU-1-R3-EDITED-LOGIC-REVIEW-2026-10-19.md) and [the status/hashes](../../../data/sequence-r3-review-status.json).

- Original R3: retained to reproduce the user's saved-file differences; its earlier model used an incorrect Mux interpretation.
- Edited R3: exact user-uploaded bytes, renamed without `(1)`; user reports CCT layout editing and Simulation, with no detailed behavioral acceptance supplied.
- Mux correction: changes only selection maps and defaults on 36 custom Muxs. Layouts, wire records and all other saved fields are preserved. It requires its own CCT opening/compile/resource/simulation checks.

Both historical generated candidates and the edited specimen contain the reviewed selection defect. The corrected file has not been accepted in native CCT or on equipment.
