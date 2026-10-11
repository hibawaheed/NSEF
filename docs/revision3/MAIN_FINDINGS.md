# SubPSI revision 3: what was built and what the evidence says

AI-assisted technical report, 11 October 2026. This is explanatory material for the student and mentor, not a student-authored final submission. The user approved the consolidated plan in chat; the exact message is recorded in `records/revision3/main/approval.json`. No independently verified mentor action is asserted.

**The approved study is complete. Accumulating records improved assessability for some small groups, equally for PSI and KS. It did not recover the prescribed target substitution in these experiments. The evidence does not establish a superior or novel drift-detection algorithm.** A reproducible empirical study of subgroup monitoring, support limitations, waiting, binning and outcome disagreement is the defensible contribution.

Open the [12-chart PDF](../../figures/revision3/main-approved-checked/SubPSI_revision3_chart_pack.pdf) or the [local chart gallery](../../figures/revision3/main-approved-checked/index.html). The gallery is a local artifact, not a deployed website. Every chart has PNG, PDF, SVG and its exact source CSV. The earlier support-feasibility figure remains in `figures/revision3/feasibility/`.

## What the software actually does

1. It fixes named groups from the data documentation, including combinations such as recorded female sex and Black race. This is the subgrouping step: **declared categories and their intersections**, not a clustering model that discovers groups after seeing attractive results.
2. It compares a historical feature distribution with a later distribution inside each group. PSI compares bin proportions; KS compares cumulative distributions of numeric or ordered values. Neither statistic uses outcome labels in its collection schedule.
3. A shared collector waits until both the reference and incoming group have enough records. Both statistics receive the exact same records and test together; their buffers reset together. Ordinary monitoring instead uses each incoming batch independently. An ordinary-minimum-100 comparison separates the effect of accumulation from the original unequal minimums of 50 and 100.
4. A separate, historically fitted logistic model is audited on separate records. Its accuracy, true-positive rate and false-positive rate answer questions about prediction outcomes, not whether an input-drift detector found a true event.

“Subgroup-decomposed” here means reporting conditional scores for fixed subgroups. The subgroup scores are not claimed to add algebraically to the overall PSI. This is input monitoring; it does not fix a model, infer protected identities, prove discrimination, or automatically establish fairness.

## Real public records and honest time

| Case | Actual records and roles | What can be concluded |
|---|---|---|
| ACS Massachusetts | 348,256 person records across actual 2015–2019 1-Year PUMS files; 289,981 meet the explicit age-16–90 definition. Fit/design/reserved calibration: 2015; reference and separate baseline audit: 2016; monitoring and separate audits: 2017–2019. Roles are split by household within each year. | Descriptive differences in the selected, unweighted records. Not a person panel, causal effect, population estimate or known natural drift event. |
| OULAD BBB | 3,835 eligible distinct-person records in the retained 2013J/2014J pair after day-zero eligibility and later-repeat exclusions. Earlier fit/design/reference/audit roles and later monitoring/audit roles are disjoint. | One later, same-season cohort comparison. Not a long stream with known drift timing. |

ACS features are age and ordered educational-attainment code. The positive label is **ESR=1, civilian employed and at work**, not all employment. OULAD features are previous attempts and studied credits; the positive label is Pass or Distinction, and the negative label combines Fail and Withdrawn. The OULAD task concerns successful completion, not ability.

The original survey weights, replicate weights, allocation flags and identifiers remain in immutable local source files. They were not converted to replicated people. The estimates are explicitly unweighted. Survey clustering, selection, imputation/disclosure processing and cohort selection limit independent-observation assumptions. Consequently **no natural p-values, calibrated drift alerts, drift-detection accuracy, or natural change-point recovery are reported**. Schema, support and label denominators had been inspected before approval; later years are not claimed to be untouched in every respect.

