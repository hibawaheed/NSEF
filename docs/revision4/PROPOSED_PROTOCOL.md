# SubPSI Revision 4 — one methodological approval checkpoint

**Proposed, not approved. Prepared 11 October 2026 with AI assistance.** No new data-based calibration or follow-up evaluation has run. This is a technical proposal for the student and mentor to review, not a student-authored research submission. The machine-readable settings are in [proposed.json](../../configs/revision4/proposed.json). Earlier approvals do not authorize these settings.

The question is whether targets chosen from separate historical records improve detection, assessability, waiting and cost compared with fixed targets. Subgroup-decomposed PSI remains the core, with matched KS throughout. A sensitivity study and negative or tied policy comparison are valid outcomes. Neither a new algorithm nor PSI superiority is established.

## What is already completed

The clean starting point was local correction commit `7ddcc02c4bf458b68617bbd5b1f184cbfb82e1c5`, descending from published Version 3 `27288575028181baae90f68d30d4e3dc5e363a53`. The separate local branch is `codex/subpsi-r4-calibrated-collection`. GitHub's Version 3 still points to the latter SHA; main still points to Version 2. No push occurred.

The preceding correction already fixed OULAD attempts to 0 / 1 / 2+ and completed all 1,820 matched Version 2 synthetic streams. Those outputs remain unchanged. This preparation adds a representation audit, balanced-accuracy reporting from saved confusion counts, a tested immutable-target collector, a symmetric selection-table lookup, private lineage guards and two reporting figures. All 117 tests pass. Four earlier key runs were reproduced; ten earlier figure CSVs match their source tables. The 4,997 files tracked at the starting commit are protected by a new inventory; the prior 1,990-file correction freeze was verified.

## Data roles and feasible support

