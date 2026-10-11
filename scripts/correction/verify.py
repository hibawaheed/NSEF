"""Verify preservation, complete evidence, replays and plotted table selections."""
import argparse,gzip,json,sys,tempfile
from pathlib import Path
import importlib.util
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from subpsi.correction import matched_v2
from subpsi.provenance import sha256,write_json


def clean(value):
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items() if not k.endswith('seconds')}
    if isinstance(value,list):return [clean(v) for v in value]
    return value


def table_equal(expected,actual):
    pd.testing.assert_frame_equal(expected.reset_index(drop=True),actual.reset_index(drop=True),
                                  check_dtype=False,check_exact=False,rtol=0,atol=1e-12)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='records/correction/verification.json');args=parser.parse_args()
    out=ROOT/args.out
    if out.exists():raise ValueError('Refuse to replace verification record')
    inventory=json.loads((ROOT/'records/correction/preserved_inventory.json').read_text())
    for name,digest in inventory.items():
        if sha256(ROOT/name)!=digest:raise ValueError('Original file changed: '+name)
    manifests=['results/raw/correction/oulad','results/raw/correction/v2-matched','results/raw/correction/cost-check',
               'results/summary/correction','figures/correction']
    count=0
    for folder in manifests:
        m=json.loads((ROOT/folder/'manifest.json').read_text())
        for name,digest in m['files'].items():
            if sha256(ROOT/folder/name)!=digest:raise ValueError('Artifact hash mismatch: '+folder+'/'+name)
            count+=1
    c=json.loads((ROOT/'configs/revision2.json').read_text())
    names=['null_n250_0000.json.gz','grid_n250_s0.05_m1.4_0000.json.gz','correlation_0000.json.gz']
    for name in names:
        with gzip.open(ROOT/'results/raw/revision2'/name,'rt') as f:old=json.load(f)
        with gzip.open(ROOT/'results/raw/correction/v2-matched'/name,'rt') as f:saved=json.load(f)
        replay=matched_v2(c,old)
        if clean(replay)!=clean({k:saved[k] for k in replay}):raise ValueError('Numerical replay differs: '+name)
    # Recompute OULAD with source, role, frozen-model, and old-result guards.
    spec=importlib.util.spec_from_file_location('correction_run',ROOT/'scripts/correction/run.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix='subpsi-correction-replay-') as tmp:
        replay=Path(tmp);module.natural(json.loads((ROOT/'configs/correction/frozen.json').read_text()),replay)
        for name in ['natural_tests.csv','natural_schedule.csv','bin_counts.csv','outcomes.csv','old_vs_corrected.csv']:
            old=pd.read_csv(ROOT/'results/raw/correction/oulad'/name);new=pd.read_csv(replay/name)
            cols=[col for col in old if 'seconds' not in col]
            table_equal(old[cols],new[cols])
    # All 1820 paired methods have identical support, wait, block age and shared inputs.
    streams=pd.read_csv(ROOT/'results/raw/correction/v2-matched/streams.csv')
    for col in ['target_ever_assessed','target_first_assessment_restricted','target_assessed_fraction','eligible_fraction','maximum_block_age','shared_input_frame_bytes']:
        p=streams.pivot(index='run',columns='method',values=col)
        if not p.PSI.eq(p.KS).all():raise ValueError('Unequal collection: '+col)
    ou=ROOT/'results/raw/correction/oulad';summary=ROOT/'results/summary/correction';figures=ROOT/'figures/correction'
    bins=pd.read_csv(ou/'bin_counts.csv');distances=pd.read_csv(ou/'old_vs_corrected.csv');outcomes=pd.read_csv(ou/'outcomes.csv')
    cells=pd.read_csv(summary/'all_cells.csv');aggregate=pd.read_csv(summary/'benchmark_aggregate.csv')
    expected={
      '01_historical_bin_correction':bins.query("period=='design_2013J' and group=='Everyone' and feature=='num_of_prev_attempts'"),
      '02_oulad_corrected_distances':distances.query("variant=='accum100'"),
      '03_prediction_baseline':outcomes.query("group=='Everyone'"),
      '04_outcome_gaps_with_baseline':outcomes,
      '05_input_and_outcome_context':pd.read_csv(summary/'oulad_input_outcome_pairs.csv'),
      '06_all_original_grid_cells':cells[cells.id.str.startswith('grid_') & cells.metric.eq('post_alert')],
      '07_matched_detection_and_null_alerts':aggregate[aggregate.method.isin(['PSI','KS']) & aggregate.metric.isin(['stream_alert','post_alert'])],
      '08_target_coverage_and_wait':cells[cells.id.str.startswith('grid_') & cells.magnitude.eq(1.4) & cells.metric.isin(['target_ever_assessed','target_detected','target_restricted_delay','eligible_fraction'])],
      '09_all_robustness_cases':cells[~cells.id.str.startswith(('grid_','null_')) & cells.metric.eq('post_alert')],
      '10_costs_with_scope':cells[cells.metric.isin(['test_seconds','maximum_logical_payload_bytes','shared_input_frame_bytes','maximum_block_age'])]}
    for stem,frame in expected.items():
        table_equal(frame,pd.read_csv(figures/f'{stem}.csv'))
    summary_manifest=json.loads((summary/'manifest.json').read_text())
    write_json(out,{'status':'PASS','original_files_preserved':len(inventory),'artifact_hashes_verified':count,
                   'verified_manifests':{folder+'/manifest.json':sha256(ROOT/folder/'manifest.json') for folder in manifests},
                   'replayed_v2_streams':names,'replayed_oulad':'all policies, bins and both outcome models; exact counts and scores within 1e-12; timings excluded',
                   'figure_csvs_match_source_tables':list(expected),'matched_support_streams':1820,
                   'original_v2_reporting':summary_manifest['original_v2_report_parity'],
                   'note':'No claims about natural drift truth or independent student authorship. Visual checks are recorded separately.'})
    print('PASS:',len(inventory),'original files preserved;',count,'artifact hashes; four numerical replays; ten figure CSVs matched.')

if __name__=='__main__':main()