Census records are used with source attribution and no endorsement claim; they are not relabelled as CC0 or MIT. [Census PUMS documentation](https://www.census.gov/programs-surveys/acs/microdata/documentation.html) and [citation guidance](https://www.census.gov/about/policies/citation.html). OULAD is reused under CC BY 4.0, credited to Jakub Kuzilek, Martin Hlosta and Zdenek Zdrahal: [UCI dataset, DOI 10.24432/C5KK69](https://archive.ics.uci.edu/dataset/349/open+university+learning+analytics+dataset) and [dataset paper](https://www.nature.com/articles/sdata2017171). Detailed source, licence, timing and leakage checks remain in `DATA_CARDS.md`.

## Main findings

### Natural records: coverage limits and ties

Only **18/30 ACS views** and **4/9 OULAD views** met the fixed input-support rule. A “view” includes the aggregate, single categories and intersections, so these fractions are not fractions of people covered. The remaining views stay visible as unassessable.

For every supported natural comparison, ordinary and accumulated monitoring used identical blocks and produced identical scores within each statistic. The yearly/cohort batches were already large enough for those groups. Accumulating later records cannot repair an undersized fixed reference. There is therefore **no observed natural accumulation advantage** in this design.

The heatmaps show which selected-record distributions differ more under each statistic. They do not prove that a particular group experienced a real-world harmful change. Raw PSI and KS numbers have different scales; their color bars cannot be compared as if equal numbers meant equal evidence.

### Constructed controls: more assessability, no exact-target recovery

The 120 streams comprise 30 repetitions × two batch sizes × two conditions. Each stream draws a 10,000-record reference and 20 incoming blocks independently with replacement from fixed public-record pools. Repeated draws are explicitly reused source records, not newly collected people. The reference pool contains 15,584 deterministic household representatives from 2016. From delivery block 6, the substitution condition replaces only the fixed target group's draws with whole rows from its 2017 pool. The target contains 512 source representatives in 2016 and 526 in 2017. All labels remain attached to their original rows. Both conditions share the original reference/delivery draws; replacement draws use a separate RNG.

| Records per delivery block | Ordinary ≥100: target ever assessable | Accumulated ≥100: target ever assessable | Mean first assessment with accumulation | Exact-target recovery after substitution |
|---|---:|---:|---:|---:|
| 250 | 0/30 streams | 30/30 streams | Look 12.57 | 0/30 for both statistics |
| 1,000 | 0/30 streams | 30/30 streams | Look 3.57 | 0/30 for both statistics |

Ordinary ≥50 assessed the target in 0/30 streams at batch size 250 and only 1/30 at 1,000. Both PSI and KS inherit precisely the same coverage from the shared scheduler. Target assessment occurred on 5.0% and 26.0% of looks under accumulation. Having enough records once does not mean having continuous coverage.

Across all 30 declared views and 20 looks, mean assessable fractions rose from 18.14% to 20.21% at batch size 250 and from 20.00% to 28.38% at 1,000 when comparing ordinary ≥100 with accumulated ≥100. The paired differences were **2.06 percentage points** (95% conditional bootstrap interval 1.96–2.16) and **8.38 points** (8.31–8.44). These narrow intervals describe repeated draws from these fixed pools, not uncertainty about the wider population. Relative to ordinary ≥50, the gains were smaller: 0.21 and 3.04 points. Mean maximum age of assessed target blocks was 11.57 and 3.00 delivery blocks; these are constructed delivery ages, not calendar time.

Every exact-target substitution miss remains in the delay summaries, with restricted delay 15. Dropping those misses would create a misleading result. A 0/30 rate has a 95% Wilson interval from 0 to **11.35%**; zero observed recovery does not prove mathematical impossibility, and zero null alerts does not prove a zero false-alert probability.

For the full intersection family, unchanged streams produced:

| Batch size | Ordinary ≥50 PSI | Ordinary ≥100 PSI | Accumulated ≥100 PSI | Corresponding KS methods |
|---|---:|---:|---:|---:|
| 250 | 0/30 | 0/30 | 0/30 | 0/30 each |
| 1,000 | 1/30 | 1/30 | 2/30 | 0/30 each |

The accumulated-PSI 2/30 null-alert rate is 6.67%, with a wide 95% Wilson interval of **1.85–21.32%**. Thirty repetitions cannot establish precise calibration or superiority. The nominal .05 budget belongs separately to each method and scope over 20 looks, not to the union of all methods. KS uses the prespecified factor-two combination for missingness and its numeric test, and tied values can make its continuous-null reference conservative. Representation and calibration choices, not extra observations, can therefore affect the comparison.

At 1,000 records, PSI gave one post-substitution alert outside the exact target; it was the same repeat/look/parent-sex schooling alert also present in the paired unchanged stream. This is **not persuasive evidence of intervention recovery**. Aggregate/single/intersection results, pre-intervention alerts, ordinary ≥50 sensitivity, all ties and paired intervals are retained in the full tables.

Post-run integrity diagnostics measured the target source pools' finite-record distances: age PSI 0.01737 / KS 0.04529, schooling PSI 0.03487 / KS 0.04611. These are descriptive diagnostics, not an independently chosen effect-size calibration. No larger shift, new target, alternative seed set or more favorable data period was selected after observing the misses. The experiment does not establish broad detector power under stronger or different changes.

### Prediction outcomes are a different question

The frozen ACS baseline's aggregate held-out accuracy was 74.86% in 2016 and 75.64%, 75.80%, 76.49% in 2017–2019. These are descriptive **model-accuracy** results, not drift-detection accuracy or population-level employment claims.

OULAD accuracy was 58.42% in the earlier audit and 55.60% in the later audit. Its false-positive rate rose from 75.69% to 86.62%; this simple two-feature baseline has poor specificity. A high true-positive rate alone would conceal that limitation. The source CSV preserves all rate numerators/denominators and each group's baseline and later comparison against its complement.

A gap is group rate minus complement rate; a gap change is later gap minus baseline gap. Positive gap change does not automatically mean harm: direction depends on the metric and starting gap. Relevant denominators must each reach 20; unsupported comparisons remain blank with a status. Differences in selected-record gaps do not prove discrimination or a causal effect. The input-versus-outcome scatterplots are descriptive, dependent observations with no fitted association or significance test.

### An important binning limitation, preserved rather than hidden

The approved historical quantile rule requests six finite bins, but ties reduce the effective number. ACS retains six for each feature; OULAD studied credits retains four. OULAD previous attempts produces only two finite intervals, below zero and zero-or-above. All selected finite observations occupy the latter interval, even though their original attempt counts vary. Thus **this frozen PSI representation cannot detect changes among nonnegative attempt counts**; KS still sees the original counts. Unequal sample sizes and smoothing can produce tiny PSI differences even when those finite-bin proportions are identical.

This is an avoidable design-check omission and a limitation of this experiment, not evidence that previous attempts are stable or irrelevant. It was identified after the main run and is explicitly logged. No post-result bin repair or extra main run was used to replace these findings. A future, separately frozen revision should check occupied bins using historical design data and predeclare how discrete counts are binned before inspecting evaluation results.

### Costs and novelty

On eight prespecified identical real-record blocks, PSI's median kernel time was lower in seven cases and higher in one. Those benchmarks use unchanged draws, conservative permutation early stopping and five alternating-order repeats. They are not a universal speed claim. The histogram pair's logical payload is 112 bytes for these ACS features, but the current offline engine also retains input frames, raw IDs, scheduler state and temporary arrays. **112 bytes is not its total memory use.** Profiling separately records temporary allocations; the entire main process reached 300.83 MiB high-water RSS.

The full main run took 323.46 seconds wall time and 416.56 seconds CPU, including loading, the natural study, controls, and the short kernel benchmark. Numerical replay and plotting are additional verification/export costs, recorded separately. No paid compute was used.

Prior-work review found existing subgroup monitoring, temporal fairness audits, KS windows and forgetting mechanisms. Freshness-limited collection is implemented/tested as a shared capability but **was not evaluated as a main contribution**: three later ACS years and one OULAD comparison cannot support the proposed fast-drift/freshness claim. There is no established new algorithm here. The strongest honest result is a matched empirical study showing the distinction between assessability and recovery, reference shortages, representation loss, timing/memory tradeoffs and separate outcome audits.

## What is ready, and what remains the student's work

The code, data-source receipts, configuration and seeds, 120 compressed raw control results, natural score/outcome tables, complete-stream uncertainty tables, scientific figures, verification scripts and change/AI-use records are in the existing NSEF repository on local branch `codex/subpsi-real-data-r3`. New source respondent files and private draw lineage stay in ignored local data directories; reproducible retrieval code and hashes are tracked. This avoids distributing individual records merely to publish charts. Earlier v1/v2 evidence and all preparation deliverables remain unchanged.

There were 78 passing tests after the export fix. Verification checked all 432,000 constructed group-feature-policy opportunities, all Holm decisions, input/lineage/output hashes, natural inference restrictions, and outcome denominators. Four fixed first-stream replays, one from each design cell, reproduced every numerical value, support decision, block hash and alert while excluding runtime measurements. The failed summary attempt and first figure layout are preserved and clearly superseded; no experiments were silently overwritten.

The student and mentor still need to decide the submission framing, understand and defend these limits, write the final submission in the student's own words, document their actual contributions, and complete any applicable fair requirements. This report cannot establish independent student authorship or confirm compliance/approvals not supplied. No submission, deployment, purchase or GitHub push was performed in this revision. The supplied deadline remains 26 October 2026.
