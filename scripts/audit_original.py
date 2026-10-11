#!/usr/bin/env python3
"""Software-only fixtures exposing original defects; no research trials."""
import importlib.util,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('original',ROOT/'legacy/subgroup_psi_original.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
a=np.array([0.,1.,2.,3.]); b=np.array([100.,101.,102.,103.])
edges=np.percentile(a,np.linspace(0,100,3)); edges[0]-=1e-9; edges[-1]+=1e-9
report={'original_outlier_fixture':{'reference':a.tolist(),'current':b.tolist(),'counted_current':int(np.histogram(b,edges)[0].sum()),'actual_current':len(b),'psi':module.calculate_psi(a,b,bins=2)},
        'empty_reference_exception':None,'zero_pvalue_fixture':None}
try: module.calculate_psi([],b)
except Exception as exc: report['empty_reference_exception']=repr(exc)
np.random.seed(42)
report['zero_pvalue_fixture']=module.psi_permutation_pvalue(np.zeros(10),np.ones(10),module.calculate_psi(np.zeros(10),np.ones(10),bins=2),bins=2,n_perm=19)
(ROOT/'records/original_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
