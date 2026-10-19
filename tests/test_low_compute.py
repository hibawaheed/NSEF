"""Deterministic engineering fixtures, not new research respondents/trials."""
from copy import deepcopy
import numpy as np
import pandas as pd
import pytest
from subpsi.core import NumericBins,Group
from subpsi.correction import AttemptBins
from subpsi.matched import declared_groups
from subpsi.revision4 import CollectionPlan,run_frozen_targets
from subpsi.low_compute_baseline import run_baseline
from subpsi.low_compute import run_lightweight,iter_monitor,group_masks

SCHEDULE=['group','look','time','block_sha256','n_current','n_reference','eligible','opened_look','waiting_looks','waiting_time','oldest_time','newest_time','maximum_age','dropped_old','dropped_total','incoming_target','min_reference','plan_sha256','historical_shortage','collecting_current']
COMMON=SCHEDULE+['feature','level','policy','status']
PSI=['psi','p','draws','censored']
KS=['ks_p','ks_d','ks_status']
def project(out,method):
    rows=[{k:r[k] for k in COMMON+(PSI if method=='PSI' else KS)} for r in out['tests']]
    return {'tests':rows,'schedule':[{k:r[k] for k in SCHEDULE} for r in out['schedule']],
            'decisions':[d for d in out['decisions'] if d['method']==method]}

def inputs(policy='accumulate'):
    ref=pd.DataFrame({'attempt':[0,0,1,1,2,10,np.nan,0], 'x':[4]*8,'A':[0,1]*4,'B':[0,0,1,1]*2},index=[f'r{i}' for i in range(8)])
    groups=declared_groups({'A':[0,1,2],'B':[0,1]})
    windows=[]
    for look,values in enumerate([[0,1,2],[],[20,np.nan,0,1],[0,100]],1):
        n=len(values);windows.append((look,pd.DataFrame({'attempt':values,'x':np.arange(n)*100-50,'A':np.arange(n)%2,'B':np.arange(n)%2,'label':np.zeros(n)},index=[f'd{look}:{i}' for i in range(n)])))
    bins={'attempt':AttemptBins(),'x':NumericBins.fit([4]*8,6)}
    plan=CollectionPlan(tuple((g.name,3 if g.level=='aggregate' else 4) for g in groups),2,4,policy)
    return ref,windows,dict(bins=bins,groups=groups,plan=plan,alpha=.05,draws=2399,inferential=True,seed=727)

@pytest.mark.parametrize('policy',['accumulate','batch'])
def test_all_scientific_fields_exact_psi_and_ks(policy):
    r,w,kw=inputs(policy);old=run_frozen_targets(r,w,**kw)
    traces=[];newtr=[]
    baseline=run_baseline(r,w,trace=lambda a,b,s,o:traces.append((a.tolist(),b.tolist(),s,o)),**kw)
    new=run_lightweight(r,iter(w),trace=lambda a,b,s,o:newtr.append((a.tolist(),b.tolist(),s,o)),**kw)
    assert project(old,'PSI')==project(baseline,'PSI')==project(new,'PSI')
    assert traces==newtr
    assert project(old,'KS')==project(run_lightweight(r,iter(w),method='KS',**kw),'KS')
    assert all(x['p']==1 for x in new['tests'] if not x['eligible'])
    assert new['metadata']['validation_accounted_bytes_end']>new['metadata']['persistent_histogram_array_bytes']


def test_labels_invariant_and_features_do_not_change_schedule():
    r,w,k=inputs();a=run_lightweight(r,w,**k)
    labels=[(t,f.assign(label=1-f.label)) for t,f in w]
    assert project(a,'PSI')==project(run_lightweight(r,labels,**k),'PSI')
    features=[(t,f.assign(x=-f.x,attempt=0)) for t,f in w]
    assert a['schedule']==run_lightweight(r,features,**k)['schedule']

@pytest.mark.parametrize('kind',['reference','cross_batch','within_batch','non_string','time','infinity','invalid_attempt'])
def test_bad_arrivals_raise_without_completed_run(kind):
    r,w,k=inputs();w=deepcopy(w)
    if kind=='reference':w[0][1].index=['r0','q1','q2']
    if kind=='cross_batch':w[3][1].index=[w[0][1].index[0],'new']
    if kind=='within_batch':w[0][1].index=['same']*3
    if kind=='non_string':w[0][1].index=[1,2,3]
    if kind=='time':w[1]=(0,w[1][1])
    if kind=='infinity':
        w[0][1]['x']=w[0][1].x.astype(float)
        w[0][1].iloc[0,w[0][1].columns.get_loc('x')]=np.inf
    if kind=='invalid_attempt':w[0][1].iloc[0,0]=-1
    with pytest.raises(ValueError):run_lightweight(r,w,**k)


def test_resolution_horizon_and_no_alpha_reset():
    r,w,k=inputs()
    with pytest.raises(ValueError,match='floor'):run_lightweight(r,w,**{**k,'draws':1})
    with pytest.raises(ValueError,match='horizon'):run_lightweight(r,w[:2],**k)
    a=run_lightweight(r,w[:2],allow_prefix=True,**k)
    assert {d['cutoff'] for d in a['decisions']}=={.05/4}
    extra=pd.DataFrame({col:[] for col in r},index=pd.Index([],dtype=str))
    with pytest.raises(ValueError,match='horizon'):run_lightweight(r,w+[(5,extra)],**k)


def test_selector_missingness_tails_and_overlapping_groups():
    f=pd.DataFrame({'A':[None,0,1,np.nan],'B':[0,0,0,1]})
    g=[Group('all'),Group('missing',(('A',None),),'single'),Group('zero',(('B',0),),'single')]
    for a,b in zip(group_masks(f,g),[x.mask(f) for x in g]):np.testing.assert_array_equal(a,b)
    b=AttemptBins();assert b.counts([0,1,2,3,100000,np.nan]).tolist()==[1,1,3,1]


def test_counts_added_before_smoothing_and_whole_batch_overshoot():
    r,w,k=inputs();trace=[]
    run_lightweight(r,w,trace=lambda a,b,s,o:trace.append((a,b,s,o)),**k)
    # First Everyone block contains all three records, including each discrete category.
    assert trace[0][1].tolist()==[1,1,1,0]
    assert trace[0][0].tolist()==[3,2,2,1]
    a=run_lightweight(r,w,**k)
    overshoot=[x for x in a['schedule'] if x['eligible'] and x['n_current']>x['incoming_target']]
    assert overshoot and all(x['n_current']>=x['incoming_target'] for x in overshoot)
