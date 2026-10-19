"""Generate measured handoff and claim ledger from saved tables; no new study."""
from common import *
import csv
S=ROOT/'results/summary/low_compute/2026-10-18';R=ROOT/'records/low_compute/2026-10-18'
summary=pd.read_csv(S/'cost_summary.csv');eq=pd.read_csv(S/'equivalence.csv');conditions=pd.read_csv(S/'condition_timings.csv')
def row(v,m,w='primary'):return summary.loc[(summary.variant==v)&(summary.metric==m)&(summary.workload==w)].iloc[0]
def v(a,m,w='primary'):return row(a,m,w)['median']
labels={'A':'Faithful original PSI-only','B':'Count-reuse PSI','C':'Matched KS-only','D':'Aggregate PSI (less scope)'}
lines=['| Implementation | CPU seconds, median [min-max] | Wall seconds, median | Peak RAM, median MiB |','|---|---:|---:|---:|']
for a in 'ABCD':
 c=row(a,'complete_cpu');lines.append(f"| {labels[a]} | {c['median']:.2f} [{c.minimum:.2f}-{c.maximum:.2f}] | {v(a,'complete_wall'):.2f} | {v(a,'peak_rss_mib'):.2f} |")
cpu=100*(1-v('B','complete_cpu')/v('A','complete_cpu'));wall=100*(1-v('B','complete_wall')/v('A','complete_wall'));ram=v('A','peak_rss_mib')-v('B','peak_rss_mib')
strong=conditions.loc[conditions.condition=='age_up4'].groupby('variant').elapsed_cpu.median();strongextra=100*(strong.B/strong.C-1)
text=f'''# Low-compute findings - local engineering addendum, 19 October 2026

Registered title unchanged: **SubPSI: Detecting Hidden Bias Drift in Machine Learning Through Subgroup-Decomposed Population Stability Analysis.**

This is AI-generated technical evidence for discussion and the student's own writing, not a final submission in the student's voice. The session began 18 October and crossed midnight. The earlier scientific results remain frozen; this explicitly requested implementation addendum is dated honestly. Deadline: 26 October 2026.

## What changed

The new PSI path counts the fixed reference once, turns each incoming feature into bin codes once per batch, reuses group memberships, and adds integer counts across complete batches. It applies the original smoothing and statistical test when the original collection rule says a group is ready. It can read and write a batch at a time. It does less repeated copying and searching through tables.

The original implementation remains usable and unchanged. This improvement is beside it on local branch `codex/subpsi-low-compute-20261018`. The benchmarked implementation and tests are committed at `0ca3134`; all exact file hashes are in the [execution manifest](records/low_compute/2026-10-18/benchmark_execution_manifest.json). No push, merge, deployment, purchase, email or submission was performed in this pass.

## What stayed identical

Twenty fixed-100 saved runs and four fixed-400 runs were compared with Version 4. All **{int(eq.feature_rows.sum()):,} declared feature comparisons** matched: reference/current integer histograms, support, collection boundaries, PSI scores, permutation seed/draw hashes and extreme counts, stopping, p-values, Holm-adjusted values, hits and first alerts. There were **{int(eq.assessed_tests.sum()):,} assessed tests** and **{int(eq.permutation_draws.sum()):,} actual permutation draws** in that trace check. Maximum PSI difference was **zero**. KS outputs matched too. Unsupported tests remained present.

The corrected OULAD replay also matched all 54 descriptive feature rows exactly across its three existing policies, using the same 0 / 1 / 2+ attempt bins. An initial comparison exposed pandas' default CSV float parsing (difference under 1e-16); reading the saved decimals with round-trip precision recovered exact equality. No tolerance was relaxed and no model was refitted. All **137 Python tests** passed; the browser-core test also passed during this session.

This checks selected replays, not every one of the 220 historical streams. Timing repetitions are not additional detection trials.

## What was actually measured

Each row below covers the same 20-stream, four-condition workload: 20 batches of 1,000 incoming records and a 10,000-record reference per stream. One warm-up was excluded, followed by five alternating-order technical repeats in fresh processes on this machine. Complete execution includes imports, loading, exact ID checks, setup, monitoring and scientific-output writing. Original source preparation and old calibration/model fitting are separate costs.

{chr(10).join(lines)}

Compared with the faithful PSI-only baseline, count-reuse PSI used **{cpu:.1f}% less complete CPU time** and **{wall:.1f}% less wall time** by these medians. Monitoring-only CPU was {v('A','monitoring_cpu'):.2f} versus {v('B','monitoring_cpu'):.2f} seconds. Complete throughput increased from about {v('A','complete_throughput'):,.0f} to {v('B','complete_throughput'):,.0f} incoming records per second.

Peak RAM improved by only **{ram:.2f} MiB ({100*ram/v('A','peak_rss_mib'):.1f}%)** on the primary workload. The 10-batch prefix used **{v('B','peak_rss_mib','prefix10')-v('A','peak_rss_mib','prefix10'):.2f} MiB more** with optimized PSI. There is no uniform or large RAM-saving claim. The histogram arrays occupy 6,720 bytes, but the detector's Python objects occupy about 30 KiB, the retained exact-ID audit about 4.6 MiB at a full stream's end, and the full process about 139 MiB. Those are different quantities, not interchangeable system requirements.

KS was faster in the strongest-change subset: optimized PSI used {strong.B:.3f} versus KS {strong.C:.3f} CPU seconds for five streams, about {strongextra:.1f}% more (imports excluded from this condition subtotal). PSI was cheaper on the balanced workload median, not universally cheaper. Aggregate PSI was much cheaper because it checks only Everyone; it cannot replace the subgroup method's scope. Technical timing ranges overlap in some comparisons and are not confidence intervals across machines.

The smaller fixed-400 check and both prefix checks are retained in [all cost summaries](results/summary/low_compute/2026-10-18/cost_summary.csv), including unfavorable memory results. Per-condition timing, per-batch latency and all raw repeats are available beside it. No conditions, permutations or hard tests were dropped.

## Which three figure groups to use

1. [Runtime and throughput](figures/low_compute/final/01_runtime.pdf): shows the measured compute saving and labels aggregate PSI's smaller scope.
2. [Measured RAM and separate state accounting](figures/low_compute/final/02_memory.pdf): shows why tiny histogram arrays do not mean a tiny complete system.
3. [Equivalence and retained scientific trade-offs](figures/low_compute/final/03_equivalence_and_tradeoff.pdf): separates the new exact replay check from old detection, false-alert, coverage and waiting results, including the failed 800-record policies.

Each has an exact same-name source CSV, 300-dpi PNG and vector SVG. Use `figures/low_compute/final`; the earlier layout is preserved. These are full-width figures, not narrow-column miniatures.

## What to explain to a mentor

The defensible claim is an implementation improvement with identical results on the tested replays. Histogram reuse is not a new statistical invention. Exact duplicate-ID auditing remains in RAM and grows with the stream; this is not constant total memory. Source preparation, calibration and training costs are not hidden inside the monitor-only claim. CPU time is not measured energy use or a deployment guarantee.

The historical scientific limitations remain: the 800 targets failed their criterion and never assessed the target, PSI did not dominate KS, and the frozen OULAD predictor performed worse in ordinary accuracy than the training-majority baseline. Actual ACS/OULAD observations remain descriptive; constructed resampling is not new people or natural drift-detection accuracy. The registered title does not establish mentor/fair procedural approval.

See the [claim-to-evidence ledger](docs/low_compute/CLAIM_EVIDENCE.csv), [method and limits](docs/low_compute/METHOD_AND_LIMITS.md), [reproduction notes](docs/low_compute/REPRODUCE.md), and [AI/change log](records/low_compute/2026-10-18/WORK_LOG.md). The bounded pass is complete; development stops here so the next stage can be the paper.
'''
(ROOT/'LOW_COMPUTE_FINDINGS.md').write_text(text)
claims=[
 ('LC01',f'Primary complete CPU median lower by {cpu:.1f}% versus faithful PSI-only baseline','demonstrated on bounded workload','results/summary/low_compute/2026-10-18/process_measurements.csv','figures/low_compute/final/01_runtime.csv','Five technical repeats; one machine; not joint PSI+KS baseline'),
 ('LC02',f'Primary peak RSS median lower by {ram:.2f} MiB; prefix10 optimized RSS higher','limited and mixed','results/summary/low_compute/2026-10-18/cost_summary.csv','figures/low_compute/final/02_memory.csv','No large or uniform RAM-saving claim; RSS includes process/runtime'),
 ('LC03','24 saved comparisons reproduce all 28800 declared PSI feature rows and actual RNG traces exactly','verified subset','results/raw/low_compute/2026-10-18/equivalence/summary.csv','figures/low_compute/final/03_equivalence_and_tradeoff.csv','Not all 220 streams; exact checks do not prove assumptions/statistical validity'),
 ('LC04','Matched KS outputs reproduce saved KS behavior on the same 24 replays','verified subset','results/raw/low_compute/2026-10-18/equivalence/completion.json','','Nominal budget equal, realized sensitivity/false alerts differ'),
 ('LC05','KS has lower measured CPU in strongest-change subset','retained unfavorable comparison','results/summary/low_compute/2026-10-18/condition_timings.csv','','Five-stream condition subtotals exclude process imports; technical ranges not independent-machine inference'),
 ('LC06','6720 histogram bytes coexist with growing ID audit and about 139 MiB peak process RAM','measured separate quantities','results/summary/low_compute/2026-10-18/stream_measurements.csv','figures/low_compute/final/02_memory.csv','Object accounting is not RSS; no constant-total-memory or 112-byte headline'),
 ('LC07','Corrected natural OULAD scores reproduce 54 rows exactly; no natural alarms','descriptive replay only','results/raw/low_compute/2026-10-18/oulad_equivalence.json','','Round-trip CSV reading; unchanged bins/classifier; no untouched-validation claim'),
 ('LC08','Historical fixed-100 detection varies by direction: PSI39/40 vs KS40/40 for strong upward change','historical context, not new trials','results/summary/revision4/main-approved/rates.csv','figures/low_compute/final/03_equivalence_and_tradeoff.csv','Historical statistical code 1b1509e; optimized checks cover selected 20 fixed100 streams only'),
 ('LC09','Calibrated policies fell back to800 and the target never became assessable','preserved negative finding','results/summary/revision4/main-approved/coverage.csv','figures/low_compute/final/03_equivalence_and_tradeoff.csv','No recalibration, threshold tuning or replacement of failed policies'),
 ('LC10','Aggregate PSI has lower cost while checking only Everyone','lower-scope cost reference','results/summary/low_compute/2026-10-18/process_measurements.csv','figures/low_compute/final/01_runtime.csv','Two feature tests rather than60; not equal subgroup monitoring scope'),
 ('LC11','Energy saving, battery life or deployment suitability','unsupported','docs/low_compute/METHOD_AND_LIMITS.md','','No energy instrumentation or deployment study'),
 ('LC12','New PSI theorem or new statistical detector','unsupported','src/subpsi/low_compute.py','','Caching/count reuse is engineering; existing statistical tests unchanged'),
 ('LC13','Original baseline spends substantial time in repeated DataFrame selection and count testing','profiled diagnostic','results/raw/low_compute/2026-10-18/profile/functions.csv','','Four fixed first streams; cumulative profile times are nested, not additive')]
with (ROOT/'docs/low_compute/CLAIM_EVIDENCE.csv').open('w') as h:
 w=csv.writer(h);w.writerow(['claim_id','claim','status','source','source_sha256','figure_csv','configuration','configuration_sha256','implementation_commit','limitations'])
 for ident,claim,status,source,figure,limit in claims:w.writerow([ident,claim,status,source,sha256(ROOT/source),figure,'configs/low_compute/benchmark.json',sha256(CONFIG),'0ca3134',limit])
print('Wrote measured findings and 13 explicit claim/evidence entries.')
