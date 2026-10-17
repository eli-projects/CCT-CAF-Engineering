# Failed CAF specimens

`AHU-1_Integrated_Sequence_CCT_TEST.caf` is retained solely for failure analysis. On October 17, 2026, the user reported that everything in its Control tab was blank. Its SHA256 is `5180b9ea0fe254d844f5385882c547afc74f165fc898f022750dd38957708a88`.

Earlier static/model checks passed; they did not establish CCT compatibility. The observational rendering audit now identifies 187 category-code discrepancies, including 166 internal primitive blocks. Causation and a repair have not been isolated in CCT.

Do not use this file as a working template or a validated construction example. See [the review](../../docs/NATIVE-MODULE-REVIEW-2026-10-17.md), [failure ledger](../../data/failed-candidates.json), and [exact audit](../../data/failed-integrated-display-audit.json).
