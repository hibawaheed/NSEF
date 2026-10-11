import numpy as np
import pandas as pd
import pytest
from subpsi.core import NumericBins, CategoryBins
from subpsi.matched import CollectionScheduler, declared_groups, run_matched, compare_block


def frame(ids, x=None, group=None):
    return pd.DataFrame({'x': np.arange(len(ids),dtype=float) if x is None else x,
                         'g': ['a']*len(ids) if group is None else group}, index=ids)


def test_whole_batches_reset_once_and_no_overlap():
    s=CollectionScheduler({'a':8,'absent':0},min_n=3,horizon=4)
    inputs=[['1','2'],[],['3','4'],['5']]
    blocks=[s.advance(t,{'a':v,'absent':[]})[0] for t,v in enumerate(inputs,2016)]
    assert [b.ids for b in blocks]==[('1','2'),('1','2'),('1','2','3','4'),('5',)]
    assert [b.ready for b in blocks]==[False,False,True,False]
    assert blocks[2].metadata()['waiting_time']==2
    assert blocks[3].opened_look==4
    with pytest.raises(ValueError,match='horizon'):s.advance(2020,{'a':[],'absent':[]})


def test_reference_support_never_manufactured():
    s=CollectionScheduler({'a':2},min_n=3,horizon=2)
    assert not s.advance(1,{'a':['1','2','3']})[0].ready
    b=s.advance(2,{'a':['4']})[0]
    assert not b.ready and len(b.ids)==4


def test_age_boundary_expiration_and_waiting_clock():
    s=CollectionScheduler({'a':100},min_n=4,horizon=4,max_age=1)
    s.advance(2016,{'a':['1','2']})
    b=s.advance(2017,{'a':['3']})[0]
    assert b.ids==('1','2','3') and b.dropped_old==0
    b=s.advance(2018,{'a':['4']})[0]
    assert b.ids==('3','4') and b.dropped_old==2 and not b.ready
    assert b.metadata()['waiting_time']==2 and b.metadata()['maximum_age']==1
    b=s.advance(2019,{'a':['5','6','7']})[0]
    assert b.ready and b.ids==('4','5','6','7') and b.dropped_total==3
    assert b.look==4 and b.opened_look==1


def test_new_missing_and_multicategory_groups_are_declared():
    groups=declared_groups({'g':['a','b','c',None],'sex':['F','M']})
    assert len(groups)==15 and sum(g.level=='intersection' for g in groups)==8
    f=pd.DataFrame({'g':['a',None,'new'],'sex':['F','M','F']})
    assert [g for g in groups if g.name=='g=None'][0].mask(f).tolist()==[False,True,False]
    with pytest.raises(ValueError):declared_groups({'a':[0],'b':[0],'c':[0]})


@pytest.mark.parametrize('bad',[-1,1.5])
def test_invalid_age_cap(bad):
    with pytest.raises(ValueError):CollectionScheduler({'a':5},min_n=2,horizon=3,max_age=bad)


def test_ids_times_and_memberships_fail_before_state_change():
    s=CollectionScheduler({'a':5,'b':5},min_n=3,horizon=5)
    s.advance(1,{'a':['1'],'b':['1']}) # overlap across groups is intended
    for t,m in [(2,{'a':['1'],'b':[]}),(1,{'a':[],'b':[]}),(2,{'a':['2','2'],'b':[]}),(2,{'a':[]})]:
        with pytest.raises(ValueError):s.advance(t,m)
        assert s.look==1


def test_matched_statistic_calls_receive_exact_blocks(monkeypatch):
    import subpsi.matched as module
    seen=[]; original=module.compare_block
    def spy(a,b,binning,**kw):
        seen.append((a.copy(),b.copy()))
        return original(a,b,binning,**kw)
    monkeypatch.setattr(module,'compare_block',spy)
    ref=frame(['r1','r2','r3','r4'],[0,0,1,np.nan])
    ws=[(2017,frame(['a','b'],[100,np.nan])),(2018,frame(['c','d'],[-100,2]))]
    out=run_matched(ref,ws,bins={'x':NumericBins.fit([0,1,2])},groups=declared_groups({}),min_n=3)
    assert len(seen)==1
    np.testing.assert_equal(seen[0][1],[100,np.nan,-100,2])
    r=out['tests'][-1];assert r['n_current']==4 and r['missing_current']==1
    assert r['p'] is None and r['ks_p'] is None
    assert all(d['alert'] is None for d in out['decisions'])


def test_scheduler_invariant_to_values_outcomes_and_feature_order():
    ref=frame(['r'+str(i) for i in range(10)])
    ws=[(t,frame([f'{t}-{i}' for i in range(2)])) for t in range(3)]
    bins={'x':NumericBins.fit([0,1,2])};groups=declared_groups({'g':['a','b']})
    a=run_matched(ref,ws,bins=bins,groups=groups,min_n=3)
    for _,f in ws:f['x']=[np.nan,999];f['y']=[1,0]
    b=run_matched(ref,ws,bins=bins,groups=groups,min_n=3)
    def schedules(o):return [{k:v for k,v in r.items() if 'seconds' not in k} for r in o['schedule']]
    assert schedules(a)==schedules(b)
    assert all(not r['eligible'] for r in a['tests'] if r['group']=="g='b'")


