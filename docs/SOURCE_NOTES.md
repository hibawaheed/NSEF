# Factual source notes, not a submission bibliography

- Original UCI Adult dataset page: https://archive.ics.uci.edu/dataset/2/adult . Checked 11 October 2026. Lists CC BY 4.0 and the dataset citation. Actual retrieval and SHA-256 hashes are in `records/adult_dataset.json`.
- Adult citation: Becker, B. & Kohavi, R. (1996). Adult [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5XW20 . License: https://creativecommons.org/licenses/by/4.0/ . Used with deduplication, train/design/reference/audit/monitor split, and simulated weighted sampling; original records and outcomes are unchanged.
- SciPy permutation test documentation: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html . Used to verify exact and randomized permutation conventions, independent-sample assumptions, and ties.
- NumPy multivariate hypergeometric documentation: https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.multivariate_hypergeometric.html . Count sampling is without replacement from pooled histogram totals, equivalent in distribution to random sample-label allocation.
- statsmodels multiplicity implementation: https://www.statsmodels.org/stable/_modules/statsmodels/stats/multitest.html . Used as an independent implementation check for Holm, BH and BY.

Four supplied papers were located: `2502.02221v2.pdf` (Maximum Subgroup Discrepancy), `2402.07586v4.pdf` (group-specific distributed concept drift), `ocaf039.pdf` (fairness drift in model maintenance), and `applsci-14-08860.pdf` (bias literature review). First-two-page extracts were inspected for identity/context only. Exact scientific claims, differences, and novelty require reading the complete papers; this task does not assert that step is done.

Earlier statements that all commercial monitors are aggregate-only, that BH controls unrestricted false-alarm probability, or that a narrow bootstrap interval proves a real drift signal must not be reused as established facts.

## Additional targeted reading during the task

The supplied MSD paper's introduction, subgroup-distance discussion, and experimental setup sections (1.1, 4, 5.1–5.3) were also inspected. It already discusses intersectional masking, small-subgroup significance/sample-size problems, a minimum subgroup count, runtime evaluation, and alternative algorithms. It should not be dismissed as impractical solely because it uses MIO. This is targeted reading, not a full-paper review or a reproduced comparison. The defensible contribution here must be the measured behavior of this particular lightweight fixed-subgroup monitor and its limitations, rather than invention of subgroup distribution auditing.
