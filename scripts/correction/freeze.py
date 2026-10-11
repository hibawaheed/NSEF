"""Create an immutable, verified evidence index; never choose a final submission."""
from datetime import datetime,timezone
import json,subprocess,sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from subpsi.correction import read_table
from subpsi.provenance import sha256,write_json


def main():
    target=ROOT/'records/correction/FREEZE.json'
    if target.exists():raise ValueError('Frozen set already exists; a later change requires a new revision')
    verification=json.loads((ROOT/'records/correction/verification.json').read_text())
    if verification['status']!='PASS':raise ValueError('Unverified evidence')
    for name,digest in verification['verified_manifests'].items():
        if sha256(ROOT/name)!=digest:raise ValueError('Evidence changed after verification: '+name)
    cfg='configs/correction/frozen.json';v2cfg='configs/revision2.json';v3cfg='configs/revision3/approved.json'
    ou='results/raw/correction/oulad';summary='results/summary/correction';v2='results/raw/correction/v2-matched'
    om=json.loads((ROOT/ou/'manifest.json').read_text());vm=json.loads((ROOT/v2/'manifest.json').read_text())
    original_main=json.loads((ROOT/'results/raw/revision3/main-approved/manifest.json').read_text())
    claims=[]
    def add(cid,statement,table,selector,fields,code,configuration=cfg,interpretation=''):
        d=read_table(ROOT/table);selected=d.query(selector) if selector else d
        if selected.empty:raise ValueError('Empty claim source: '+cid)
        rows=json.loads(selected[fields].to_json(orient='records',double_precision=15))
        claims.append({'claim_id':cid,'statement':statement,'source_table':table,'source_sha256':sha256(ROOT/table),
                       'selector_pandas_query':selector,'values':rows,'configuration':configuration,
                       'configuration_sha256':sha256(ROOT/configuration),'numerical_code_commit':code,
                       'interpretation':interpretation})
    add('O1','Historical design counts justify 0 / 1 / 2+ bins; original rule collapsed all nonnegative counts.',
        ou+'/bin_counts.csv',"period=='design_2013J' and group=='Everyone' and feature=='num_of_prev_attempts'",
        ['version','bin','label','count'],om['git_head'],interpretation='Post-result repair; design-only rule selection; sparse tail remains.')
    add('O2','Overall previous-attempts PSI changes from 0.001721 to 0.029233; KS stays 0.044566.',
        ou+'/old_vs_corrected.csv',"variant=='accum100' and group=='Everyone' and feature=='num_of_prev_attempts'",
        ['psi_old','psi_new','ks_d_old','ks_d_new','n_reference_new','n_current_new'],om['git_head'],interpretation='Descriptive distance; no true drift onset, significance or detection accuracy claim.')
    add('O3','Four of nine OULAD group views remain assessable; five retain insufficient reference support.',
        ou+'/old_vs_corrected.csv',"variant=='accum100' and feature=='num_of_prev_attempts'",
        ['group','eligible_new','n_reference_new','n_current_new'],om['git_head'])
    add('O4','Later logistic accuracy is 541/973; training-majority accuracy is 547/973. Earlier logistic accuracy exceeds the baseline.',
        ou+'/outcomes.csv',"group=='Everyone' and metric=='Accuracy'",
        ['model','baseline_numerator','baseline_denominator','baseline_rate','current_numerator','current_denominator','current_rate'],om['git_head'],
        interpretation='No retraining or search; no claim that the six-record accuracy difference is statistically significant.')
    add('O5','The all-positive baseline has both TPR and FPR equal to 100%; a zero rate gap does not establish fairness.',
        ou+'/outcomes.csv',"group=='Everyone' and metric!='Accuracy'",
        ['model','metric','current_numerator','current_denominator','current_rate'],om['git_head'])
    add('O6','The corrected bins expose the observed count proportions: zero previous attempts occurs in 310/362 reference records and 882/979 monitoring records.',
        ou+'/bin_counts.csv',"version=='corrected' and group=='Everyone' and feature=='num_of_prev_attempts' and period!='design_2013J'",
        ['period','label','count'],om['git_head'],interpretation='Natural cohort comparison; no independent ground truth for drift or causal explanation.')
    add('S1','Matched synthetic grid comparison gives both methods the original records, support and standalone error budget.',
        summary+'/benchmark_aggregate.csv',"kind=='shift' and metric=='post_alert'",
        ['n','method','successes','n_streams','estimate','low','high','interval'],vm['git_head'],interpretation='Retrospective comparison on mathematical simulations. Grid averages weight all 12 fixed cells equally; any alert is not exact localization.')
    add('S2','Synthetic null alert rates must be reported alongside detection, including uncertainty.',
        summary+'/benchmark_aggregate.csv',"kind=='null'",
        ['n','method','successes','n_streams','estimate','low','high','interval'],vm['git_head'],interpretation='Standalone methods; union not guaranteed at 5%. Observed rates do not certify a universal error bound.')
    add('S3','Revisit both the 5% and 2% target examples behind the original Version 2 accumulation claim.',
        summary+'/all_cells.csv',"id in ['grid_n250_s0.05_m1.4','grid_n250_s0.02_m1.4'] and metric in ['target_detected','target_ever_assessed','target_restricted_delay','target_first_assessment_restricted']",
        ['id','method','metric','estimate','successes','n_streams','low','high'],vm['git_head'],interpretation='Prespecified historical examples, not a search for favorable cases; all weaker shifts, other shares and batch sizes remain in tables.')
    add('S4','Across all 35 cases, show the paired detection, coverage, waiting and delay differences, including ties.',
        summary+'/paired_cells.csv',"metric in ['post_alert','target_detected','eligible_fraction','target_first_assessment_restricted','target_restricted_delay']",
        ['id','metric','difference','low','high','degenerate','n_pairs'],vm['git_head'],interpretation='Pointwise paired simulation intervals, not simultaneous significance claims. Degenerate intervals can arise from identical observed pairs.')
    add('R1','The original real-record substitution controls did not recover the exact target in any of 30 streams per batch size for either accumulated method.',
        'results/summary/revision3/main-approved-checked/control_proportions.csv',"condition=='substitution' and variant=='accum100' and scope=='intersection' and metric=='target_post_alert'",
        ['batch_n','method','successes','n','estimate','low','high'],original_main['git_head'],v3cfg,
        interpretation='Constructed real-record resampling controls, not natural chronology or generated people. Preserved unchanged; no corrected OULAD result rescues this negative result.')
    add('C1','Same-block cost checks separate test allocations and payload from total monitor memory.',
        'results/raw/correction/cost-check/costs.csv','',
        ['run','selection','method','repeat','order_position','n_reference','n_current','seconds','python_peak_allocated_bytes','logical_payload_bytes'],
        json.loads((ROOT/'results/raw/correction/cost-check/manifest.json').read_text())['git_head'],interpretation='Six alternating-order repeats per fixed block, timed separately from allocation tracing. No universal speed or total-memory superiority claim.')
    ledger=ROOT/'docs/correction/CLAIM_EVIDENCE.json';write_json(ledger,claims)
    pd.DataFrame([{**{k:v for k,v in c.items() if k!='values'},'values_json':json.dumps(c['values'],separators=(',',':'))} for c in claims]).to_csv(ROOT/'docs/correction/CLAIM_EVIDENCE.csv',index=False)
    index=['# Claim-to-evidence record','', 'AI-generated evidence index for review. This is not the student’s final results section. JSON/CSV contain exact selections, values, source hashes, configuration hashes and numerical execution commits.','',
           '| ID | Claim and interpretation | Source |','|---|---|---|']
    for c in claims:
        index.append(f'| {c["claim_id"]} | {c["statement"]} {c["interpretation"]} | [{Path(c["source_table"]).name}](../../{c["source_table"]}) |')
    (ROOT/'docs/correction/CLAIM_EVIDENCE.md').write_text('\n'.join(index)+'\n')
    a=read_table(ROOT/summary/'benchmark_aggregate.csv');cell=read_table(ROOT/summary/'all_cells.csv')
    def row(n,kind,method,metric):return a[a.n.eq(n)&a.kind.eq(kind)&a.method.eq(method)&a.metric.eq(metric)].iloc[0]
    report=['# Bounded correction completed — evidence for review','',
            '**Status: corrected results frozen locally; original Versions 1, 2 and 3 preserved. This is post-result work, not untouched validation. The final project version has not been selected.**','',
            'The OULAD previous-attempts histogram now distinguishes zero, one and two-or-more attempts. Its rule uses only the 372 historical design records (314 / 45 / 13). The sparse tail remains a limitation. Overall PSI changes from 0.001721 to 0.029233; KS remains 0.044566. The original small PSI was driven by smoothing unequal sample sizes across empty bins, because all valid counts fell in one occupied bin. A larger corrected distance demonstrates a repaired measurement, not better prediction, proven harm, or natural drift-detection accuracy.','',
            'The same four of nine OULAD group views qualify. The five unsupported groups stay visible. Credits, the cohorts, student splits, labels, groups, thresholds and logistic parameters are unchanged.','',
            'For example, zero prior attempts accounts for **310/362** reference students and **882/979** monitored students. The old bins could not represent this difference in proportions. The corrected count table shows it directly, without turning it into a known-change detection claim.','',
            'The simple predictor is fixed from 438 positive versus 319 negative historical training labels: always predict Pass/Distinction. On the later audit, the frozen logistic model correctly predicts **541/973 (55.60%)** versus **547/973 (56.22%)** for this baseline. On the earlier audit, logistic gets **229/392** versus **211/392**. The six-record later difference is descriptive, not a significance claim. Both TPR and FPR are 100% for an all-positive predictor; this is not a useful claim of fairness. No classifier search or retraining was performed.','',
            '## Matched Version 2 comparison','',
            f'All **{vm["runs"]:,} original synthetic streams** completed. Every original PSI score, support decision, block start and alert-group set passed the replay checks. Both statistics use the same complete blocks and alpha/20 budget with a fixed Holm family. No extra observations were given to either method. This is a retrospective comparison on the old benchmark, not a new prospectively untouched study.','',
            '| Batch size | Accumulated PSI: grid alerts | Accumulated KS: grid alerts | PSI null alerts | KS null alerts |','|---|---:|---:|---:|---:|']
    for n in [250,1000]:
        vals=[row(n,k,m,metric) for k,m,metric in [('shift','PSI','post_alert'),('shift','KS','post_alert'),('null','PSI','stream_alert'),('null','KS','stream_alert')]]
        report.append(f'| {n} | '+' | '.join(f'{int(r.successes)}/{r.n_streams} ({r.estimate:.1%})' for r in vals)+' |')
    report += ['', 'On the completed shift grid, accumulated KS has more observed post-onset alerts at both batch sizes. This does not establish universal superiority; false alerts, exact localization, support and delay must also be read alongside it. The old PSI counts are reproduced, rather than replaced.','',
               'Grid denominators give equal weight to the original 12 settings per batch size. Any alert is not exact target identification. The source table contains stratified paired bootstrap intervals; null rates have Wilson intervals. The methods are separate 5% monitors, not a combined 5% PSI-or-KS rule.','']
    for share in [.05,.02]:
        part=cell[cell.id.eq(f'grid_n250_s{share}_m1.4')]
        lines=[]
        for method in ['PSI','KS']:
            p=part[part.method.eq(method)].set_index('metric');det=p.loc['target_detected'];delay=p.loc['target_restricted_delay']
            lines.append(f'{method}: {int(det.successes)}/40 exact target alerts; restricted mean delay {delay.estimate:.3f} batches')
        report.append(f'- Original {share:.0%}-target, n=250, 1.4-SD example: '+ '; '.join(lines)+'.')
    report += ['', 'Misses count as 15 batches in restricted delay. Support and waiting are identical between statistics because collection is shared. All 35 cases, including nulls, cancellation, gradual changes, missingness, benign shifts, outcome-only changes, composition and correlation, remain in the tables. None were removed for an unattractive result.','',
               'The added comparison addresses the missing comparator behind the old accumulation claim. Any benefit of pooling more observations should be credited to the shared collection policy unless a matched statistic comparison supports something narrower. **No new algorithmic novelty or general PSI superiority is established.**','',
               'The original Version 3 real-record controls remain separate and unchanged: exact target recovery is 0/30 for both accumulated statistics at both batch sizes. This negative result is not replaced by the synthetic study. Natural ACS comparisons are unchanged.','',
               f'Benchmark execution: {vm["wall_seconds"]:.1f} seconds wall time, {vm["cpu_seconds"]:.1f} seconds CPU; shared peak process RSS {vm["peak_process_rss_kib"]/1024:.1f} MiB. These are local software costs, not deployment guarantees. Logical histogram/raw-array payload and separately instrumented Python allocations are not total monitor memory. KS warnings: {vm["ks_warnings"]}.','',
               '## Reading and reproducing the frozen set','',
               '- [New chart pack](../../figures/correction/SubPSI_correction_chart_pack.pdf) and [interactive file index](../../figures/correction/index.html). Ten charts, each with PNG/PDF/SVG and a source CSV.','- [Plain-English chart guide](CHART_GUIDE.md).','- [Claim-to-evidence ledger](CLAIM_EVIDENCE.md), with machine-readable CSV/JSON alongside it.','- [Reproduction steps](REPRODUCE.md).','- [Change and AI contribution log](../../records/correction/WORK_LOG.md).','- [Freeze manifest](../../records/correction/FREEZE.json) binds the evidence hashes and code versions.','',
               'The freeze records the bounded evidence set requested in this correction. It does not choose a final submission version, certify competition eligibility, establish novelty, or claim independent student authorship. No final results section is written in the student’s voice.']
    (ROOT/'docs/correction/FINDINGS.md').write_text('\n'.join(report)+'\n')
    (ROOT/'REVISION3_CORRECTION.md').write_text('# Version 3 correction — start here\n\nThis is a documented post-result correction, with the original Versions 1, 2 and 3 preserved.\n\n[Findings and limitations](docs/correction/FINDINGS.md) · [Chart pack](figures/correction/SubPSI_correction_chart_pack.pdf) · [Claim/evidence record](docs/correction/CLAIM_EVIDENCE.md) · [Change log](records/correction/WORK_LOG.md)\n\nThe final project version is still the user’s choice. This correction is local; no new push or deployment was performed.\n')
    # Retain verified, unaffected main V3 figures. Replace its OULAD figures with
    # the correction pack; old figure 11 remains archived because it mixes datasets.
    oldfig=ROOT/'figures/revision3/main-approved-checked'
    selected=[p for p in oldfig.iterdir() if p.name[:2] in {'01','03','05','06','07','08','09','10','12'}]
    entries={}
    # The CLI stdout log may still be open while this manifest is assembled.
    # Bind completed evidence only, excluding the manifest's own receipt/log.
    excluded={target,target.with_suffix('.sha256'),ROOT/'records/correction/freeze_creation.txt'}
    for folder in ['configs/correction','src/subpsi','scripts/correction','tests','results/raw/correction','results/summary/correction','figures/correction','docs/correction','records/correction']:
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and '__pycache__' not in str(p) and p not in excluded:
                entries[str(p.relative_to(ROOT))]=sha256(p)
    for p in selected+[ROOT/'REVISION3_CORRECTION.md',ROOT/v2cfg,ROOT/v3cfg,ROOT/'results/summary/revision3/main-approved-checked/control_proportions.csv',ROOT/'results/raw/revision3/main-approved/manifest.json']:
        entries[str(p.relative_to(ROOT))]=sha256(p)
    write_json(target,{'status':'FROZEN_VERIFIED_CORRECTION_SET','created_utc':datetime.now(timezone.utc).isoformat(),
               'final_submission_version_selected':False,'post_result_correction':True,
               'freeze_code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
               'numerical_versions':{'corrected_oulad':om['git_head'],'matched_v2':vm['git_head'],'preserved_v3':original_main['git_head']},
               'evidence_sha256':entries,'claims_sha256':sha256(ledger),
               'baseline_preservation_inventory_sha256':sha256(ROOT/'records/correction/preserved_inventory.json'),
               'figure_selection':{'corrected':'all ten figures/correction plots','preserved_v3_prefixes':['01','03','05','06','07','08','09','10','12'],
                                   'superseded_oulad':['original V3 02, 04 and OULAD portion of 11; preserved as historical artifacts, not current claims']},
               'scope':'Natural observations, constructed real-record controls and mathematical simulations remain distinct. This freeze is evidence preparation, not a student-authored submission.'})
    (target.with_suffix('.sha256')).write_text(sha256(target)+'  FREEZE.json\n')
    print('Frozen',len(entries),'evidence files;',len(claims),'claim records. Final version selection remains pending.')

if __name__=='__main__':main()
