"""Fixed teaching fixtures only: these tests are not research experiments."""
from copy import deepcopy
from dataclasses import FrozenInstanceError
import numpy as np
import pandas as pd
import pytest

from subpsi.core import NumericBins, proportions, psi_counts
from subpsi.correction import AttemptBins, TrainingMajority
from subpsi.matched import declared_groups, run_matched
from subpsi.revision4 import (CollectionPlan, FrozenTargetScheduler, representation_audit,
    outcome_metrics, augment_saved_outcomes, run_frozen_targets, select_targets,
    wilson_lower, calibration_role, validate_role_separation, draw_whole_records, validate_draw_lineage)


def test_zero_heavy_representation_detects_old_collapse_and_corrects_shift():
    historical = [0]*90 + [1]*7 + [2]*3
    old = NumericBins.fit(historical, 6); new = AttemptBins()
    before = representation_audit(historical, old)
    after = representation_audit(historical, new)
    assert before['status'] == 'collapsed_nonconstant'
    assert before['n_distinct_observed'] == 3 and before['largest_bin_proportion'] == 1
    assert before['effective_bin_count'] == 1
    assert after['status'] == 'represented' and after['occupied_numeric_bins'] == 3
    assert after['effective_bin_count'] > 1 and after['largest_bin_proportion'] == .9
    changed = [0]*70 + [1]*27 + [2]*3
    assert psi_counts(old.counts(historical),old.counts(changed)) == 0
    assert psi_counts(new.counts(historical),new.counts(changed)) > 0


def test_count_tails_missing_conservation_and_normalized_smoothing():
    b = AttemptBins(); x = [0,1,2,100000,np.nan]
    assert b.edges[0] == -np.inf and b.edges[-1] == np.inf
    assert b.counts(x).tolist() == [1,1,2,1]
    assert b.counts(x).sum() == len(x)
    assert proportions(b.counts(x)).sum() == pytest.approx(1.)
    assert np.isfinite(proportions(b.counts([0]))).all()
    a = representation_audit(x,b)
    assert a['occupied_bins'] == 4 and a['n_missing'] == 1


@pytest.mark.parametrize('x', [[-1],[.5],[np.inf],[-np.inf],[[1,2]]])
def test_invalid_counts(x):
    with pytest.raises(ValueError): representation_audit(x,AttemptBins())


def test_constant_and_all_missing_are_explicit_not_binning_failures():
    a = representation_audit([0,0,np.nan],AttemptBins())
    assert a['status'] == 'constant_design' and not a['nonconstant_collapse']
    assert a['effective_bin_count'] == 1
    missing = representation_audit([np.nan],AttemptBins())
    assert missing['status'] == 'no_observed_values' and missing['effective_bin_count'] is None


def test_balanced_accuracy_uses_both_denominators():
    rows = {r['metric']:r for r in outcome_metrics(484,547,369,426)}
    assert rows['Accuracy']['value'] == pytest.approx(541/973)
    assert rows['Balanced accuracy']['value'] == pytest.approx(.5*(484/547+57/426))
    assert rows['Balanced accuracy']['denominator'] is None
    assert rows['Balanced accuracy']['positives'] == 547
    baseline = {r['metric']:r for r in outcome_metrics(547,547,426,426)}
    assert baseline['Accuracy']['value'] == pytest.approx(547/973)
    assert baseline['Balanced accuracy']['value'] == .5
    missing = outcome_metrics(0,0,5,100)[-1]
    assert missing['value'] is None and not missing['mathematically_defined']
    small = outcome_metrics(1,2,10,100)[-1]
    assert small['value'] is None and small['mathematically_defined']
    with pytest.raises(ValueError): outcome_metrics(2,1,0,1)


def test_saved_counts_must_be_consistent():
    rows = []
    for metric,n,d in [('TPR',8,10),('FPR',3,10),('Accuracy',15,20)]:
        row = dict(model='fixture',time=1,group='Everyone',level='aggregate',metric=metric)
        for period in ['baseline','current']:
            row.update({period+'_numerator':n,period+'_denominator':d,
                        period+'_complement_numerator':0,period+'_complement_denominator':0})
        rows.append(row)
    out = augment_saved_outcomes(pd.DataFrame(rows),minimum=1)
    assert len(out) == 16
    assert out.query("metric == 'Balanced accuracy' and subset == 'group'").value.tolist() == [.75,.75]
    rows[-1]['current_numerator'] = 16
    with pytest.raises(ValueError,match='Inconsistent'): augment_saved_outcomes(pd.DataFrame(rows))


def test_majority_is_fixed_by_training_only_even_if_evaluation_majority_reverses():
    m = TrainingMajority().fit([0,1,1]); before = deepcopy(m.metadata())
    assert m.predict(pd.DataFrame({'label':[0]*10})).tolist() == [1]*10
    assert m.metadata() == before
    assert TrainingMajority().fit([0,1]).predict([None])[0] == 0


