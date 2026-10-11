"""Verify immutable predecessors and the exact tables exported to the two charts."""
import argparse,json,sys
from pathlib import Path
from datetime import datetime,timezone
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from subpsi.correction import read_table
from subpsi.provenance import sha256,write_json
from subpsi.revision4 import augment_saved_outcomes


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='records/revision4/preparation_verification.json')
    args=parser.parse_args();out=ROOT/args.out
    if out.exists():raise FileExistsError('Choose unused verification output')
    base=ROOT/'results/summary/revision4/preparation-02'
    inventory=json.loads((base/'preserved_inventory.json').read_text())
    for name,expected in inventory.items():
        if sha256(ROOT/name)!=expected:raise ValueError('Starting file changed: '+name)
    frozen=json.loads((ROOT/'records/correction/FREEZE.json').read_text())
    for name,expected in frozen['evidence_sha256'].items():
        if sha256(ROOT/name)!=expected:raise ValueError('Old correction changed: '+name)
    verified=0
    for folder in ['results/summary/revision4/preparation','results/summary/revision4/preparation-02','figures/revision4/preparation']:
        m=json.loads((ROOT/folder/'manifest.json').read_text())
        for name,expected in m['files'].items():
            if sha256(ROOT/folder/name)!=expected:raise ValueError('R4 artifact changed: '+folder+'/'+name)
            verified+=1
    def equal(a,b):
        pd.testing.assert_frame_equal(a.reset_index(drop=True),b.reset_index(drop=True),
                                      check_dtype=False,check_exact=False,rtol=0,atol=1e-12)
    outcomes=augment_saved_outcomes(read_table(ROOT/'results/raw/correction/oulad/outcomes.csv'))
    equal(outcomes,read_table(base/'oulad_outcomes_extended.csv'))
    equal(outcomes.query("group == 'Everyone' and subset == 'group' and period == 'current'"),
          read_table(ROOT/'figures/revision4/preparation/02_oulad_prediction_baseline.csv'))
    audit=json.loads((base/'representation_audit.json').read_text());rows=[]
    for r in audit:
        if r['feature']!='num_of_prev_attempts':continue
        labels=['Below zero','0 or more','Missing'] if r['rule']=='v3_quantile' else ['0','1','2 or more','Missing']
        for label,count in zip(labels,r['counts']):
            rows.append(dict(rule=r['rule'],category=label,count=count,n_design=r['n_design'],
                             occupied_numeric_bins=r['occupied_numeric_bins'],nonconstant_collapse=r['nonconstant_collapse']))
    equal(pd.DataFrame(rows),read_table(ROOT/'figures/revision4/preparation/01_oulad_representation.csv'))
    from PIL import Image
    images=[]
    for f in sorted((ROOT/'figures/revision4/preparation').glob('*.png')):
        with Image.open(f) as im:
            if any(abs(d-300)>.1 for d in im.info['dpi']):raise ValueError('PNG is not 300 dpi')
            images.append(dict(file=str(f.relative_to(ROOT)),pixels=list(im.size),dpi=list(im.info['dpi'])))
    write_json(out,dict(status='PASS',utc=datetime.now(timezone.utc).isoformat(),
                       starting_files_unchanged=len(inventory),old_freeze_hashes=len(frozen['evidence_sha256']),
                       new_artifact_hashes=verified,balanced_accuracy_rows_verified=len(outcomes),
                       chart_csvs_match_saved_tables=2,images=images,
                       main_calibration_or_evaluation_executed=False))
    print(f'PASS: {len(inventory)} starting files unchanged; {verified} new artifact hashes; 2 figure CSVs; {len(outcomes)} outcome rows.')


if __name__=='__main__':main()
