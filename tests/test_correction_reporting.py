import importlib.util
from pathlib import Path
import pandas as pd


def test_stratified_paired_interval_handles_boolean_outcomes_and_keeps_cells_equal():
    path=Path(__file__).resolve().parents[1]/'scripts/correction/summarize.py'
    spec=importlib.util.spec_from_file_location('correction_summary',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    # Unequal cell counts deliberately distinguish a fixed-cell mean from pooling.
    rows=[dict(id=cell,repeat=i,method=method,outcome=value) for cell,n,value in [('a',2,True),('b',6,False)]
          for i in range(n) for method in ['PSI','KS']]
    d=pd.DataFrame(rows)
    one=module.stratified_interval(d,'outcome','PSI')
    assert one['estimate']==.5 and one['low']==.5 and one['high']==.5
    paired=module.stratified_interval(d,'outcome')
    assert paired['estimate']==0 and paired['degenerate']
