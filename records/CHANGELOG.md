# Task change log — 11 October 2026

1. Read the two user-supplied handoffs; searched for existing code, tests, figures and source papers. Connected GitHub API confirmed NSEF is empty.
2. Initialized a local `codex/subpsi-foundation` branch with origin `hibawaheed/NSEF`; no remote write. Preserved original source and hashed inputs.
3. User clarified to proceed without a protocol gate, record all work, and use freely reusable datasets with attribution. Recorded these choices; no mentor/fair approval inferred.
4. Added fixed-bin numeric/categorical PSI, explicit missing/unknown handling, positive count smoothing and separate normalization.
5. Added independent-sample exact/count-randomization tests, nonzero Monte Carlo p-values, multiplicity implementations and a p-value-resolution guard.
6. Added fixed predefined groups, two-sided support checks, retained unsupported tests and comparison methods A0/A1/B0/B1/B2.
7. Added synthetic scenarios S0–S5, independent random streams and separated data roles, a fixed logistic classifier, and labelled outcome audits excluded from detection.
8. Downloaded openly licensed Adult from UCI; recorded CC BY 4.0 attribution and original-file hashes. Added deduplication, disjoint roles, finite-pool semi-synthetic sampling and conditional inference warnings.
9. Added scientific unit/integration tests and original-code bug fixtures; test outcomes and experiment run results are recorded after execution.
10. Added figure pipeline and per-figure tables/manifests, analytical planning examples clearly separated from empirical charts.
11. Added starting-state report, explicit settings, source notes, additions/limitations tracker and AI-use log.

Further validation fixes, measured runtimes and evidence findings are appended as they occur.
12. Targeted reading of the supplied MSD paper identified overlapping prior contributions (intersectional masking, sample-size tradeoffs and computational evaluation). Flagged the novelty-framing risk to the user; no claim of superiority to MSD is made.
13. All 35 initial unit/integration tests passed; six smoke runs completed with zero failures. Original-code fixtures reproduced lost outliers, empty-reference failure, and a zero random-permutation p-value.
14. Completed 360 synthetic and 80 Adult configured runs with zero failures. Runtime recorded in manifests (~96 seconds synthetic, ~12 seconds Adult); setup/download time was much longer and is not experiment compute time.
15. First plot build exposed floating-point endpoint rounding in a Wilson interval at a 100% rate, which matplotlib rejected as a tiny negative error-bar length. Corrected bounds to include exact 0/1 endpoints and added a regression test. No experiments or estimates changed. Partial failed plot files were moved to task scratch; failure traceback remains in the validation log.
16. Added locking for concurrent validation-log appends. Main experiment settings were not retuned after viewing results.
17. Final initial study findings: S2 intersection monitoring detected all changed intersections in 60/60 runs; the calibrated aggregate comparator matched subgroup horizon detection in S1 (60/60) and Adult injection (40/40). Flagged this limit to the user rather than selecting a weaker comparator or changing settings.
18. Reported outcome-only failure and the 20% complete-stream null false-alert rate for B2 (12/60 six-window streams). These materially limit universal bias-warning and continuous-monitoring claims.
19. Generated 11 figures with source CSVs, manifests, PDF/SVG/300 dpi PNG, combined PDF and local gallery. Visual review found crowding between two legends and footnotes; increased spacing and added explicit AI-production disclosure. Added visible rate intervals to the detection-delay chart. Numerical CSVs were retained unchanged.
20. Compared every preselected smoke run with the corresponding main-run seed: all six numerical outputs reproduced exactly, excluding recorded runtime.
21. Final asset validation passed for all 11 figure manifests, source-run hashes, CSVs and 300 dpi images; the combined vector PDF contains 11 pages. The layout revision left all 11 numerical CSVs byte-identical. Requested the chart PDF open in the app.
22. Python dependencies were installed only in the task's local virtual environment; the exact versions are pinned. Slow/rejected download attempts were resolved by validating complete wheel SHA-256 hashes against public PyPI metadata before installation. No paid/cloud compute was used.
23. Packaged the local repository, saved experiment outputs, charts and logs. The original script remains preserved. No remote push or submission was performed.
