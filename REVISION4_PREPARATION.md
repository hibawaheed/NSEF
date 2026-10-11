# SubPSI Revision 4 preparation — awaiting the new protocol's approval

Continue the existing project from local correction commit `7ddcc02`, on `codex/subpsi-r4-calibrated-collection`. Versions 1–3 and the prior correction remain intact. Nothing has been pushed or deployed for this revision.

- [One consolidated methodological proposal](docs/revision4/PROPOSED_PROTOCOL.md) and [proposed settings](configs/revision4/proposed.json).
- [What changed and what the charts mean](docs/revision4/CORRECTIONS_AND_GUIDE.md).
- [Two OULAD charts, including balanced accuracy and the training-only baseline](figures/revision4/preparation/index.html).
- [Historical role/support counts](results/summary/revision4/preparation-02/acs_candidate_support.csv).
- [Prior-work boundary](docs/revision4/PRIOR_WORK.md) and [reproduction instructions](docs/revision4/REPRODUCE_PREPARATION.md).
- [Claims linked to source evidence](docs/revision4/CLAIM_EVIDENCE.csv).
- [AI-use and change log](records/revision4/WORK_LOG.md) and [student decision prompts](docs/revision4/STUDENT_DECISIONS.md).

Implemented and tested: representation diagnostics, balanced-accuracy reporting, immutable per-group collection targets, a separate reference gate, matched PSI/KS execution, symmetric target selection from historical summaries, and private whole-record lineage checks. **117 tests pass.** The previous correction's key runs and ten figure CSVs were reproduced/verified. No new data-based calibration or follow-up evaluation has run, and no new algorithmic claim is established.

The research implementation is Python code under `src/subpsi/` with saved configurations/results. The existing website is a demonstration; it has not been updated to Revision 4 and is not a substitute for the research pipeline.

New results freeze: **18 October 2026**. Submission deadline: **26 October 2026**. Approval of this plan will not be recorded as mentor/fair approval or as selection of the final project version.
