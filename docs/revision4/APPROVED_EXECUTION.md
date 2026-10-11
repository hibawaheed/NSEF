# Approved Version 4 execution

The user approved the exact proposed protocol and GitHub publication. The new configuration preserves every numerical study setting. This is not evidence of mentor or fair approval.

## Reproduction

Run `python scripts/revision4/run_study.py all` from the repository with the locked dependencies and verified original raw caches. Outputs are new under `results/raw/revision4/main-approved` and `results/summary/revision4/main-approved`. Private record lineage remains in ignored `data/raw/revision4/main-approved`. Existing versions and correction outputs are unchanged.

The script freezes the code/configuration identity and ordered selection cells before computation, saves each completed cell, and refuses to resume with changed code, configuration, support or source files. It saves the selected map before validation and requires completed validation before evaluation. Every cell, including unsupported groups, is retained. No extra seeds or algorithms are added after inspection. CPU use is cumulatively checkpointed across stages; the approved 14,400-second and 2-GiB limits are checked at repetition/cell boundaries. A hard crash between checkpoints can leave one repetition unaccounted for; incomplete cells must be identified in the log.

## Fixed randomization details

NumPy SeedSequence uses `[2026101104, stage, cell_index, repeat, channel]`. Stage numbers are selection 10, validation 20, evaluation 30 and bootstrap 40. Selection/validation cell order is declared group order, reference-grid order, increasing incoming size, then condition order. Validation deduplicates equal group/global sizes. All unsupported cells keep their indices. Channels 1/2 select reference/current whole rows. Channel 4 generates one uint32 seed; feature ordinal is appended for each matched block's permutation RNG.

Evaluation reference and base delivery use cell index 0 for every condition, ensuring paired inputs within each replicate. Weighted replacements use channel 3 and the fixed condition ordinal. They operate only on target-group positions from look 6. The same base permutation seed (channel 4, cell 0, repeat) is used across policies and conditions; the immutable existing engine appends look, group, feature and collection-state indices. PSI and KS always receive identical observation blocks. Repeated source draws are resampling, not new people.

For source-distribution diagnostics, empirical PSI uses normalized bin masses without pseudocounts; joint-zero bins contribute zero. The monitoring statistic retains its fixed 0.5 pseudocount. Source KS uses weighted empirical CDFs. These are descriptive distances, not confidence intervals or proof of detection accuracy.

## Software checks before data-based estimation

124 tests pass. Seven new tests check whole-record resampling, paired condition/reference draws, label-invariant draw selection, distinct RNG namespaces, empirical-distance arithmetic, both-stage support requirements, validation deduplication, retained misses and exact policy ties when maps coincide. A test-file syntax typo was fixed before any data-based calibration. An incorrect group attribute name was caught by code inspection and corrected before execution. Prior 117 tests remain unchanged.

The original proposal and preparation documents retain their historical pending-approval labels. See `records/revision4/main/approval.json` for the subsequent authorization. Work is AI-assisted; no student decision, understanding, independent authorship or mentor approval is invented.
