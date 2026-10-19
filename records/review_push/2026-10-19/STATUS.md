# Review-branch preparation — 19 October 2026

The user authorized a push of only `codex/subpsi-low-compute-20261018` to `https://github.com/hibawaheed/NSEF.git`, conditional on tests, privacy review and establishing that no deployment would be triggered. No merge, deployment or submission is authorized. **The push is on hold because the Vercel deployment behavior could not be established.**

## Actual checks

Fresh results are saved in [CHECKS.json](CHECKS.json), [Python test output](python_tests_final.txt), [browser test output](browser_tests_final.txt), [package integrity](package_integrity.txt), and [Version 4 integrity](version4_integrity.txt). All four commands exited successfully. The Python suite contains 137 passing tests; the browser-core test passes. Package verification checks all 7,817 starting files, 211 package files, 19 measured code files, 96 process receipts, 80 timed processes and 24 selected scientific replays. It is a read-only evidence check, not a rerun of experiments. The original Version 4/correction manifests also pass.

The first pytest command completed successfully but its shell wrapper then attempted to assign zsh's read-only `status` variable. The full final test was rerun with a Python subprocess wrapper and its actual return code recorded. No code or tolerance was changed to pass a test.

## Deployment gate

- GitHub's authenticated branch listing verified the intended repository, main at `646bfea7f30d3a52be8ab40cff99590baea4650a` and Version 4 at `39014345b53f4ff7fe8481e6aa9a996d00c10b5b`. The proposed branch did not exist remotely at inspection time.
- No GitHub Actions workflow files or Vercel configuration are present in the outgoing branch. Authenticated reading of main's README succeeds; reading main's `.github` directory returns not found. The added `.github/README.md` is documentation only. The connector does not allow its generic fetch tool to list Actions workflows; an unauthenticated API check returned 404. This does not establish all account-level integration behavior.
- Vercel listed the `subpsi-lab` project. Reading its project details and repository-linked project settings under the returned team returned **403 Forbidden**. The connector's mapped CLI fallback is unavailable because no Vercel executable is installed. Browser inventory contained no authenticated browser tabs. Listing the project is not evidence that Git integration is disconnected or that previews are disabled.
- Therefore neither a preview nor a production deployment can be ruled out. No push, deployment, configuration change, reconnect, merge or submission was attempted. The user must restore read access to the intended Vercel team's project settings before this condition can be resolved. Do not assume a non-main branch is safe and do not silently disable deployment settings.

## Publication cleanup and preservation

The original two local commits are retained at `refs/local-only/subpsi-low-compute-original-20261019`, pointing to `0c156cb9b515dcacb6b974c1095c7923302f9abe`. Only the review branch is prepared for possible future publication; that local-only preservation ref must not be pushed.

The prospective public history starts from the existing Version 4 commit. It excludes the original unpublished commit metadata containing a local network address. Its new commit identifies Codex as the preparer, rather than implying student authorship. This is local publication preparation; there is no remote history rewrite or force-push.

Ten new diagnostic files contained local account paths: eight cProfile files, their function CSV and the initial OULAD parsing diagnostic. The paths were replaced with `<HOME>`. Every numerical profiler leaf was checked unchanged. The [redaction ledger](REDACTIONS.json) retains before/after hashes; the [original final manifest](ORIGINAL_FINAL_MANIFEST.json) is retained alongside the updated public manifest. The untouched original bytes remain recoverable from the local-only Git ref. New browser-test logs have the same path redaction. No scientific code, test, benchmark configuration, numerical result, chart or chart-source CSV was modified.

Source-code/figure hashes and package checks remain authoritative. The original measured commit ID `0ca31347b216bb617ac071257386dc4331cf4407` remains in the execution manifest as an honest local provenance identifier; it will not necessarily resolve on GitHub after publication cleanup. The review branch contains the same measured code bytes.

The privacy review covers all new file versions from the two original outgoing commits, including decompressed JSON traces and binary cProfile content, plus the final publication preparation files. No new respondent archives, raw NPZ records, private draw lineages, signed forms, credentials or tokens were found in those outgoing files. Aggregate block hashes and test RNG seeds are retained as reproducibility evidence. Existing public Version 1–4 ancestry is preserved, not rewritten. See [PRIVACY_AUDIT.json](PRIVACY_AUDIT.json) for the final staged-content checks and their scope limitations.

## Contributions and stopping point

Codex performed the inspection, fresh checks, metadata/path redaction, publication documentation and local commit preparation under the user's conditional authorization. No new scientific decision, dataset, calibration, classifier or experiment was introduced. The original [AI-use record](../../low_compute/2026-10-18/AI_USE.md) describes the earlier engineering pass; this note records the later conditional push request without inventing student, mentor or fair approval. Development is stopped. Only resolution of the publication gate remains.
