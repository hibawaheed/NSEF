import json
import numpy as np
import pandas as pd
import pytest
from scipy.stats import permutation_test
from statsmodels.stats.multitest import multipletests
from subpsi.core import (NumericBins,CategoryBins,psi_counts,psi_probabilities,proportions,
 permutation_test_counts,adjust_pvalues,compare,Group,union_groups,decisions,validate_resolution)
from subpsi.scenarios import generate,assert_disjoint,fit_logistic,predict
from subpsi.provenance import verify_inputs,sha256


def test_known_two_bin():
    assert psi_probabilities([.5,.5],[.2,.8]) == pytest.approx(.3*np.log(4))


def test_equal_histograms():
    assert psi_counts([40,60],[40,60])==0


@pytest.mark.parametrize('a,b',[([1,4],[8,2]),([0,0,5],[0,8,1]),([3,9,4],[4,9,3])])
def test_symmetry_and_nonnegative(a,b):
    assert psi_counts(a,b)>=-1e-12
    assert psi_counts(a,b)==pytest.approx(psi_counts(b,a))


def test_normalization_unequal_totals():
    assert proportions([0,3,7]).sum()==pytest.approx(1)
    assert proportions([0,30,70]).sum()==pytest.approx(1)
    assert np.isfinite(psi_counts([0,3,7],[0,30,70]))


def test_numeric_outliers_missing():
    b=NumericBins.fit([0,1,2,3],n_bins=3)
    assert b.counts([-1e100,1e100,np.nan]).sum()==3
    assert b.counts([np.nan])[-1]==1


def test_constant_bins_separate_equal_and_shifted():
    b=NumericBins.fit([7,7,7])
    assert len(set(b.encode([6,7,8])))==3


def test_quantile_ties():
    b=NumericBins.fit([0]*20+[1]*20)
    assert np.all(np.diff(b.edges)>0)
    assert b.counts([0,1,2]).sum()==3


@pytest.mark.parametrize('x',[[],[np.nan],[np.inf]])
def test_invalid_design(x):
    with pytest.raises(ValueError): NumericBins.fit(x)


def test_category_unknown_missing():
    b=CategoryBins.fit(['low','high',None])
    c=b.counts(['low','new',None])
    assert c.sum()==3 and c[-2]==1 and c[-1]==1
    with pytest.raises(ValueError): b.encode([1,2])


def test_empty_histogram():
    with pytest.raises(ValueError): psi_counts([0,0],[2,3])


def test_small_reference_and_absent_groups():
    a=pd.DataFrame({'x':[1,2,3],'g':['old','tiny','old']})
    b=pd.DataFrame({'x':[1]*100,'g':['new']*50+['tiny']*50})
    groups=union_groups(a,b,['g'],predefined=[Group('absent',(('g','absent'),),'single')])
    rows=compare(a,b,{'x':NumericBins.fit([0,1,2,3])},groups,min_n=10)
    assert all(r['status']=='insufficient_evidence' for r in rows)
    assert all(r['pvalue']==1 and r['psi'] is None for r in rows)
    assert {r['group'] for r in rows}=={'all',"g='new'","g='old'","g='tiny'",'absent'}
    assert not decisions(rows)['B2']['alert']


def test_exact_permutation_against_scipy():
    a=np.array([0,0,1]); b=np.array([1,1])
    def statistic(x,y): return psi_counts(np.bincount(x.astype(int),minlength=2),np.bincount(y.astype(int),minlength=2))
    standard=permutation_test((a,b),statistic,vectorized=False,n_resamples=np.inf,alternative='greater')
    result=permutation_test_counts([2,1],[0,2])
    assert result['exact'] and result['pvalue']==pytest.approx(standard.pvalue)


def test_randomized_deterministic_and_floor():
    kwargs=dict(n_resamples=199,seed=123,exact_limit=0)
    a=permutation_test_counts([100,0],[0,100],**kwargs)
    assert a==permutation_test_counts([100,0],[0,100],**kwargs)
    assert a['pvalue']>=1/200 and a['pvalue']>0


def test_permutation_ties_equal_statistic():
    assert permutation_test_counts([4,4],[4,4],n_resamples=99,exact_limit=0)['pvalue']==1


def test_count_sampler_matches_exact_null():
    exact=permutation_test_counts([3,0],[1,3])['pvalue']
    sampled=permutation_test_counts([3,0],[1,3],n_resamples=40000,exact_limit=0,seed=928)['pvalue']
    assert abs(exact-sampled)<.015  # one deterministic algorithm cross-check; not a calibration study


@pytest.mark.parametrize('method,standard',[('holm','holm'),('bh','fdr_bh'),('by','fdr_by')])
def test_multiplicity_against_standard(method,standard):
    p=np.r_[0,.001,.03,.03,1,np.random.default_rng(19).uniform(size=25)]
    assert np.allclose(adjust_pvalues(p,method),multipletests(p,method=standard)[1])


def test_resolution_guard():
    with pytest.raises(ValueError): validate_resolution(99,18)
    validate_resolution(1999,18)


def test_labels_cannot_change_detection():
    rng=np.random.default_rng(8)
    a=generate(80,rng,role='a'); b=generate(80,rng,role='b')
    bins={'signal':NumericBins.fit(rng.normal(size=100))}; groups=[Group('all')]
    kwargs=dict(min_n=20,n_resamples=99,seed=19)
    first=compare(a,b,bins,groups,**kwargs)
    b['y']=1-b.y
    assert first==compare(a,b,bins,groups,**kwargs)


def test_data_role_disjointness():
    a=generate(10,np.random.default_rng(1),role='a'); b=generate(10,np.random.default_rng(2),role='b')
    assert_disjoint(a,b)
    with pytest.raises(ValueError): assert_disjoint(a,a.copy())


def test_outcome_only_intervention_keeps_inputs():
    a=generate(100,np.random.default_rng(1),'S4',False,role='a')
    b=generate(100,np.random.default_rng(1),'S4',True,role='a')
    pd.testing.assert_frame_equal(a.drop(columns='y'),b.drop(columns='y'))
    assert (a.y!=b.y).any()


def test_benign_feature_not_in_model():
    a=generate(100,np.random.default_rng(2)); m=fit_logistic(a)
    b=a.copy(); b['nuisance']+=100
    assert np.array_equal(predict(m,a),predict(m,b))


def test_provenance_rejects_tampering(tmp_path):
    p=tmp_path/'data.csv'; p.write_text('a,b\n1,2\n'); entries={'data.csv':sha256(p)}
    verify_inputs(tmp_path,entries); p.write_text('changed')
    with pytest.raises(ValueError): verify_inputs(tmp_path,entries)


@pytest.mark.parametrize('values',[[np.nan],[-.1],[1.1]])
def test_invalid_pvalues(values):
    with pytest.raises(ValueError): adjust_pvalues(values)


def test_supplied_original_is_preserved():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    inventory=json.loads((root/'records/input_inventory.json').read_text())
    expected=next(f['sha256'] for f in inventory['files'] if f['name']=='subgroup_psi.py')
    assert sha256(root/'legacy/subgroup_psi_original.py')==expected


def test_missing_group_stays_visible():
    a=pd.DataFrame({'g':['x',None],'x':[1,2]})
    b=pd.DataFrame({'g':['x',None],'x':[1,3]})
    groups=union_groups(a,b,['g'])
    missing=next(g for g in groups if g.selectors==(('g',None),))
    assert missing.mask(a).tolist()==[False,True]
