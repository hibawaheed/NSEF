import numpy as np
import pandas as pd
import pytest
from subpsi.realdata import (acs_role,eligible_oulad,household_pool,constructed_stream,
    FrozenLogistic,audit_outcomes,paired_interval,wilson,validate_schema)
from subpsi.matched import declared_groups,run_matched
from subpsi.core import NumericBins


def test_role_assignment_is_household_not_row_or_order():
    keys=['2015:h1','2015:h2','2015:h1']
    got=[acs_role(k,2015) for k in keys]
    assert got[0]==got[2]
    assert list(reversed(got))==[acs_role(k,2015) for k in reversed(keys)]
    assert {acs_role(f'2015:{i}',2015) for i in range(100)}=={'fit','design','calibration'}


def test_oulad_day_zero_and_repeat_exclusion_uses_all_earlier_enrolments():
    info=pd.DataFrame({'code_module':['BBB']*7,'code_presentation':['2013J','2014J','2014J','2014J','2014J','2014J','2014J'],
                       'id_student':[1,1,2,3,4,5,6]})
    reg=info.copy();reg['date_registration']=[10,-5,-1,np.nan,-2,1,-2]
    reg['date_unregistration']=[np.nan,np.nan,0,np.nan,1,np.nan,np.nan]
    got=eligible_oulad(info,reg)
    assert set(got.id_student)=={4,6}  # Earlier-ineligible student's later repeat still removed.
    # No future assessment/outcome columns are consulted by eligibility.
    info['final_result']='Pass'
    assert eligible_oulad(info,reg).id_student.tolist()==got.id_student.tolist()
    with pytest.raises(ValueError,match='Duplicate'):
        eligible_oulad(pd.concat([info,info.iloc[:1]]),reg)


def pool_fixture():
    d=pd.DataFrame({'household_id':['a','a','b','c','d','e'], 'SPORDER':[2,1,1,1,1,1],
                    'SEX':[2,2,1,2,1,2], 'RAC1P':[2,2,1,2,1,2],
                    'AGEP':[10,20,30,40,50,60], 'SCHL':[1,2,3,4,5,6],
                    'label':[0,1,1,0,1,0]},index=list('abcdef'))
    return household_pool(d)


def test_household_representative_does_not_search_features_or_labels():
    p=pool_fixture()
    assert p.index.tolist()==list('bcdef')
    altered=p.copy();altered['label']=1-altered.label;altered['AGEP']=-100
    assert household_pool(altered).index.tolist()==p.index.tolist()


def test_constructed_intervention_whole_rows_same_groups_same_baseline():
    pool=pool_fixture();rep=pool.loc[pool.SEX.eq(2)].copy()
    rep.index=['2017:'+x for x in rep.index];rep['AGEP']+=100;rep['label']=1-rep.label
    r0,w0=constructed_stream(pool,rep,100,8,'unchanged',horizon=8,reference_n=90)
    r1,w1=constructed_stream(pool,rep,100,8,'substitution',horizon=8,reference_n=90)
    pd.testing.assert_frame_equal(r0,r1)
    assert r0.index.is_unique and r0.index.intersection(pd.concat([d for _,d in w0]).index).empty
    for (look,a),(_,b) in zip(w0,w1):
        pd.testing.assert_frame_equal(a[['SEX','RAC1P']],b[['SEX','RAC1P']])
        target=a.SEX.eq(2)&a.RAC1P.eq(2)
        if look<6: pd.testing.assert_frame_equal(a,b)
        else:
            pd.testing.assert_frame_equal(a.loc[~target],b.loc[~target])
            for _,row in b.loc[target].iterrows():
                expected=rep.loc[row.source_id]
                for col in rep.columns: assert row[col]==expected[col]
    assert len(set(r0.source_id))<len(r0)  # Explicit replacement sampling, distinct draw IDs.


