# Version-3 publication authorization and plan

On 11 October 2026 the user wrote: “push all of ity as a third version, keeping the second and first verion” and “ill lyk in the end which one is the finalised version”.

This authorizes publication of the completed local revision, code, computed results, charts, CSV sources and logs to the existing private `hibawaheed/NSEF` repository. Keep explicit `version-1`, `version-2` and `version-3` branches; do not select a final version, overwrite the earlier versions, merge into main, change visibility, or redeploy the website.

Local research release before publication documentation: `049f2bbbba91ab3b75a219a8665432019bc63bb7`. The research results and their original execution hashes stay unchanged. Main execution statements saying that no push occurred describe the earlier research stage; this later request separately authorizes publication.

Terminal Git has no saved credentials. The connected GitHub account has repository write permission. Publication will use its authenticated connector and a one-time bounded import workflow to transfer a checked incremental Git bundle, preserving the original local research commits and normal browsable repository files. The job only creates the version-3 branch, checks its complete tree and file count, and removes its own temporary transfer branch. It does not run or change the scientific experiments, alter the website, or expose credentials.

Previous branches inspected before publication: `main` at `646bfea7f30d3a52be8ab40cff99590baea4650a`; `codex/subpsi-foundation` at `247c87fc353668ef0af408e20445607172950ea3`. Final import verification is recorded in the one-time Actions run and the publication receipt.

## Completion

The import succeeded in Actions run [38156361391](https://github.com/hibawaheed/NSEF/actions/runs/38156361391). GitHub version 3 matched the complete local source tree and all 3,010 tracked files before this receipt update. All twelve checked PNG/SVG/PDF/CSV chart sets and the combined PDF are present. Versions 1 and 2, main and the original foundation branch retained their verified commits; the temporary transfer branch was removed. The scientific results were not rerun or changed. See `RECEIPT.json` for the exact hashes. Final-version selection remains with the user.
