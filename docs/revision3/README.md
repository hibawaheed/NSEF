# Revision 3 preparation — main evaluation awaiting approval

Start with **[the one consolidated methodological plan](METHODOLOGICAL_PLAN.md)**. It lists feasible datasets, periods, groups, roles, outcomes, comparisons, assumptions, compute and deadline milestones. Nothing in the proposed configuration records an approval.

- [Basic-English explanation](PLAIN_ENGLISH.md)
- [Data source/schema/support cards](DATA_CARDS.md)
- [Methods-level prior-work review](PRIOR_WORK.md)
- [Executed change/command log](../../records/revision3/WORK_LOG.md)
- [AI-use and contribution record](../../records/revision3/AI_USE_AND_CONTRIBUTIONS.md)
- [Support feasibility figure PDF](../../figures/revision3/feasibility/01_support_feasibility.pdf)

New implementation: `src/subpsi/matched.py`; tests: `tests/test_matched.py`, `tests/test_revision3_sources.py`. Preparation scripts: `scripts/revision3/`. Main natural-data/result runners and final presentation charts are still to be completed after approval. No website or remote changes in this revision.

The previous 2,662 tracked files remain byte-for-byte preserved, including v1/v2 failures and negative results. `records/revision3/baseline_inventory.json` makes this checkable. All new raw records and row identifiers are local/ignored; exported feasibility tables contain only aggregated counts and public source metadata.

To run software tests: `python -m pytest -q`. The compact OULAD source extractor can download only needed original tables. For a new reproduction, use a separate checkout/output name: scripts refuse existing result directories. Source snapshots record actual code at each saved preparation run.
