# Read-only verification of Version 4

To check the delivered evidence without downloading source data, installing scientific libraries, or changing any file:

```sh
python scripts/revision4/verify_snapshot.py
```

This compares saved file hashes for the Version 4 results, original preparation, preceding correction and all 4,997 files present at the revision’s starting point. It verifies integrity, not statistical assumptions or universal accuracy.

For numerical replays and original-source checks, follow [the reproduction instructions](docs/revision4/REPRODUCE_MAIN.md). Those verifiers preserve the delivered receipts and save repeat audit receipts in ignored local paths.

`finalize_evidence.py` is the one-time snapshot-creation utility. Do not rerun it in the frozen delivered checkout: use the read-only checker above. The experiment’s pinned commit and the complete source snapshots allow a separate reproduction without replacing this evidence.

The append-only change log and later GitHub publication receipt are outside the scientific snapshot. They can record publication after the results were frozen. No final submission version, mentor approval or fair approval is implied.
