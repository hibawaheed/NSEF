# SubPSI revision 3 — consolidated plan for student and mentor review

**Status: proposed, not approved or frozen. Main evaluation has NOT run.** Prepared with AI assistance on 11 October 2026. Deadline supplied by the student: **26 October 2026**. This is technical planning material, not a final paper or student-authored submission.

## Research question and candidate contribution

When monitoring fixed demographic groups with limited records, what does subgroup-decomposed PSI reveal beyond aggregate monitoring, and how do its results, coverage, waiting time and computational costs compare with KS **when both statistics receive exactly the same observations**?

The candidate contribution is an honest, reproducible empirical comparison with explicit coverage failures, two real public-record case studies, a matched collection scheduler, and separate checks of prediction outcomes. **A new algorithmic contribution is not established.** Subgroup monitoring, KS windows, discarding stale records, and error spending already have substantial prior work. There is no basis yet to claim PSI superiority, fairness repair, or a universal bias detector. See `PRIOR_WORK.md` for methods-level overlap.

## A. Main evidence: natural observational records

### ACS PUMS: Massachusetts, actual survey years 2015–2019

The five official **one-year** person archives are downloaded and hashed. They contain 68,785 / 69,126 / 69,635 / 70,131 / 70,579 records. Massachusetts was chosen before viewing new drift scores, as a manageable single-state case; no state selection by favorable results occurred. Year comes from the official release, never row order or invented dates. These are repeated cross-sections, not a panel of the same identifiable people.

**Task:** an explicitly restricted ACSEmployment-style benchmark: ages **16–90 inclusive**, target **ESR=1** versus other observed ESR codes. That means “civilian employed, at work,” not all employment. ESR=2 (has a job, temporarily absent) is negative under this benchmark definition. The Folktables paper/README describes an age restriction, but the inspected current loader has identity preprocessing; this revision will implement the age rule explicitly and disclose the adaptation. No missing adult ESR was found in these files. This benchmark is not an actual hiring decision.

**Inputs:** AGEP (age) and SCHL (ordered educational attainment) for the primary matched PSI/KS comparison. KS uses educational order, not distances between nominal category codes. Model: a small, frozen logistic baseline with historical-only scaling of age and age squared, one-hot SCHL, regularization C=1, threshold 0.5, no search over models. This intentionally restricted baseline is for outcome auditing, not a claim to state-of-the-art employment prediction. ESR, work status/hours/income, identifiers and allocation flags are not predictors. The 2019 RELP→RELSHIPP schema change is recorded; neither is used.

**Groups:** Everyone; each of the two recorded SEX categories; each of all nine RAC1P categories; all 18 intersections. Total **30 views**, fixed from documentation. Use the recorded term “sex,” preserve full multicategory race coding, and do not merge rare categories into an invented binary group. Unexpected/missing grouping codes require an explicit recorded handling decision, not silent exclusion. Missing feature values get a separate PSI bin and a separate KS missing-rate channel. New feature categories get an unknown bin in any later nominal analysis.

**Roles:** deterministic whole-household allocation using year+SERIALNO and seed string `r3-role-31721`; person key adds SPORDER. Proposed splits, already inspected only for support:

| Year | Proposed roles and actual record counts |
|---|---|
| 2015 | fit 28,389; bin design 14,320; historical calibration/diagnostics 14,422 |
| 2016 | reference 28,590; independent outcome audit baseline 28,813 |
| 2017 | monitor 28,500; outcome audit 29,306 |
| 2018 | monitor 29,274; outcome audit 29,228 |
| 2019 | monitor 29,570; outcome audit 29,569 |

Bins, model preprocessing and all settings use historical data only. Later-year inspection so far has been limited to schema, keys, group/label-denominator counts, missingness and allocation flags; those years are **not untouched in every sense**. No new feature drift, model accuracy or subgroup outcome gaps have been inspected. The later three annual comparisons remain held out for those endpoints. Household keys cannot establish cross-year person independence; no re-identification or record linkage will be attempted.

