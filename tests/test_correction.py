import numpy as np
import pandas as pd
import pytest
from subpsi.core import NumericBins, psi_counts
from subpsi.correction import AttemptBins, TrainingMajority, restore_model
from subpsi.realdata import FrozenLogistic
from subpsi.matched import Group, run_matched


def test_known_quantile_collapse_is_fixed_without_fitting_later_data():
    design = np.repeat([0,1,2,3],[314,45,12,1])
    old = NumericBins.fit(design,6); fixed = AttemptBins()
    assert len(set(old.encode([0,1,2,3]))) == 1
    assert fixed.encode([0,1,2,3,100,np.nan]).tolist() == [0,1,2,2,2,3]
    assert fixed.counts(design).tolist() == [314,45,13,0]
    a,b = np.zeros(100),np.ones(100)
    assert psi_counts(old.counts(a),old.counts(b)) == 0
    assert psi_counts(fixed.counts(a),fixed.counts(b)) > 0


@pytest.mark.parametrize('bad', [[-1],[.5],[np.inf],[-np.inf],[[0,1]]])
def test_attempts_reject_invalid_count_values(bad):
    with pytest.raises(ValueError): AttemptBins().encode(bad)


def test_majority_rule_training_only_and_tie_fixed():
    model=TrainingMajority().fit([1,1,0])
    before=model.metadata()
    assert model.predict(pd.DataFrame({'label':[0,0,0]})).tolist()==[1,1,1]
    assert model.predict(pd.DataFrame({'label':[1,1,1]})).tolist()==[1,1,1]
    assert model.metadata()==before
    assert TrainingMajority().fit([0,1]).constant==0
    with pytest.raises(ValueError): TrainingMajority().fit([])


def test_saved_model_restores_predictions_without_refit():
    frame=pd.DataFrame({'num_of_prev_attempts':[0,0,1,2,1,3], 'studied_credits':[60,90,120,60,90,120], 'label':[0,1,0,1,1,0]})
    model=FrozenLogistic('oulad').fit(frame)
    copy=restore_model(model.metadata())
    assert np.array_equal(model.predict(frame),copy.predict(frame))
    assert model.metadata()==copy.metadata()


def test_count_correction_preserves_shared_ks_and_support():
    reference=pd.DataFrame({'x':[0]*60+[1]*30+[2]*10},index=[f'r{i}' for i in range(100)])
    windows=[(t,pd.DataFrame({'x':[1]*60},index=[f'{t}:{i}' for i in range(60)])) for t in [1,2]]
    kwargs=dict(groups=[Group('Everyone')],min_n=100,inferential=False)
    old=run_matched(reference,windows,bins={'x':NumericBins((-np.inf,0,np.inf))},**kwargs)
    new=run_matched(reference,windows,bins={'x':AttemptBins()},**kwargs)
    for a,b in zip(old['tests'],new['tests']):
        for k in ['eligible','n_current','block_sha256','opened_look','ks_d']:
            assert a[k]==b[k]
    assert new['tests'][1]['n_current']==120  # whole batch overshoot, for both tests
    assert new['tests'][1]['psi'] > old['tests'][1]['psi']
