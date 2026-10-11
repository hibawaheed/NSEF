# Reproduce the completed Version 4 study

The experimental code was frozen at commit `1b1509e8ec895208e75dc652b35504434f72b98a`. Final reporting code is committed at `e689516b57e557184c9a9b4ea21063a5bd4b3481`; its file hash is also in the figure manifest. The approved settings are `configs/revision4/approved.json`. All previous version files remain intact.

## Read or verify the delivered results

Use the locked Python environment and the genuine source cache. From the repository root:

```sh
python -m pytest -q
python scripts/revision4/verify_study.py
python scripts/revision4/verify_evaluation.py
```

The first verifier checks the protected earlier evidence and reproduces three fixed calibration cells. The second verifies every completed engine, complete declared test families, unsupported p=1 placeholders, all identical-map ties, source/draw lineage and two fixed complete policy streams. Verification preserves the delivered reports. Subsequent audit receipts are saved with unique names in ignored `data/raw/revision4/verification-replays`, so checking the study does not overwrite its evidence snapshot.

Raw public result records are under `results/raw/revision4/main-approved`. Summary tables are under `results/summary/revision4/main-approved`. Private source identities and positional draw arrays remain in ignored `data/raw/revision4/main-approved`. Official source and deterministic-role reconstruction instructions are in [Version 3 reproduction](../revision3/REPRODUCE_MAIN.md). Regenerated archives and role files must match the published hashes in `selection_sources.json`, `validation_sources.json`, `evaluation_sources.json` and the OULAD replay manifest. Do not silently substitute changed downloads.

## Recompute the experiment in a separate checkout

Use a separate checkout at the experimental commit above, recreate/verify the ignored official source cache and deterministic role files, then run:

```sh
python scripts/revision4/run_study.py all
```

That commit precedes the saved main output directories, so the fixed new paths are unused. Do not delete the delivered evidence or change the declared experiment just to make it rerun. The runner saves an identity containing configuration, support and all source-code hashes, then fixed ordered cells. It resumes completed cells only under the same identity and source hashes. Later reporting scripts intentionally change the overall code inventory; use the pinned experimental commit or preserved `source_snapshot.zip` for an exact computational rerun rather than weakening the resume check.

Sampling uses the saved SeedSequence definitions, ordered inventories and private source positions. All 1,350 selection cells and 120 validation cells remain, including unsupported cells. There are 67,500 supported selection repetitions, 6,000 validation repetitions, 220 evaluation streams and 1,100 policy engines. Completed selection produces a hashed map before validation/evaluation. The group/global maps both equal 800 because the criterion was unmet; this is not a successful calibration. The main study’s total CPU cap is 14,400 seconds, with a 2-GiB working-memory budget. No failed criterion is repaired by adding repetitions or changing thresholds.

To redraw saved results in a new, unused directory:

```sh
python scripts/revision4/report_study.py --out figures/revision4/reproduction-001
```

Set `MPLCONFIGDIR` to a writable cache if needed. Use the reporting code commit above; graph layout metadata and measured timing may differ by platform. The final data values, count endpoints, source rows and statistical decisions should reproduce. The bootstrap uses stage 40, the fixed condition ordinal as cell, repeat 0 and channel 1; the same 2,000 complete-stream resamples are reused across the declared paired comparisons within each condition. Direction is policy/method A minus B. Intervals are pointwise, conditional on the fixed empirical source.

## Natural OULAD replay and reporting history

The OULAD replay calls the unchanged `natural` function in `scripts/correction/run.py` with `configs/correction/frozen.json` and a new output directory. The exact invocation and CPU/provenance receipt are recorded in the main log and replay manifest. Four numerical/data artifacts matched the preceding correction byte-for-byte. No model search or refitting of the frozen logistic model occurred.

`figures/revision4/main-approved` preserves the first failed rendering with a failure record. `main-approved-checked` preserves the first complete rendering before a paper-footer spacing fix and plain-language scenario labels. Use **`figures/revision4/final`**. Its twelve exact CSVs match the corresponding first-complete-render CSVs; only presentation changed. `report_before_layout_fix.py.txt` preserves that earlier reporter source. Wilson boundary display rounding and pandas None/NaN comparison repairs are recorded and did not alter experimental runs.

`stream_endpoints_reported.csv` explicitly marks inapplicable exact-target scopes and separates null false alerts from detections. Raw engine records and original `streams.csv` remain unchanged. The main findings and claim ledger identify which version of evidence supports each statement. Natural observations have no fabricated accuracy estimate or artificial replicate confidence interval.