def test_baseline_transforms_and_coefficients_are_frozen():
    rng=np.random.default_rng(55)
    fit=pd.DataFrame({'AGEP':rng.integers(16,90,200),'SCHL':rng.integers(1,5,200),'label':rng.integers(0,2,200)})
    model=FrozenLogistic('acs').fit(fit);before=model.metadata()
    future=fit.iloc[:8].copy();future['SCHL']=99;future['AGEP']=500;future['label']=3
    pred=model.predict(future)
    assert set(pred)<= {0,1} and model.metadata()==before
    assert np.all(model.transform(future)[:,3:]==0)  # Future category cannot modify historical vocabulary.
    # Deliberately changing future labels has no effect on predictions.
    future['label']=0;assert np.array_equal(pred,model.predict(future))
    assert model.fit_info['max_abs_gradient']<.001


def test_constant_numeric_predictor_is_finite_with_l2():
    d=pd.DataFrame({'num_of_prev_attempts':[0]*40,'studied_credits':[60]*40,'label':[0,1]*20})
    m=FrozenLogistic('oulad').fit(d)
    assert np.isfinite(m.coef).all() and (m.scale==1).all()


def test_outcome_gaps_need_each_relevant_denominator():
    class Prediction:
        def predict(self,d): return d.pred.to_numpy()
    base=pd.DataFrame({'A':[0]*40+[1]*40,'label':[0,1]*40,'pred':[0]*40+[1]*40})
    cur=base.copy();cur['pred']=1-cur.pred
    groups=declared_groups({'A':[0,1]})
    rows=pd.DataFrame(audit_outcomes(base,cur,groups,Prediction()))
    r=rows.query("group == 'A=0' and metric == 'TPR'").iloc[0]
    assert r.baseline_gap==-1 and r.current_gap==1 and r.gap_change==2
    assert r.baseline_denominator==20
    small=cur.iloc[1:].copy()
    rows=pd.DataFrame(audit_outcomes(base,small,groups,Prediction()))
    r=rows.query("group == 'A=0' and metric == 'FPR'").iloc[0]
    assert r.gap_status=='insufficient_denominator' and pd.isna(r.gap_change)
    assert rows.query("group == 'Everyone'").gap_status.eq('not_applicable').all()


def test_control_intervals_use_paired_streams_and_flag_ties():
    same=paired_interval([0,1,0,1],[0,1,0,1])
    assert same['difference']==0 and same['low']==0 and same['degenerate']
    contrast=paired_interval([1,1,1,1],[0,0,0,0])
    assert contrast['difference']==1 and contrast['n_pairs']==4
    low,high=wilson(0,30)
    assert low==0 and .11<high<.12  # Zero observed alerts does not prove zero risk.
    with pytest.raises(ValueError):paired_interval([1],[1,2])


def test_unknown_group_or_nonfinite_feature_stops_loader():
    with pytest.raises(ValueError,match='group code'):
        validate_schema(pd.DataFrame({'x':[1], 'A':[3]}),['x'],{'A':[1,2]})
    with pytest.raises(ValueError,match='missing'):
        validate_schema(pd.DataFrame({'x':[np.nan], 'A':[1]}),['x'],{'A':[1,2]})


def test_minimum_100_sensitivity_separates_support_from_accumulation():
    ref=pd.DataFrame({'x':np.arange(200.),'A':[1]*200},index=[f'r{i}' for i in range(200)])
    frames=[(i,pd.DataFrame({'x':np.arange(60.),'A':[1]*60},index=[f'w{i}:{j}' for j in range(60)])) for i in [1,2]]
    kw=dict(reference=ref,windows=frames,bins={'x':NumericBins.fit(ref.x,6)},groups=declared_groups({'A':[1]}))
    ordinary=run_matched(**kw,min_n=100,policy='batch')
    accum=run_matched(**kw,min_n=100,policy='accumulate')
    assert not any(r['eligible'] for r in ordinary['tests'])
    assert [r['n_current'] for r in accum['tests'] if r['eligible']]==[120,120]
    for result in [ordinary,accum]:
        assert all(d['alert'] is None for d in result['decisions'])
        assert all(r['p'] is None and r['ks_p'] is None for r in result['tests'])