Reuse the already verified official sources, local receipts and original role assignments. No new dataset is proposed. [Census public-use/citation guidance](https://www.census.gov/about/policies/citation.html) and [UCI's OULAD CC BY 4.0 record](https://archive.ics.uci.edu/dataset/349/open+university+learning+analytics+dataset) were checked again. Exact archive/member hashes are in the preparation manifest and the earlier data cards.

| Role | Records and restrictions |
|---|---|
| Bin design | Existing 2015 Massachusetts ACS design role: 14,320 people, unchanged six-bin age/schooling representation. OULAD keeps the historical 372-person design and corrected count bins. |
| Calibration selection | The previously reserved 2015 ACS calibration role, one lowest-SPORDER eligible adult per household, split by the fixed R4 household hash: **3,924** representatives. Only this stage's feature-based sensitivity summaries may select targets. |
| Calibration validation | Other half of that reserved role: **3,944** representatives, household-disjoint from selection. Separate draws/seeds. Assess the frozen targets without revising them. |
| Constructed evaluation | Reuse the Version 3 **2016 ACS reference-role household pool**. It is separate from the 2015 calibration source by the recorded year/household keys. Draw new pseudo-references and streams from this pool; it is previously examined evidence, not a new population validation sample. |
| Natural reference/monitoring | Preserve ACS 2016 versus actual 2017–2019 releases and BBB OULAD 2013J versus 2014J. Descriptive results only. Reproduce corrected OULAD results after approval in new directories; do not refit the frozen model. |
| Outcome audits | Keep previous disjoint audit roles and frozen model. The OULAD constant class is fixed by training counts 319 negative / 438 positive, zero on ties. Labels never choose collection targets. ACS remains ESR=1, civilian employed and at work; OULAD remains successful completion, not ability. |

The role hash is `SHA256('r4-calibration-20261011|' + year:SERIALNO)`: first unsigned 64 bits below `2**63` select the selection half. It was fixed before sensitivity estimation. Household role conflicts and OULAD student conflicts were checked and none found. The earlier OULAD repeated-student exclusion remains unchanged. Keys cannot prove that different survey years contain entirely different people; no identity linkage is attempted.

Inspection of executable Version 3/correction code found no use of the reserved 2015 calibration role for bins, fitting or detection experiments. Schema and counts had been inspected, and loaders had read the files; it is **not claimed untouched**. New preparation inspected only roles, support and counts on either side of the proposed age cut, not calibration distances, p-values or power.

Historical support requires **50 distinct household representatives and at least 5 on each side of age 60 in each calibration half**. Exactly **15/30 declared views** qualify. All 30 stay in result tables and the statistical family. The other 15 receive explicit calibration-shortage status and the fixed fallback. Their absence from the calibration fitting subset is never described as successful detection or adequate power. The full support table is `results/summary/revision4/preparation-02/acs_candidate_support.csv`.

No OULAD collection-target calibration is proposed: its small historical roles and single later cohort do not support a convincing separate selection/validation/stream study. It remains a compact corrected natural case study. That is a scope limit, not a reason to manufacture chronology or new records.

## Historical sensitivity experiment

| Setting | Proposed value |
|---|---|
| Features and group family | AGEP and SCHL; existing Everyone, SEX, RAC1P and all intersections: 30 views, 60 tests. |
| Pseudo-reference sizes per group | **100, 400, 800** draws; distinguish these from numbers of distinct source households. |
| Incoming group counts | **50, 100, 200, 400, 800** draws. No interpolation or extrapolation. |
| Repetitions | **100** paired repetitions per supported group × reference size × incoming size × condition. |
| Conditions used for selection | Unchanged, age-up2 and age-up4. Both non-null changes are DESIGN alternatives. |
| Selection planning reference size | **400**. Other reference sizes characterize sensitivity; they do not permit changing the rule after inspection. |
| Held-out stress pattern | Age-down4, used only in independent validation and final evaluation. |

Within each group, take the stage's declared empirical pool as the reference distribution. Unchanged reference and incoming samples are drawn independently **from that same pool**, with replacement. Under age-up2 or age-up4, multiply a record's sampling weight by 2 or 4 if its recorded **AGEP ≥ 60**, otherwise by 1, and normalize. Age-down4 uses multiplier 0.25. The cut is a proposed, fixed whole-year age threshold, not chosen by scanning later effects. It is not a claim about retirement, harm or discrimination.

Every draw carries its original features, group codes and label together. We never edit age, schooling or outcomes. Changed probabilities can affect correlated fields; report distances for both features and do not call the intervention an isolated causal age effect. Save the empirical source PSI/KS distances, draw counts, distinct-source counts and privately auditable draw-to-source IDs. Repeated source draws are not additional people. A 50-household support gate does not create 800 unique households.

Single-block success means that **at least one of the exact group's two features** has a p-value at most **.05/(20×60)** for that statistic. This is a conservative sufficient cutoff for the intended full-family Holm procedure. It is deliberately harder than unadjusted .05, and can miss rejections that step-down Holm would make. PSI and KS use identical draws. These estimates describe sensitivity of a single block, not whole-stream detection probability or an 80% guarantee.

There are at most **67,500 matched group-block repetitions** in selection (15×3×5×3×100), each evaluating two features with both statistics. Unsupported cells remain explicit without simulated estimates. Parameter choices can produce low power or flat curves. In particular, finite reference size and strict multiple-testing correction may prevent any incoming target from meeting the criterion.

## Frozen target selection and validation

For each historically supported group at pseudo-reference size 400, calculate the lower endpoint of a **pointwise two-sided 95% Wilson interval** for exact-group success. At each incoming size take the minimum across **PSI, KS and both design alternatives**. Choose the smallest tested size whose minimum is at least **0.80**. Finite Monte Carlo estimates need not be monotone; inspect the actual grid without smoothing away failures.

For the **global calibrated baseline**, use the exact same calibration cells and choose the smallest single size satisfying that criterion for **every historically supported group**. This is the comparable worst-group planning objective with one common target; it receives no extra calibration data. Preserve any advantage or cost disadvantage caused by this constraint.

When a group lacks historical support or no size meets the criterion, use incoming target **800**, accompanied by the corresponding shortage or target-unmet flag. A maximum-size fallback is not a successful calibration. All unsupported groups stay visible. If no global size passes, the global baseline is also 800 and marked unmet. If all maps coincide, report that tie instead of inventing another rule.

Freeze the maps and hashes **before** accessing validation feature-based results or final evaluation. On the independent validation half, use reference size 400 and 100 repetitions per group/condition for the selected group target and the global target, deduplicating identical sizes. Include unchanged and all three alternatives. Maximum **12,000** matched blocks. Reapply the same descriptive criterion and show failures, but never retune targets or omit a failed group. The pointwise intervals and selected estimates are not simultaneous certification; validation is a diagnostic check. The final comparison still uses the originally frozen maps and labels failed validation explicitly.

The deployed research collector sees only the immutable map, group membership, counts and delivery index. Its common reference gate is **50**, separate from the incoming target. It consumes whole batches, so actual blocks may overshoot the target; 800 is a target cap, not a hard buffer bound. Unsupported references cannot be repaired by pooling incoming records. Unfinished collections remain unfinished at look 20. No value-based early stop, p-value-based extension or alpha reset is permitted.

Actual evaluation reference-group counts will differ from planning size 400. Record those counts for every run. Sensitivity at 100/400/800 helps expose this mismatch but does not certify power at arbitrary reference sizes. Target selection will not read evaluated-reference feature values, later features, labels or result tables. Calibration runs must load only the historical role; role/count metadata are the only permitted cross-stage planning input.

## Matched final constructed comparison

Use one compact delivery setting: **1,000 records per batch, 20 batches, a fresh 10,000-draw reference per repetition**. This retains the existing Version 3 scales without a large new Cartesian product. Compare ordinary batch minimum 50, fixed accumulation 100, fixed accumulation 400, global calibrated and subgroup calibrated targets. Both statistics share exact reference records, whole incoming blocks, reset times and support rules **within each policy**. Across policies, the underlying delivery stream is identical; different block boundaries and waiting costs are legitimate results.

Use **100 unchanged streams** and **40 streams for each of age-up2, age-up4 and age-down4**: 220 paired streams, 1,100 policy engines. The named target stays **SEX=2 & RAC1P=2**, as in the prior controls. For alternatives, only target-group draws from delivery indices **6 through 20** are replaced by whole draws from the same group's weighted 2016 pool. Preserve membership counts and the original source values. Before index 6 everything follows the unchanged source. Reference and base delivery draws use independent RNG namespaces; reuse those draws across policies/conditions for paired comparisons. Indices are constructed delivery positions, not days or survey collection chronology.

The unchanged null in each stage uses one common empirical source for reference and current draws. Distinct finite subpools are used **between stages**, never mistaken for an exact within-stage null. Independent resampling establishes conditional independence of draws given the finite pool, not independent new respondents or population generalization. All later pools have already been examined. Seed lists, ordered cell inventory and RNG channels are fixed before running, and private lineage is validated against every source field.

Retain the original Version 3 weak 2016→2017 substitution result as a separately labelled limitation check. Do not tune against its known misses or portray the new sampling changes as explaining them away. The OULAD bin correction does not explain those ACS misses. Reuse the already completed Version 2 matched extension as labelled synthetic evidence; there is no need to repeat its full campaign.

## Statistical interpretation and uncertainty

The primary scope is the full intersection family; aggregate and single-attribute scopes are secondary. Each statistic/policy/scope is a separate comparator with alpha **.05 over 20 looks**. Holm correction retains every predeclared feature/group test, unsupported tests at p=1. Look spending remains .05/20 after resets and empty deliveries. The union of methods/policies/scopes has no inherited .05 guarantee.

Use **23,999** PSI permutations, pseudocount .5 and conservative stopping. The plus-one p-value floor 1/24,000 equals the strict first-Holm boundary .05/(20×60); reject any configuration with worse resolution. This is a minimal, coarse permutation resolution, and its discreteness is a limitation, not precision to hide. Keep the existing KS missingness factor of two, conservative handling of ties and p=1 on exact-calculation warning/fallback. Do not remove those safeguards after seeing unfavorable comparisons.

Under the constructed unchanged model, source-specific independent draws and fixed bins give the within-group exchangeable null. Historical target selection is separate from the evaluation source; current count-based stopping does not use feature scores. Conditional on group-membership/count schedules, comparisons retain that null argument. Shared references and overlapping groups make tests dependent; Holm plus the finite-horizon union bound does not require independence across those tests. This argument does not transfer to natural survey rows, imputed observations or real temporal dependence. Empirical null checks can reveal problems; zero alerts do not prove a general theorem.

Report any alert, exact-target alert, pre-onset alert, ever assessable, assessment fraction, first assessment, first exact-target detection, and restricted delay including misses. Restricted post-onset delay is first detection index minus 6, with **15** for no detection by index 20. First assessment is a separate endpoint. Exact-target detection is not applicable to aggregate-only reporting. In all-group summaries retain groups never assessed.

Use 95% Wilson intervals for Monte Carlo proportions and **2,000 paired complete-stream bootstrap** draws for policy/statistic differences, separately by condition. A stream—not a group, look or repeated person—is the uncertainty unit. Report intervals as pointwise conditional Monte Carlo uncertainty. A zero-width paired interval means the measured paired endpoints coincided in these runs, not universal equivalence. Never add seeds until significance appears. Natural ACS/OULAD observations get descriptive metrics and denominators, without natural drift-detection accuracy or artificial replicate confidence intervals.

## Compute, outputs and stopping

Six fixed software timing fixtures took roughly 0.0005–0.0008 seconds per easy matched feature block and 0.021–0.023 seconds when PSI used all permutations. These are cost probes, not power evidence. The prior complete 1,820-stream extension took about 24.7 minutes. Estimate **1–3 hours local computation** for the proposed selection, validation, streams and exports; allow a **four-hour total CPU cap**, working memory **2 GiB**, no paid compute. Loading and large-group testing can exceed fixture estimates. Record selection/validation and monitoring costs separately, including full-process peak RSS, frame/ID/buffer storage, kernel times and engine wall time. Histogram bytes are not total memory or proof of a faster system.

Implement hash-bound resumable cell outputs after approval. Stop at a cap or broken separation/validity check, keep the partial record and report the issue. Do not silently reduce repeats, relax thresholds or substitute sources. If the policy cannot be justified/tested by **15 October**, finish the sensitivity/correction evidence and mark it unvalidated. Freeze scientific claims/results by **18 October**, earlier than the obsolete Version 3 target of 20 October. Today is 11 October; no current schedule conflict. The prior bounded correction/V2 comparison is already finished before its 14 October limit. Deadline remains **26 October**; intended student-controlled submission is 25 October.

Export the six requested figure families only when their underlying data exist, with exact CSVs, 300 dpi PNG and vector PDF/SVG, manifests, code/config/data hashes and visual checks. Separate natural observations, constructed real-record controls and mathematical simulations. The two preparation charts are already available; no sensitivity curve or calibrated target map is fabricated now. Maintain the claim ledger, AI-use/change/command records and basic-English graph guide. Complete student writing and mentor review remain distinct contributions.

**Single approval requested:** approve this proposed configuration and workflow, or specify amendments. Approval authorizes local calibration/evaluation and routine implementation choices within this scope. It does not establish mentor/fair/SRC approval, a final selected project version, or permission to push, merge, deploy, purchase or submit.