def test_plan_copies_mutable_input_and_is_frozen():
    values = [['a',2]]; plan = CollectionPlan(values,1,2); old = plan.sha256
    values[0][1] = 99
    assert plan.targets == (('a',2),) and plan.sha256 == old
    with pytest.raises(FrozenInstanceError): plan.horizon = 10


def test_group_targets_separate_reference_gate_whole_batch_overshoot_and_no_reuse():
    p = CollectionPlan((('a',2),('b',4),('short',1)),2,3)
    s = FrozenTargetScheduler({'a':2,'b':2,'short':1},p)
    blocks = s.advance(1,{'a':['x','y','z'],'b':['x','y','z'],'short':['x']})
    assert [b.ready for b in blocks] == [True,False,False]
    assert blocks[0].ids == ('x','y','z')  # whole batch, not silently truncated
    next_blocks = s.advance(2,{'a':['q'],'b':['q'],'short':[]})
    assert next_blocks[0].ids == ('q',)  # prior completed block is never reused
    assert next_blocks[1].ready and next_blocks[1].reference_n < len(next_blocks[1].ids)
    assert next_blocks[1].ids == ('x','y','z','q')
    assert next_blocks[2].ids == ('x',) and not next_blocks[2].ready
    with pytest.raises(ValueError,match='repeated'): s.advance(3,{'a':['x'],'b':[],'short':[]})
    assert s.look == 2  # rejected input has not mutated state
    s.advance(3,{'a':[],'b':[],'short':[]})
    with pytest.raises(ValueError,match='horizon'): s.advance(4,{'a':[],'b':[],'short':[]})


def test_batch_discards_unsupported_data_without_restarting_clock():
    s = FrozenTargetScheduler({'a':10},CollectionPlan((('a',2),),1,3,'batch'))
    assert not s.advance(1,{'a':['x']})[0].ready
    assert s.advance(2,{'a':['y']})[0].ids == ('y',)
    assert s.advance(3,{'a':['z','q']})[0].ready
    assert s.look == 3


@pytest.mark.parametrize('counts,targets,minimum,horizon', [({'a':1},(('b',1),),1,2),
    ({'a':1},(('a',0),),1,2),({'a':1},(('a',1),),0,2),({'a':-1},(('a',1),),1,2),
    ({'a':1},(('a',1),),1,0),({'a':1},(('a',True),),1,2)])
def test_invalid_fixed_plans(counts,targets,minimum,horizon):
    with pytest.raises(ValueError): FrozenTargetScheduler(counts,CollectionPlan(targets,minimum,horizon))


def fixture_inputs():
    ref = pd.DataFrame({'x':[0,1,0,1,2,3],'A':[0,1,0,1,0,1]},index=[f'r{i}' for i in range(6)])
    windows = [(i,pd.DataFrame({'x':[i,2*i],'A':[0,1],'label':[0,1]},index=[f'w{i}a',f'w{i}b'])) for i in range(1,5)]
    return ref,windows,{'x':NumericBins.fit([0,1,2,3],2)},declared_groups({'A':[0,1,2]})


def test_matched_engine_constant_map_replays_old_scheduler_and_inference():
    ref,windows,bins,groups = fixture_inputs()
    old = run_matched(ref,windows,bins=bins,groups=groups,min_n=2,draws=399,inferential=True)
    plan = CollectionPlan(tuple((g.name,2) for g in groups),2,len(windows))
    new = run_frozen_targets(ref,windows,bins=bins,groups=groups,plan=plan,draws=399,inferential=True)
    for a,b in zip(old['tests'],new['tests']):
        for key in ['n_reference','n_current','block_sha256','eligible','opened_look','psi','p','ks_p','ks_d']:
            assert a[key] == b[key]
    for a,b in zip(old['decisions'],new['decisions']):
        for key in ['alert','hits','family_size','cutoff','adjusted_pvalues','assessed']:
            assert a[key] == b[key]
    assert {d['cutoff'] for d in new['decisions']} == {.05/4}
    assert {d['family_size'] for d in new['decisions'] if d['scope']=='intersection'} == {4}
    unsupported = [r for r in new['tests'] if r['group']=='A=2']
    assert all(r['p']==r['ks_p']==1 and r['historical_shortage'] for r in unsupported)


def test_feature_and_outcome_perturbation_cannot_change_map_or_schedule():
    ref,windows,bins,groups = fixture_inputs()
    plan = CollectionPlan(tuple((g.name,2 if g.level=='aggregate' else 3) for g in groups),2,4)
    a = run_frozen_targets(ref,windows,bins=bins,groups=groups,plan=plan)
    altered = [(t,f.assign(x=-1000*f.x,label=1-f.label)) for t,f in windows]
    b = run_frozen_targets(ref,altered,bins=bins,groups=groups,plan=plan)
    clean = lambda out:[{k:v for k,v in row.items() if not k.endswith('seconds_all_groups')} for row in out['schedule']]
    assert clean(a) == clean(b) and a['metadata']['plan_sha256'] == b['metadata']['plan_sha256']
    assert [r['psi'] for r in a['tests']] != [r['psi'] for r in b['tests']]