def test_batch_policy_discards_unsupported_batches():
    ref=frame(['r'+str(i) for i in range(5)])
    ws=[(t,frame([f'{t}-{i}' for i in range(2)])) for t in range(3)]
    args=dict(bins={'x':NumericBins.fit([0,1,2])},groups=declared_groups({}),min_n=3)
    a=run_matched(ref,ws,policy='batch',**args)
    b=run_matched(ref,ws,policy='accumulate',**args)
    assert not any(r['eligible'] for r in a['tests'])
    assert [r['eligible'] for r in b['tests']]==[False,True,False]


def test_family_resolution_and_no_age_budget_reset():
    ref=frame(['r'+str(i) for i in range(10)])
    ws=[(t,frame([f'{t}-{i}' for i in range(3)])) for t in range(4)]
    args=dict(bins={'x':NumericBins.fit([0,1,2])},groups=declared_groups({'g':['a','absent']}),min_n=2,inferential=True,max_age=0,channels=2)
    with pytest.raises(ValueError,match='floor'):run_matched(ref,ws,draws=478,**args)
    o=run_matched(ref,ws,draws=479,**args)
    d=[r for r in o['decisions'] if r['scope']=='intersection' and r['method']=='PSI']
    assert all(r['family_size']==3 for r in d)
    assert sum(r['cutoff'] for r in d)==pytest.approx(.025)
    for w in range(1,5):
        pair=[r for r in o['decisions'] if r['look']==w and r['scope']=='intersection']
        assert pair[0]['cutoff']==pair[1]['cutoff'] and pair[0]['assessed']==pair[1]['assessed']


def test_nominal_ks_not_arbitrarily_ordered_and_unknowns_preserved():
    r=compare_block(['a','a'],['new',None],CategoryBins.fit(['a','b']),inferential=False,seed=0,draws=99,cutoff=.05)
    assert r['psi']>0 and r['ks_status']=='not_applicable_nominal' and r['ks_p'] is None
    assert r['missing_current']==1


@pytest.mark.parametrize('x,y',[(np.zeros(4),np.zeros(6)),([np.nan]*4,[np.nan]*6),([0]*4,[np.nan]*6),([0,0,1,1],[0,0,1,1,1,1]),([0,1,2,3],[-1e9,1e9,2,3,4,5])])
def test_constants_ties_missing_tails_unequal_counts(x,y):
    r=compare_block(x,y,NumericBins.fit([0,1,2]),inferential=True,seed=99,draws=99,cutoff=.05)
    assert np.isfinite(r['psi']) and 0<r['p']<=1 and 0<=r['ks_p']<=1
    assert r['ks_payload_bytes']==8*(len(x)+len(y))


def test_duplicate_roles_rejected():
    ref=frame(['shared','r'])
    with pytest.raises(ValueError,match='share record'):
        run_matched(ref,[(1,frame(['shared','c']))],bins={'x':NumericBins.fit([0,1])},groups=declared_groups({}),min_n=1)


def test_fallback_warning_is_conservative(monkeypatch):
    import warnings,subpsi.matched as module
    def fallback(a,b):warnings.warn('Exact calculation failed');return .0001
    monkeypatch.setattr(module,'ks_missing',fallback)
    r=compare_block([0,1],[9,10],NumericBins.fit([0,1]),inferential=True,seed=1,draws=99,cutoff=.05)
    assert r['ks_p']==1 and r['ks_warning'] and r['ks_status']=='conservative_warning'


def test_every_feature_gets_same_block_even_if_all_missing():
    ref=frame(['r'+str(i) for i in range(10)]);ref['z']=np.nan
    ws=[(t,frame([f'{t}-{i}' for i in range(2)])) for t in range(4)]
    for _,f in ws:f['z']=np.nan
    bins={'x':NumericBins.fit([0,1,2]),'z':NumericBins.fit([0,1,2])}
    out=run_matched(ref,ws,bins=bins,groups=declared_groups({}),min_n=3)
    for w in range(1,5):
        rows=[r for r in out['tests'] if r['look']==w]
        assert len({r['block_sha256'] for r in rows})==1
        assert len({r['n_current'] for r in rows})==1
        assert len({r['eligible'] for r in rows})==1
    assert [r['n_current'] for r in out['tests'] if r['feature']=='x']==[2,4,2,4]


def test_age_cap_applies_identically_to_both_statistics():
    ref=frame(['r'+str(i) for i in range(6)])
    ws=[(2016,frame(['a','b'],[10,11])),(2017,frame(['c'],[20])),(2018,frame(['d','e'],[30,31]))]
    out=run_matched(ref,ws,bins={'x':NumericBins.fit([0,1,2])},groups=declared_groups({}),min_n=3,max_age=0)
    assert not any(r['eligible'] for r in out['tests'])
    assert [r['dropped_old'] for r in out['schedule']]==[0,2,1]
    for w in range(1,4):
        pair=[r for r in out['decisions'] if r['look']==w and r['scope']=='aggregate']
        assert pair[0]['assessed']==pair[1]['assessed']==0
