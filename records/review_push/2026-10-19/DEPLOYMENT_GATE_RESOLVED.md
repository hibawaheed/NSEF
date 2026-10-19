# Deployment gate resolved by read-only browser inspection — 19 October 2026

The user reported reconnection and reiterated authorization to push only `codex/subpsi-low-compute-20261018`, conditional on no deployment, without merging or changing the live website.

The Vercel API still returned 403 for the intended team. A newly opened in-app browser, however, had an authenticated session and could display the project settings. No account permission or deployment setting was changed.

## Observed deployment configuration

- [SubPSI Git settings](https://vercel.com/hibas-projects-09cdb13e/subpsi-lab/settings/git) explicitly stated: **This Project is not connected to a Git repository.** The Deploy Hooks section states that a Git connection is required to set up a hook. No Git connection or hook was created.
- The team project list showed no other project connected to `hibawaheed/NSEF`. Existing connected projects pointed to unrelated repositories; SubPSI displayed “Connect Git Repository.”
- [SubPSI production overview](https://vercel.com/hibas-projects-09cdb13e/subpsi-lab) showed production deployment **HGnj8eCtER8RvWnz96oFCaaHF3yx**, created October 11, Ready, source **vercel deploy**, serving `subpsi-lab.vercel.app`. This is the before-push production identity for the final unchanged-site check.
- The review branch has no `.github/workflows` files. Authenticated GitHub checks confirm main has no `.github` directory, with main at `646bfea7f30d3a52be8ab40cff99590baea4650a`. The GitHub workflow-run API returned no runs for that main commit. No Actions workflow can be triggered from either of these checked trees. A logged-out browser could not inspect the private repository; the connected GitHub app supplied the authenticated checks.
- Local Git has no pre-push hook, custom hooks path, mirror push, configured multi-ref push or follow-tags setting. The planned operation explicitly names only the review branch and does not force-push.

These checks establish no configured Vercel Git/Deploy Hook or repository GitHub Actions deployment trigger for this branch push. This conclusion is scoped to the inspected configuration and should be checked again if settings change. Neither absence of an old deployment nor a non-main branch name alone was treated as evidence.

## Final checks and evidence

Fresh Python, browser-core, package-integrity and original Version 4/correction integrity command results are saved under [reconnected](reconnected/), with actual exit codes and timestamps. No new experiment, feature, calibration or scientific-code change occurred. The publication edits only update the starting documentation and add this read-only check record.

The original [privacy audit](PRIVACY_AUDIT.json) is retained as the audit of the prepared commit `e19a07f7440d128c4bf7b19c19614228d59e6c57`. A second [publication-content audit](RECHECK_PRIVACY_AUDIT.json) covers the updated staged files, including the new documentation and check receipts. Original measured code, chart sources, result tables, and all Version 1–4 evidence remain intact.

This record authorizes no action by itself; authorization comes from the user's messages. It records readiness before the single-branch publication attempt, not a claim that publication has already succeeded. The final response must identify the verified remote SHA and whether production remained unchanged.

## Public-export recheck

2026-10-19T20:31:50.090852+05:00 — Authenticated browser inspection again showed no Git connection for subpsi-lab and that deploy hooks require a connection. Authenticated GitHub branch listing still showed no low-compute review branch, and main and Version 1–4 remained at their recorded SHAs. Fresh export verification passed 137 Python tests in 2.07 s, one browser-core test, all 203 public-package hashes, 19 measured-code hashes, 13 claim-source/configuration hashes, and 7,817 preserved starting files. A clean temporary export without any of the eight profiler binaries also passed the package checker. The check receipts are in public-export/. No settings or deployment changed.