def test_matched_input_validation_and_resolution():
    ref,windows,bins,groups = fixture_inputs()
    plan = CollectionPlan(tuple((g.name,2) for g in groups),2,4)
    with pytest.raises(ValueError,match='floor'):
        run_frozen_targets(ref,windows,bins=bins,groups=groups,plan=plan,draws=10,inferential=True)
    windows[0][1].index = ['r0','w1b']
    with pytest.raises(ValueError,match='cross'):
        run_frozen_targets(ref,windows,bins=bins,groups=groups,plan=plan)


def calibration_cells():
    return [dict(stage='selection',group=g,incoming_n=n,reference_n=100,scenario=s,method=m,
                 successes=99 if n==200 or (g=='a' and n==50) else 20,repeats=100)
            for g in ['a','b'] for n in [50,100,200] for s in ['modest','large'] for m in ['PSI','KS']]


def choose(cells):
    return select_targets(cells,groups=['a','b','short'],grid=[50,100,200],
                          design_scenarios=['modest','large'],reference_n=100,
                          historically_supported={'a':True,'b':True,'short':False})


def test_selection_uses_weaker_method_all_designs_and_does_not_assume_monotonicity():
    rows = calibration_cells(); out = choose(rows)
    assert [r['target'] for r in out['group_targets']] == [50,200,200]
    assert out['global_target'] == 200
    assert out['group_targets'][-1]['status'] == 'historical_calibration_shortage'
    rows[0]['successes'] = 0
    assert choose(rows)['group_targets'][0]['target'] == 200
    assert choose(list(reversed(rows))) == choose(rows)
    for r in rows: r['successes'] = 0
    failed = choose(rows)
    assert failed['group_targets'][0]['status'] == 'target_not_met_within_grid'
    assert failed['global_status'] == 'criterion_unmet_fallback'


def test_validation_cannot_select_and_missing_cells_do_not_silently_drop_groups():
    rows = calibration_cells()
    with pytest.raises(ValueError,match='Missing'): choose(rows[1:])
    with pytest.raises(ValueError,match='Duplicate'): choose(rows+rows[:1])
    rows[0]['stage'] = 'validation'
    with pytest.raises(ValueError,match='selection-stage'): choose(rows)
    rows[0]['scenario'] = 'unused_stress'
    with pytest.raises(ValueError,match='selection-stage'): choose(rows)
    assert wilson_lower(0,100) == pytest.approx(0)
    assert wilson_lower(100,100) > .95


def test_unit_roles_disjoint_and_deterministic():
    d = pd.DataFrame({'household_id':['h1','h1','h2'],'role':['selection','selection','validation']})
    assert validate_role_separation(d,'household_id')['units'] == 2
    assert calibration_role('h1') == calibration_role('h1')
    d.loc[1,'role'] = 'validation'
    with pytest.raises(ValueError,match='conflicting'): validate_role_separation(d,'household_id')
    students = pd.DataFrame({'id_student':[1,2,1],'role':['fit','audit','monitor']})
    with pytest.raises(ValueError,match='conflicting'): validate_role_separation(students,'id_student')


def test_whole_record_draw_lineage_retains_correlated_features_labels_and_repeats():
    pool = pd.DataFrame({'age':[20,70],'A':[0,1],'label':[1,0]},index=['p1','p2'])
    d = draw_whole_records(pool,10,np.random.default_rng(3),prefix='reference',weights=[1,4])
    summary = validate_draw_lineage(d,pool)
    assert summary['draws'] == 10 and summary['distinct_source_units'] <= 2
    assert summary['repeated_source_draws'] >= 8
    d.loc[d.index[0],'label'] = 1-d.iloc[0].label
    with pytest.raises(ValueError,match='differs'): validate_draw_lineage(d,pool)


def test_independent_same_pool_null_draws_have_distinct_namespaces():
    pool = pd.DataFrame({'x':[0,1,2]},index=['p1','p2','p3'])
    seeds = np.random.SeedSequence(17).spawn(2)
    a = draw_whole_records(pool,10,np.random.default_rng(seeds[0]),prefix='reference')
    b = draw_whole_records(pool,10,np.random.default_rng(seeds[1]),prefix='current')
    assert not set(a.index).intersection(b.index)
    assert set(a.source_id).issubset(pool.index) and set(b.source_id).issubset(pool.index)
    assert a.source_id.tolist() != b.source_id.tolist()
    validate_draw_lineage(a,pool); validate_draw_lineage(b,pool)
