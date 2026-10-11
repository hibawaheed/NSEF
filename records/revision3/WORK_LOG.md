# Revision 3 executed-work log

AI-assisted log,11 October 2026. Actions below actually occurred; proposals are separated in the consolidated plan. No invented student or mentor activities.

1. Read both supplied improvement documents in full. They have identical SHA-256 hashes. Preserved the TXT specification at `docs/revision3/REQUESTED_SPECIFICATION.txt`.
2. Inspected clean local HEAD 7fffe23 and GitHub main 646bfea through read-only API. Their file trees matched e221d5136ca9b2cc738fc44a3d634f32fbeaad7a. Created local branch `codex/subpsi-real-data-r3`. Saved SHA-256 inventory of all 2,662 tracked files; no old evidence modified.
3. Read core/revision code, tests, configurations, v2 findings/methods/prior-work records, experiment/public runners, summary/plot/provenance scripts and contribution logs. Confirmed v2 lacks accumulated KS, hardcodes nine binary views and target 8, and only times ordinary statistics. New code lives separately.
4. Baseline `python -m pytest -q`:43 passed. `python scripts/validate_revision.py`:1,820 synthetic and120 Adult raw results plus snapshots verified;10 figure/table/manifests and PDF pages verified; five saved smoke/main numerical matches verified. Existing manifest claims were checked rather than merely repeated.
5. Recorded a pre-inspection source/selection rationale. Downloaded and CRC/SHA-256-checked five official Massachusetts ACS 1-Year person archives. Saved year-specific dictionaries,2019 accuracy document, Folktables source and primary research methods. First network attempt failed under sandbox DNS; permitted download then succeeded. Two initially guessed dictionary URLs returned 404; official alternative filenames resolved them. Both failure and successful receipts remain recorded.
6. Added `src/subpsi/matched.py`: fixed named groups, one shared membership/count/time scheduler, complete-block matching, joint resets, absent groups, explicit support, no outcome inputs, finite horizon, optional shared age expiration, descriptive default, matched PSI/KS statistics and costs, conservative KS-fallback handling. Nominal KS is unavailable rather than arbitrarily ordered. No new algorithmic claim made.
7. Added meaningful scheduler/statistic/source-extraction tests, including whole-block overshoot, no reuse across batches, overlapping views, missing values, empty/undersized references, constants/ties/tails/unequal counts, nominal unknowns, same blocks across multiple features, age boundary/expiration/no budget reset, duplicate IDs, p-resolution, and source CRC/truncation failures. Final test output is in `final_tests.txt`.
8. Replayed precisely three preselected existing v2 streams (original generators/config/seeds, repeat 0) into a new software-validation directory. All 720 accumulated group-feature opportunities matched original PSI support/counts/start boundaries/scores/alert group sets. Added KS on exactly those blocks. Saved raw JSON, full source snapshot and cost CSV. Runtime 3.95 seconds with profiling; this is implementation validation, not a new main study or detection-rate estimate.
9. Ran ACS schema/support-only inspection. Preserved private household/person role lineage, weights and allocation flags. Found all 80replicate weights each year, an unused 2019relationship-column change, and the Folktables paper/loader age-filter discrepancy. Checked actual label meaning. Under proposed disjoint roles 18/30 views have sufficient historical support; 12 do not. No natural drift scores or model predictions run.
10. For OULAD, verified the three needed original ZIP members from the downloaded prefix (size,CRC,SHA-256). Preserved 1,546,601 original bytes and member hashes. Server ignored HTTP Range; full click-log download was deliberately stopped after compact tables were extracted. The larger incomplete `.part` remains local and is not evidence input. Added a reproducible compact fetch/extractor.
11. OULAD initial support run failed because UCI encodes missing dates as`?`; preserved failure log and incomplete directory. Fixed parser explicitly and wrote a fresh checked directory. Fixed selection rule chooses BBB 2013J/2014J. Checked unique composite keys, real cohort periods, repeated students, label codes and support. Found 4,529 selected raw enrolments; after 650 day-0 exclusions and 44 later-repeat removals,3,835 remain. No future events used as predictors and no click rows analyzed.
12. Inspected specified methods plus ADWIN/KSWIN. Main novelty currently unsupported; windowed KS and stale-data removal are established. Prepared a comparison matrix with access limitations and corrected overly broad interpretations of prior error-control discussion.
13. Generated and visually inspected one feasibility chart with every declared intersection, exact CSV,SVG,PDF,300dpiPNG and hashes. It shows count feasibility only; no new natural drift or accuracy results. Prepared data cards, basic-English explanations and ONE consolidated proposed methodological plan.
14. Preserved exact code versions for earlier schema/figure checks in `source_snapshots/`, including hash-verified recovery from the software replay snapshot. Recorded proposed configuration with `main_evaluation_authorized:false`. No final freeze, main run, push, deploy, submit or purchase.

## Main commands actually run

Run from repository root with the existing task virtualenv's Python:

```sh
git status --short --branch
git rev-parse HEAD 'HEAD^{tree}'
git switch -c codex/subpsi-real-data-r3
python -m pytest -q
python scripts/validate_revision.py
python scripts/revision3/fetch_sources.py
python scripts/revision3/fetch_documentation.py
python scripts/revision3/inspect_support.py --dataset acs --out results/raw/revision3/acs-feasibility
python scripts/revision3/validate_matched_replay.py
python scripts/revision3/extract_oulad_metadata.py --prefix data/raw/revision3/oulad/oulad.part
python scripts/revision3/inspect_support.py --dataset oulad --out results/raw/revision3/oulad-feasibility
python scripts/revision3/inspect_support.py --dataset oulad --out results/raw/revision3/oulad-feasibility-checked
python scripts/revision3/plot_support.py
python -m pytest -q
```

The first OULAD support command failed and is not a result set. Source-download scripts had the specific failures described above; corrected documentation fetches were also executed as short Python commands and their URLs/hashes are saved. The shell used the absolute task virtualenv path; logs preserve actual outputs. All evidence directories refuse overwrite. Do not blindly rerun these commands into delivered directories.

## Remaining work after plan approval

Complete natural dataset/model/audit runners; construct controlled sampling streams with exact lineage; freeze the accepted plan/config/seeds; run the main studies; build all main result figures; verify claims and logs. Implementing source inspection and the matched engine does not mean this main pipeline has already run. Student/mentor approval is the current intentional stopping point.

15. Final software tests: **67 passed in 1.19 seconds**, including24new tests beyond the43-test baseline. Preparation verifier confirmed every one of the2,662pre-revision files byte-identical, all360synthetic-v1/80Adult-v1raw hashes and snapshots valid, all new preparation outputs and source-byte hashes valid, and the main-approval flag still false. Visually checked the4200×3300support PNG for legibility and retained its vector formats. No main-evaluation findings are claimed.
16. Prepared a local revision checkpoint and delivery manifest. This is local version control only; no push, deployment, purchase or submission. The consolidated plan is the intentional approval gate requested by the user.