**Feasibility finding:** 18/30 views meet both 50- and 100-record reference thresholds. Twelve do not. Every supported later annual group already exceeds 100 records. Thus ordinary and accumulated schedules are expected to tie for assessable natural groups; accumulation cannot repair an undersized fixed reference. Preserve this limitation. Do not tune support thresholds to create a benefit.

**Estimand:** unweighted selected-record distributions and prediction metrics. These are not estimates of Massachusetts population employment or demographic disparities. Retain PWGTP, all 80 replicate weights, allocation flags and household keys locally. No expansion of weights into duplicate people. Survey-weighted population inference would require a separate design and uncertainty calculation and is outside this compact revision.

Sources: [Census PUMS documentation](https://www.census.gov/programs-surveys/acs/microdata/documentation.html), [2019 sampling/accuracy document](https://www2.census.gov/programs-surveys/acs/tech_docs/pums/accuracy/2019AccuracyPUMS.pdf), [Folktables](https://github.com/socialfoundations/folktables), [Ding et al.](https://arxiv.org/abs/2108.04884). Exact dictionaries, archive hashes, access times and schema checks are recorded in `DATA_CARDS.md` and the feasibility manifests.

### OULAD: a compact, same-season cohort case study

The prespecified rule chose **BBB**, the alphabetically first module with at least 500 enrolments in both **2013J and 2014J**. J denotes the October presentation. Source tables contain 32,593 enrolment rows but only **28,785 distinct student identifiers**; enrolments are not independent unique people by default.

The selected pair contains 4,529 enrolments. At **day 0**, retain students registered by course start and not already withdrawn. Exclude unknown registration dates; do not impute them. Then exclude later-cohort students appearing in the earlier cohort, regardless of earlier outcomes. This removes 650 start-ineligible rows and 44 eligible later repeat rows, leaving **1,883 in 2013J and 1,952 in 2014J**. There were 47 overlapping student IDs before eligibility filtering. UCI uses `?` for missing dates; this is now explicitly parsed. Join keys are module+presentation+student, with uniqueness checks.

**Groups:** Everyone, recorded gender F/M, disability N/Y, and all four intersections: **9 views**. **Features:** number of previous attempts and studied credits, available at start. **Label:** Pass or Distinction = 1; Fail or Withdrawn = 0. This is eventual successful completion, not “ability.” No final_result, future assessments, withdrawal timing after day 0, or VLE events enter predictors. No click rows are treated as people.

**Roles:** seed string `r3-oulad-31721`, student-based. 2013J: fit 757, design 372, reference 362, audit 392. 2014J: monitor 979, audit 973. Same simple logistic baseline, C=1, frozen threshold 0.5, historical scaling of the two numeric features. Only **4/9 reference views** meet either 50 or 100 observations; others remain unassessable. Class denominators are smaller still. This is an intentionally small secondary case study, with one later cohort. It cannot validate long-stream monitoring, seasonal generality or calendar-time detection delay.

Sources: [UCI OULAD and CC BY 4.0 licence](https://archive.ics.uci.edu/dataset/349/open+university+learning+analytics+dataset), [Kuzilek et al. data paper](https://www.nature.com/articles/sdata2017171). Only the required original ZIP members were extracted with size/CRC checks and SHA-256 hashes; source bytes are preserved. The large click-log download was stopped after the compact tables were verified.

## Comparisons, support and statistics

Keep subgroup-decomposed PSI as the core. For each dataset, report aggregate, single-attribute and intersection scopes for **ordinary PSI / ordinary KS**, then the corresponding **accumulated PSI / accumulated KS**. This separates the effects of statistic, grouping and collection policy. Six-bin historical quantiles plus missing bin; PSI pseudocount 0.5. Ordinary minimum 50 and accumulated minimum 100 on **both** sides, as in v2. Add an ordinary-minimum-100 sensitivity comparison to separate accumulation from the unequal minimum counts; label it explicitly, do not select the better setting after seeing results.

The shared scheduler uses only membership, count and declared time. Both statistics consume whole identical batches, test on the same boundaries, and reset together after a supported block even when neither alerts. They receive the same reference and current records. All declared unsupported tests remain in the family. No value-based collection, extra KS observations or dropped hard groups. Numeric and ordered features are matched; nominal features are PSI-only and cannot be presented as matched KS comparisons.

**Natural data (A) are descriptive.** Household clustering, survey selection/weights, imputation, disclosure protection and cohort selection prevent us from automatically asserting the independent/exchangeable null needed by row-wise permutation or exact KS. Default output has PSI scores, KS ECDF distance and missing-rate difference, but no inferential p-values or statistical alerts. Do not call arbitrary threshold crossings calibrated detection. Report changes and concordance/disagreement in the scores, plus support and costs. There is no known natural onset or affected-group truth, so do not report drift-detection accuracy, power, sensitivity or false-positive rate on these records.

Outcome audit: frozen-model TPR, FPR and accuracy with positive/negative/total denominators; minimum 20 for each relevant class denominator. Show both baseline gaps and changes in gaps, using disjoint audit roles. For each single attribute, predeclared category-versus-complement comparisons; for intersections, each cell versus its complement. Retain undefined/unsupported metrics. No causal discrimination or repair conclusion. Inputs and outcomes may disagree. Natural differences are descriptive; avoid fake confidence intervals from repeatedly repartitioning the same few years/cohorts. A label audit is not ground truth for input drift.

## B. Separate constructed delivery/resampling controls

After approval, propose **120 conditional streams**: two batch sizes (250, 1,000) × two conditions × 30 fixed seeds, 20 delivery blocks each. These use genuine whole ACS records, not generated replacement feature values. The horizontal axis is **constructed delivery index**, never calendar days or survey collection order.

Use the fixed 2016 reference-role pool, one deterministic selected adult per household, to reduce within-draw household duplication. Draw a new 10,000-record reference and current records independently with replacement for each stream. Reuse of source people across draws/streams is explicit; draw IDs are distinct and privately map to original source keys. Under the constructed unchanged condition, these draws are conditionally independent from the same finite empirical distribution; this is the justification for conditional row-label exchangeability, not a claim that the original survey respondents were i.i.d.

Second condition: from delivery block 6, replace only draws belonging to the **prespecified SEX=2, RAC1P=2 intersection** with whole records from the same group's 2017 monitor-role pool. Keep labels attached, preserve group counts and all other draws, and give both methods identical records. This is an imposed source-pool substitution. Its effect may be weak or undetectable; it is not a discovered historical event. Ground truth is the intervention in sampling, not a guarantee of a particular distribution-distance magnitude. This uses no later-year outcomes to choose the target or strength. Freeze exact seed list and pool lineage after plan approval before running it.

Equal standalone method budget **alpha=.05 over H=20**; Holm across all declared group×feature comparisons at each look, cutoff alpha/H. For 30 views×2 features, the smallest first-Holm cutoff is .05/(20×60), so PSI needs **at least 23,999 permutations** with plus-one p-values. Use 23,999, inclusive ties and conservative early termination; do not reuse the insufficient v2 budget of 15,999 for this family. KS combines nonmissing KS and missingness Fisher at a fixed factor of two. SciPy fallback warnings are retained with conservative p=1. Methods/scopes are separate comparators; their union is not a new .05-guaranteed monitor. There is no combined input/outcome alarm in this compact plan.

Report whole-stream null alerts, intervention-recovery alerts (any view and exact declared target), pre-intervention alerts, support fraction, waiting until assessment, restricted delay including missed interventions, records/age at testing, and costs. Estimate uncertainty across **complete conditional streams**, pairing methods on the same streams (Wilson intervals for proportions; 2,000 paired stream-bootstrap draws for differences). Label these conditional finite-pool Monte Carlo intervals, not confidence about newly collected people. Thirty repetitions give imprecise rates; do not oversell small differences or degenerate ties.

## C. Existing simulations: validation only

Preserve v1/v2 files and negative findings. Three preselected v2 streams have been regenerated for implementation checks, using original generators/configuration/seeds: null_n250, grid_n250_s0.05_m1.4 and correlation, repeat 0. All accumulation counts, eligibility, start boundaries, PSI values and PSI alert groups matched. KS receives the same blocks. These **720 group-feature opportunities are software validation**, not a new main simulation study, new human data, or an estimate of comparative superiority. No expanded synthetic grid is proposed.

## Freshness hypothesis and novelty boundary

The scheduler has a mechanically tested optional inclusive calendar-age cap: retain records with time >= current time minus cap; record oldest/newest time and discarded count. Expiration does not restart waiting or error-budget spending, and both statistics share the same expiration. This is implementation capability, not validated improvement.

**Omit freshness as a main evaluated contribution for these datasets.** ACS offers only three held-out yearly looks and reference shortages already block the smallest groups; OULAD has only one later same-season cohort. Neither supports a persuasive claim about fast drift or a freshness/power frontier. Do not manufacture extra dates or tune an age limit on outcomes. If a future study supplies adequate real periods, compare fixed-age rolling windows against bounded-age accumulation for both statistics under the same support/error budget. That would require a revised approved plan. Existing ADWIN, KSWIN and FairFedDrift windowing make “forget old records” insufficient novelty on its own.

## Figures and reproducibility

One completed **feasibility** figure currently shows every declared intersection and its actual reference/later counts. It proves only which comparisons have enough records under the proposed split. Source CSV, SVG, PDF, 300 dpi PNG and manifest are in `figures/revision3/feasibility/`.

After approved main runs, a compact figure set will cover: (1) source periods and support; (2) natural PSI/KS scores by all declared views; (3) matched collection coverage and test costs; (4) waiting, sample ages and missed assessments; (5) frozen-model subgroup outcomes and denominators; (6) input/outcome agreement and uncertainty/unsupported cases; (7) clearly separated constructed controls. No best-looking-only selection. Preserve ties, no-change findings and excluded/unassessable groups. Existing simulation charts keep their original labels.

Each export must have its exact source CSV, source-record/configuration/role hashes, code commit and changed-source snapshot if relevant, seed list, software versions, runtime and plot-code hash. Raw original archives/member bytes are immutable and kept local. Private identifiers/lineage are not public chart exports. Use new directories; fail on existing output directories. Record failures instead of silently replacing runs. Final tables should say which metrics are descriptive and which carry justified conditional uncertainty.

Memory: report logical PSI histogram payload versus KS raw-value payload separately from actual measured allocation peaks and shared scheduler/input overhead. The current offline engine retains all input frames and ID bookkeeping; it is **not a histogram-only production streaming implementation**. Per-test profiling excludes setup; engine peak/RSS includes broader work. Do not infer end-to-end memory savings from histogram bytes alone. Runtime reports separate loading/setup, collection, tests, audit and plotting on the same machine; alternate statistic timing order.

## Compute, milestones and approval

Measured software replay: three streams, 3.95 seconds total on the current machine, about 159 MiB peak process RSS (whole validation process; instrumented). ACS schema inspection loads one yearly file at a time. Based on this pilot, budget **10–30 minutes CPU for 120 constructed streams**, **under 10 minutes for natural descriptions/model audits**, and **under 2 GiB working memory** with selected-column loading. These are estimates, not measured main-run costs; source download latency is separate. Set a two-hour local compute cap and record/report any overrun rather than enlarging the study or buying compute.

| Date | Proposed work |
|---|---|
| 11–13 October | mentor/student review of this one plan; freeze accepted config/roles/seeds |
| 14–17 October | implement remaining dataset runners/model/audit/export plumbing; run approved natural and constructed studies |
| 18–20 October | verify every result, uncertainty and provenance; freeze main tables/figures by **20 October** |
| 21–25 October | student interpretation/writing, mentor review, explanations and presentation practice; no unplanned experiment expansion |
| 26 October | student-controlled submission deadline; no submission by the assistant |

**Approval requested:** approve this specific scope (including the explicit ACS task definition, sparse OULAD case, descriptive natural inference, 120 separate constructed streams and no main freshness claim), or identify changes with the mentor. Main evaluation/configuration freeze remains paused until approval. Local implementation checks may continue. Pushing, deploying, submitting or purchases each require separate permission.
