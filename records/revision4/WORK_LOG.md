# Revision 4 AI-use and change log

Actual work date: **11 October 2026 UTC / Asia–Karachi**. This log was written after the listed actions; precise recorded timestamps are in the JSON manifests and command receipts. No entries are backdated to the planned October 12–17 work period. The current request explicitly adopts the full Revision 4 TXT as its specification. Earlier approvals are not treated as approval of this new protocol.

## Inspection and preservation

Read the requested TXT in full and inspected the current branches, HEAD, clean worktree, relevant v3/correction code, configs, logs, manifests, tests and literature notes. Verified remote branch heads with the read-only GitHub connector. Main and Version 2 remain `646bfea`; published Version 3 remains `2728857`. The latest **local** correction branch was `7ddcc02c4bf458b68617bbd5b1f184cbfb82e1c5`; created `codex/subpsi-r4-calibrated-collection` there, retaining the correction branch. Baseline: 89 tests passed. No student work was reset, cleaned or overwritten.

The prior correction already contained the historical 0/1/2+ attempt rule, training-majority baseline and complete 1,820-stream matched V2 extension. These were not relabelled as newly invented R4 work. Verified the 1,990-file prior freeze. Captured an inventory of all 4,997 tracked starting files and checked that every one remains unchanged. Old replay code and all v1/v2/v3 outputs remain byte-identical.

## New code and checks

- Added `src/subpsi/revision4.py` and 28 additional test cases. The first 26 new cases passed; two lineage cases were then added. The final full run passed **117 tests in 1.42 seconds**.
- Representation audit detects nonconstant collapse, separates constant/no-observed-value statuses, records occupied/effective bins, largest share and missing counts. Existing corrected count-bin behavior is reused, not altered.
- Added balanced accuracy with separate class denominators and the existing minimum-20 reporting rule. Recomputed 288 descriptive group/complement/period/metric rows from saved OULAD counts; consistency assertions tie correct predictions to the same confusion counts. No refitting or new label-driven baseline choice.
- Implemented an immutable per-group target plan and metadata-only collector, separate reference gate, whole-batch overshoot, duplicate-draw protection, fixed horizon and common PSI/KS boundaries. Constant-map fixture results reproduce the earlier engine. Feature/label perturbation tests leave scheduling unchanged.
- Implemented symmetric selection lookup from selection-stage summaries, explicit fallback/unmet flags, a global baseline using the same calibration cells, pointwise Wilson lower bounds and validation-stage rejection. This lookup has only been exercised on fixed test fixtures; no empirical targets exist.
- Added private role and whole-record draw-lineage validation. Repeated source use is counted; altered features/outcomes fail checks. Draw IDs can be unique while source people repeat, and documentation makes that distinction explicit.
- Re-ran the existing correction verifier into a new R4 record: three fixed V2 stream replays plus the OULAD correction replay passed; 1,885 artifact hashes and all ten previous plotted source tables were verified. This is reproduction of existing evidence, not a new campaign.

## Historical support and reporting work actually run

Ran `inspect_preparation.py` twice in different output directories. The first produced support, representation and saved-outcome arithmetic. The second added counts above/below the proposed age-60 cut. Both outputs and source snapshots are retained. No sensitivity, effect-distance or p-value calibration was performed. The shared loader reads the verified source files for schema/role checks, but evaluation feature values are not input to target selection. The future calibration runner must be restricted to the historical role.

The reserved 2015 calibration role contains 7,868 household representatives: 3,924 selection and 3,944 validation under the proposed fixed hash. Fifteen of thirty views meet the proposed per-stage support/stratum rule. Record-only role checks found no household/student role conflicts. Private lineage stays under ignored `data/raw/revision4/`; only hashes/counts are exported. Counts were inspected for feasibility; these records are not described as wholly unseen.

Ran six deterministic array timing fixtures to estimate software cost, not statistical power: easy cases about 0.0005–0.0008 seconds; full-permutation cases about 0.021–0.023 seconds per matched feature block. Saved actual values and purpose in `fixture_cost_check.json`.

Exported and visually inspected two OULAD figures from saved results, with exact CSV, 300 dpi PNG and vector PDF/SVG. No cropping, overlapping labels or misleading truncated rate axes were observed. Figure 1 shows the same 372 historical records before/after representation. Figure 2 shows the later frozen-model/constant-baseline metrics and denominators. The source-table verifier passed: **29 new artifact hashes, two figure CSVs and 288 outcome rows**. An illustrative calibration chart was not fabricated.

Inspected primary-source PSI inference and independent test-design selection papers, official Monte Carlo power documentation, and one clearly labelled abstract-only lead. Reread the earlier four-paper/windowing notes. Wrote the contribution boundary: no established new algorithm or PSI superiority. The new primary-source reading is selected sections, not a claim of an exhaustive literature review.

## Records, limitations and next boundary

Saved one proposed protocol and machine-readable settings; both new calibration and evaluation authorization fields are **false**. Approval record has no user approval yet and no mentor/fair/SRC evidence. Assistant-proposed settings remain proposals, not invented student choices. New sensitivity/evaluation runners and their experimental exports remain to be completed after approval. No final project version is selected.

Large terminal reads were occasionally truncated; targeted reads and executable checks supplied the relevant evidence. One inspection command used the wrong path for `role_checks.json` and returned “No such file”; the actual file is under the preparation result directory and was checked there. No failed scientific run, altered result or discarded adverse comparison was hidden by these inspection issues.

The new October 18 freeze supersedes the old plan's October 20 date. The bounded OULAD/V2 correction was already finished before October 14. There is no current schedule conflict. No push, merge, deployment, purchase or submission was performed. No assistant-created mentor statement, student understanding, signature, authorship claim or final submission prose was added.

The assistant performed the inspection, implementation, tests, arithmetic, plotting, source checks and technical drafting listed here. The user supplied the task and constraints. No additional student or mentor contribution is inferred. The final local preparation commit records the completed checkpoint; it does not freeze a final scientific-results set.

Final formatting check flagged CSV CRLF and normal matplotlib SVG line whitespace. The new claim-ledger CSV was normalized to LF. Already hashed scientific SVG exports were preserved exactly; code and documentation whitespace checks exclude those generated vectors. No figure values or layouts changed.
