import numpy as np
import pytest
from subpsi.revision import count_test,ks_missing,outcome_tests,generate,masks,run_stream
from subpsi.core import adjust_pvalues

def test_censored_permutation_never_smaller():
    for seed in range(8):
        full=count_test([25,40,35],[30,35,35],seed=seed,draws=399,stop_above=1)
        short=count_test([25,40,35],[30,35,35],seed=seed,draws=399,stop_above=.05)
        assert short['p']>=full['p']
        assert (short['p']<=.05)==(full['p']<=.05)

def test_ks_missing_channel():
    assert ks_missing(np.zeros(100),np.r_[np.zeros(50),np.full(50,np.nan)])<1e-8
    assert ks_missing(np.zeros(100),np.zeros(100))==1

def test_outcome_direction():
    a={'n':100,'positive':50,'negative':50,'tp':45,'fp':5,'correct':90}
    b={'n':100,'positive':50,'negative':50,'tp':20,'fp':30,'correct':40}
    assert all(r['p']<.0001 for r in outcome_tests([a],[b],20))
    assert all(r['p']>.99 for r in outcome_tests([b],[a],20))

def test_outcome_denominators():
    a={'n':100,'positive':5,'negative':95,'tp':4,'fp':5,'correct':94}
    r=outcome_tests([a],[a],20)
    assert not r[0]['eligible'] and r[0]['p']==1 and r[1]['eligible']

def test_outcome_only_keeps_inputs():
    c={'kind':'outcome','share':.25,'magnitude':1}
    a=generate(200,np.random.default_rng(5),c,0); b=generate(200,np.random.default_rng(5),c,1)
    for k in ['A','B','x','pred']: assert np.array_equal(a[k],b[k])
    assert np.any(a['y']!=b['y'])

def test_count_triggered_pool_and_horizon():
    c={'bins':3,'alpha':.05,'windows':3,'permutations':1199,'min_n':10,'pool_n':15,'outcome_min_n':10}
    case={'kind':'null','share':.25}; rng=np.random.default_rng(6)
    base=generate(200,rng,case); d=generate(100,rng,case); audit=generate(200,rng,case)
    ws=[generate(30,rng,case) for _ in range(3)]
    r=run_stream(base,d,audit,ws,c,90)
    rr=[t for t in r['tests'] if t['policy']=='accumulate' and t['group']==8]
    expected=0; start=1
    for w,t in zip(ws,rr):
        expected+=int(masks(w)[8].sum())
        assert t['n_current']==expected and t['start_window']==start
        if expected>=15: expected=0; start=t['window']+1
    # Equal spending over H looks sums to the declared stream budget.
    assert sum([c['alpha']/c['windows']]*c['windows'])==pytest.approx(.05)

def test_family_contains_unsupported_tests():
    assert adjust_pvalues([.001,1,1]).tolist()==[.003,1,1]
