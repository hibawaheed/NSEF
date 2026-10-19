"""Descriptive replay check of corrected OULAD; no new alarms or model fitting."""
from common import *
from subpsi.realdata import load_datasets
from subpsi.correction import AttemptBins
from subpsi.revision4 import CollectionPlan
from subpsi.low_compute import run_lightweight

def main():
 out=ROOT/'results/raw/low_compute/2026-10-18/oulad_equivalence.json'
 if out.exists():raise FileExistsError(out)
 cfg=json.loads((ROOT/'configs/revision3/approved.json').read_text());datasets,sources=load_datasets(ROOT,cfg);d=datasets[1]
 original=ROOT/'results/raw/revision4/main-approved/oulad-replay'
 saved=json.loads((ROOT/'results/raw/revision3/main-approved/models_and_bins.json').read_text())['OULAD_BBB']
 bins={f:NumericBins(tuple(float(x) for x in m['edges'])) for f,m in saved['bins'].items()};bins['num_of_prev_attempts']=AttemptBins()
 old=pd.read_csv(original/'natural_tests.csv',float_precision='round_trip');correction=json.loads((ROOT/'configs/correction/frozen.json').read_text());checks=[]
 features=d['features']+list(cfg['oulad']['group_levels'])
 for variant,policy,n in correction['oulad']['policies']:
  plan=CollectionPlan(tuple((g.name,n) for g in d['groups']),n,len(d['windows']),policy)
  new=run_lightweight(d['reference'][features],((t,f[features]) for t,f in d['windows']),bins=bins,groups=d['groups'],plan=plan,inferential=False)
  before=old.loc[old.variant.eq(variant)].reset_index(drop=True);after=pd.DataFrame(new['tests'])
  for key in ['group','feature','time','n_reference','n_current','eligible','block_sha256','status']:
   if before[key].tolist()!=after[key].tolist():raise AssertionError('OULAD '+key)
  np.testing.assert_allclose(before.psi,after.psi,rtol=0,atol=0,equal_nan=True)
  if any(r['p'] is not None for r in new['tests']):raise AssertionError('Natural p-values introduced')
  checks.append(dict(variant=variant,rows=len(after),exact=True,max_psi_difference=0))
 out.write_text(json.dumps(dict(checks=checks,source_csv=str((original/'natural_tests.csv').relative_to(ROOT)),source_sha256=sha256(original/'natural_tests.csv'),note='Natural cohort scores remain descriptive. Corrected 0/1/2+ bins, groups, support and records unchanged. No classifier refit or prediction change.'),indent=2)+'\n');print('OULAD natural replay exact',checks)
if __name__=='__main__':main()
