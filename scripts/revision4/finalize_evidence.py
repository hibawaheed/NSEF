"""Bind claims/figures to saved outputs; freeze a reviewable evidence snapshot.

This is not final submission approval or an algorithmic novelty certification.
"""
import argparse,csv,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from subpsi.provenance import sha256,write_json
from subpsi.correction import read_table
from subpsi.revision4 import wilson_lower


def main():
 parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');args=parser.parse_args()
 raw=ROOT/'results/raw/revision4/main-approved';summary=ROOT/'results/summary/revision4/main-approved';fig=ROOT/'figures/revision4/final'
 # Verify all explicitly declared figure files and direct parents before claims.
 manifest=json.loads((fig/'manifest.json').read_text());index=json.loads((fig/'figure_index.json').read_text())
 if len(index)!=12:raise ValueError('Expected complete figure set')
 for name,h in manifest['files'].items():
  if sha256(fig/name)!=h:raise ValueError('Figure export hash mismatch: '+name)
 for item in index:
  for name,h in item['source_tables'].items():
   if sha256(ROOT/name)!=h:raise ValueError('Graph source changed: '+name)
  previous=ROOT/'figures/revision4/main-approved-checked'/item['source_csv']
  if sha256(previous)!=sha256(fig/item['source_csv']):raise ValueError('Layout change altered a figure CSV')
 # Direct numerical table-to-figure checks (not only self-reported hashes).
 rates=read_table(summary/'rates.csv')
 expected=rates.loc[rates.scope.eq('intersection') & ((rates.condition.eq('unchanged')&rates.metric.eq('whole_stream_alert'))|(~rates.condition.eq('unchanged')&rates.metric.eq('exact_target_detection')))].reset_index(drop=True)
 for name in ['03_paired_policy_alerts','03b_paper_policy_alerts']:
  pd.testing.assert_frame_equal(read_table(fig/(name+'.csv')),expected,check_dtype=False)
 for scenario in ['unchanged','age_up2','age_up4']:
  expected=read_table(summary/'selection_cells.csv');expected=expected.loc[expected.scenario.eq(scenario)].reset_index(drop=True)
  pd.testing.assert_frame_equal(read_table(fig/f'01_sensitivity_{scenario}.csv'),expected,check_dtype=False)
 for stem,source in [('02_frozen_targets_validation','selection_validation.csv'),('04_all_group_assessability','coverage_summary.csv'),('07_compute_costs','costs.csv')]:
  pd.testing.assert_frame_equal(read_table(fig/(stem+'.csv')),read_table(summary/source),check_dtype=False)
 expected=read_table(summary/'streams.csv');expected=expected.loc[expected.scope.eq('intersection')&~expected.condition.eq('unchanged')].reset_index(drop=True)
 pd.testing.assert_frame_equal(read_table(fig/'05_detection_wait_including_misses.csv'),expected,check_dtype=False)
 expected=read_table(summary/'oulad_outcomes_extended.csv').query("group == 'Everyone' and subset == 'group' and period == 'current'").reset_index(drop=True)
 pd.testing.assert_frame_equal(read_table(fig/'06_oulad_model_baseline.csv'),expected,check_dtype=False)
 expected=read_table(raw/'oulad-replay/old_vs_corrected.csv');expected=expected.loc[expected.feature.eq('num_of_prev_attempts')].reset_index(drop=True)
 pd.testing.assert_frame_equal(read_table(fig/'08_oulad_corrected_psi.csv'),expected,check_dtype=False)
 expected=read_table(summary/'pipeline_costs.csv');actual=read_table(fig/'09_pipeline_cost_and_memory.csv')
 pd.testing.assert_frame_equal(actual.loc[actual.record_type.eq('stage'),list(expected)].reset_index(drop=True),expected,check_dtype=False)
 costs=read_table(summary/'costs.csv');payload=actual.loc[actual.record_type.eq('payload')].set_index('method')
 assert payload.loc['PSI','bytes']==costs.psi_max_payload_bytes.max()
 assert payload.loc['KS','bytes']==costs.ks_max_payload_bytes.max()
 # Pointwise source-conditional uncertainty for every group availability cell.
 cov=read_table(summary/'coverage_summary.csv');cov['successes']=cov.streams-cov.never_assessed
 cov['lower']=[0. if k==0 else wilson_lower(int(k),int(n)) for k,n in zip(cov.successes,cov.streams)]
 cov['upper']=[1. if k==n else 1-wilson_lower(int(n-k),int(n)) for k,n in zip(cov.successes,cov.streams)]
 cov.to_csv(summary/'coverage_intervals.csv',index=False)
 now=datetime.now(timezone.utc)
 verification=dict(utc=now.isoformat(),figures=12,all_figure_source_csvs_match_tables=True,
  layout_only_revisions_preserved_all_12_csv_hashes=True,figure_manifest_sha256=sha256(fig/'manifest.json'),
  metadata='All prior raw experiments unchanged. Wilson endpoint display rounding and explicit missing representations are reporting repairs only.')
 write_json(ROOT/'records/revision4/main/figure_verification.json',verification)
 code=json.loads((raw/'started.json').read_text())['git_head'];config='configs/revision4/approved.json'
 claims=[
 ('R4-C01','The corrected OULAD bins distinguish zero, one and two-or-more attempts; old and corrected outputs are retained.','Post-result natural-data correction','results/raw/revision4/main-approved/oulad-replay/old_vs_corrected.csv','08_oulad_corrected_psi','Does not establish true onset or natural drift-detection accuracy.'),
 ('R4-C02','Frozen model correct 541/973; training-majority baseline 547/973.','Natural descriptive outcome audit','results/summary/revision4/main-approved/oulad_outcomes_extended.csv','06_oulad_model_baseline','Baseline selected from training labels only; weak model; no harm or causal claim.'),
 ('R4-C03','Fifteen of thirty declared views meet historical source support.','Historical support inspection','results/summary/revision4/preparation-02/acs_candidate_support.csv','01_sensitivity_age_up2','Unsupported views remain in the family and tables.'),
 ('R4-C04','No group met the selection criterion; all targets and the global target fell back to 800.','Constructed historical resampling','results/summary/revision4/main-approved/selected_targets.csv','02_frozen_targets_validation','Fallback is not validated adequacy or a new successful rule.'),
 ('R4-C05','No supported validation group met the prespecified criterion.','Independent historical source-half resampling','results/summary/revision4/main-approved/selection_validation.csv','02_frozen_targets_validation','Validation does not retune the map; not population certification.'),
 ('R4-C06','All policy/statistic detection and null-alert counts are retained; fixed 100 gives 39/40 PSI and 40/40 KS in the strongest upward condition.','Constructed 2016 empirical-source evaluation','results/summary/revision4/main-approved/rates.csv','03b_paper_policy_alerts','Includes weaker and downward conditions; no universal winner or natural accuracy claim.'),
 ('R4-C07','All 220 global/group policy runs tie scientifically; the target is never assessed with target 800.','Constructed paired evaluation','results/summary/revision4/main-approved/coverage.csv','04_all_group_assessability','A group that cannot be tested must not be called stable.'),
 ('R4-C08','Misses receive restricted delay 15; first assessment and first detection remain separate.','Constructed paired evaluation','results/summary/revision4/main-approved/streams.csv','05_detection_wait_including_misses','Constructed looks are not days or real event times.'),
 ('R4-C09','Complete-stream paired intervals retain all differences, including ties and adverse comparisons.','Conditional Monte Carlo uncertainty','results/summary/revision4/main-approved/paired_differences.csv','03_paired_policy_alerts','Pointwise, not simultaneous or population confidence.'),
 ('R4-C10','Calibration costs, statistic kernels, shared engine costs and process memory are measured separately.','Local computational measurement','results/summary/revision4/main-approved/pipeline_costs.csv','09_pipeline_cost_and_memory','Logical payload is not total memory; timings depend on hardware.'),
 ('R4-C11','The full matched accumulated-KS comparison on the 1,820-stream Version 2 benchmark is preserved.','Legacy mathematical simulation','results/summary/correction/benchmark_aggregate.csv','','Synthetic evidence remains distinct from collected records.'),
 ('R4-C12','The original weak Version 3 real-record substitution comparison remains a limitation.','Previously examined constructed real-record controls','results/summary/revision3/main-approved-checked/control_proportions.csv','','New conditions and OULAD corrections do not erase earlier misses.')]
 rows=[]
 for cid,claim,evidence,table,figure,limitation in claims:
  this_config='configs/correction/frozen.json' if cid in ['R4-C01','R4-C02','R4-C11'] else 'configs/revision3/approved.json' if cid=='R4-C12' else config
  this_code='22d6d439045ce6c25da59fc6c7c270e99edab1be' if cid=='R4-C11' else 'efe9124eb8425ad4c7339b9c4a0373ac33ec0f1f' if cid=='R4-C12' else code
  source_manifest=('results/raw/revision4/main-approved/oulad-replay/manifest.json' if cid in ['R4-C01','R4-C02'] else 'results/summary/revision4/preparation-02/manifest.json' if cid=='R4-C03' else 'results/raw/correction/v2-matched/manifest.json' if cid=='R4-C11' else 'results/raw/revision3/main-approved/manifest.json' if cid=='R4-C12' else 'results/raw/revision4/main-approved/started.json')
  provenance=json.loads((ROOT/source_manifest).read_text());this_code=provenance.get('git_head',this_code)
  rows.append(dict(claim_id=cid,claim=claim,evidence_type=evidence,source_table=table,source_sha256=sha256(ROOT/table),
   configuration=this_config,configuration_sha256=sha256(ROOT/this_config),computation_code_version=this_code,provenance_manifest=source_manifest,provenance_manifest_sha256=sha256(ROOT/source_manifest),
   source_snapshot_or_code_sha256=provenance.get('source_snapshot_sha256',provenance.get('original_code_sha256','')),
   verification_record='records/revision4/main/evaluation_verification.json' if cid=='R4-C07' else '',
   figure_csv='figures/revision4/final/'+figure+'.csv' if figure else '',limitations=limitation))
 with (ROOT/'docs/revision4/CLAIM_EVIDENCE_FINAL.csv').open('w',newline='') as handle:
  writer=csv.DictWriter(handle,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
 if args.freeze:
  target=ROOT/'records/revision4/RESULTS_FREEZE.json'
  if target.exists():raise FileExistsError('Never overwrite a results freeze')
  # Hash all R4 delivery artifacts and code; older versions retain their own manifests.
  files={}
  for directory in ['src','tests','scripts','configs','docs/revision4','records/revision4','results/raw/revision4','results/summary/revision4','figures/revision4']:
   for path in sorted((ROOT/directory).rglob('*')):
    if path.is_file() and '__pycache__' not in str(path) and path!=target and path!=ROOT/'records/revision4/main/WORK_LOG.md':
     files[str(path.relative_to(ROOT))]=sha256(path)
  for name in ['REVISION4_STATUS.md','requirements-lock.txt','pyproject.toml']:files[name]=sha256(ROOT/name)
  write_json(target,dict(created_utc=now.isoformat(),created_local=now.astimezone(ZoneInfo('Asia/Karachi')).isoformat(),
   status='VERIFIED_EVIDENCE_SNAPSHOT_NOT_FINAL_SUBMISSION_VERSION',planned_results_freeze='2026-10-18',submission_deadline='2026-10-26',
   user_protocol_approved=True,mentor_or_fair_approval_evidence=None,final_project_version_selected=False,
   computation_code_version=code,reporting_code_version=json.loads((fig/'manifest.json').read_text())['git_head'],
   snapshot_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
   files=files,append_only_log_excluded='records/revision4/main/WORK_LOG.md',private_lineage_manifest='records/revision4/main/evaluation_verification.json',
   earlier_correction_freeze_sha256=sha256(ROOT/'records/correction/FREEZE.json'),
   prior_preparation_manifest_sha256=sha256(ROOT/'records/revision4/PREPARATION_MANIFEST.json')))
 print('Verified 12 graphs and sources, wrote 12 claim links'+('; created immutable results snapshot' if args.freeze else ''))

if __name__=='__main__':main()
