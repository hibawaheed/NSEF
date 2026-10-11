# Starting state — 11 October 2026

Registered title: **SubPSI: Detecting Hidden Bias Drift in Machine Learning Through Subgroup-Decomposed Population Stability Analysis**.

The connected GitHub account returned the private repository `hibawaheed/NSEF`. Its contents endpoint reported “This repository is empty.” No local checkout or existing tests/results were found. A new local repository was initialized on `codex/subpsi-foundation` and its origin set to that repository. No remote content was changed.

The original source was found in Downloads and preserved byte-for-byte at `legacy/subgroup_psi_original.py`; SHA-256 is in `records/input_inventory.json`. The two attached documents and the older project handoff were read. They are project context, not evidence of completed work or approvals. The user's later instruction explicitly authorizes proceeding without waiting for protocol sign-off, while documenting work. No mentor or fair approval is claimed.

Four supplied research PDFs and the older mentor brief exist. Only the first two pages were extracted during this audit; no complete literature review is claimed. `FIGURE_SPEC.md`, `SUBMISSION_CHECKLIST.md`, `SOURCE_AND_NOVELTY_NOTES.md`, and prior week-one validation files were not found. New specifications in this repository are marked as newly prepared.

## Verified source defects

1. Numeric histogram endpoints cover only the reference range. Current outliers disappear from counts while the denominator still includes them. The software fixture in `records/original_audit.json` demonstrates this.
2. Clipped bin probabilities are not renormalized.
3. Only the current subgroup count is checked. A small or empty reference can still reach the calculation.
4. Iterating only current group values hides groups that disappear. New groups can cause empty-reference failure.
5. The main subgroup function does not invoke the permutation or BH functions.
6. The random permutation p-value is `count / n_perm`, allowing zero.
7. The current-only bootstrap and its “tight interval signals a real signal” explanation do not establish a calibrated drift test.
8. The demo copies reference observations into current data, violating independent-sample assumptions if treated as independent monitoring evidence.
9. Documentation describes BH as overall false-alarm control without distinguishing false discovery rate from family-wise or stream-wide error.

The original permutation routine refits its bins during each shuffle. Refitting a statistic consistently is not itself a permutation-validity defect; the new implementation instead learns bins on independent design data and freezes them.

## Initial implementation scope

Build a tested fixed-bin estimator, explicit unsupported cases, valid independent-sample permutation draws, named multiplicity comparisons, six synthetic stress tests, one openly licensed public-data check, and traceable figures. Use a small fixed logistic classifier and keep labels out of the detector. Exclude automatic repair, cloud deployment, and broad subgroup searches from this first evidence package.

Software tests and exact commands are saved in `records/validation_commands.json` and `records/validation_output.txt`. Runtime is measured in run manifests; it is not copied from earlier claims. Dependency download time is separate from computation time.
