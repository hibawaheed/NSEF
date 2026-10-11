# Prior-work comparison and claim boundary

AI-assisted technical comparison, 11 October 2026. These are verified links to primary sources, not a completed systematic review or a student submission bibliography.

| Existing work | Overlap with this project | What this implementation actually evaluates |
|---|---|---|
| Němeček et al., Maximum Subgroup Discrepancy, KDD 2025, https://arxiv.org/html/2502.02221v2 | Intersectional masking, interpretable subgroups, sample complexity, empirical sample-size/runtime comparisons, optimization over group descriptions | Fixed low-order groups, per-feature PSI/KS, 20-batch error spending, count-triggered accumulation, known injected changes and held-out evaluation seeds |
| Dolin et al., Statistically Valid Post-Deployment Monitoring Should Be Standard for AI-Based Digital Health, https://arxiv.org/html/2506.05701v3 | Separates input change from performance deterioration; statistically valid repeated monitoring; label-efficiency and subgroup tradeoffs | An executable comparison of ordinary versus accumulated subgroup tests, and a separately scheduled labelled audit; no medical deployment or new theorem |
| Unveiling Group-Specific Distributed Concept Drift, https://arxiv.org/abs/2402.07586 | Group-specific drift and fairness questions | Centralized tabular data; no federated training, distributed detection, or attribution of changes to clients |

PSI, KS, permutation tests, Holm correction, fixed-horizon Bonferroni spending, Fisher tests and accumulating samples are existing methods. The web interface is an implementation contribution, not evidence that the statistical idea is novel. The v2 benchmark can support narrow empirical findings and quantified operating limits. It does not establish a new universal bias detector or superiority to MSD.

A head-to-head MSD implementation is not included because its reported discrepancy/search objective is not interchangeable with fixed-subgroup conditional feature PSI. Such a comparison needs an explicitly aligned target, access to the official implementation/solver and equivalent calibration. This is an outstanding comparison, not evidence that MSD is impractical.

The tested accumulation rule was chosen before v2 results: buffer each fixed group until 100 current observations, assess only if its reference also has 100, and reset that group's buffer after the test. Its contribution must be assessed through coverage, power and delay; adding this rule does not by itself prove novelty.

NSEF context checked: https://nsefpak.com/main/registration/ . The official page emphasizes experimental evidence, comparison with previous work and student ownership. ISEF judging and AI-use references are https://www.societyforscience.org/isef/grand-award/criteria/ and https://www.societyforscience.org/isef/international-rules/rules-for-all-projects/ . Competition eligibility, required paperwork and acceptance are not established by this software exercise. AI assistance must remain distinguishable from the student's own contribution.
