from pathlib import Path
import sys,json,time
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from subpsi.core import Group,NumericBins
from subpsi.revision4 import CollectionPlan
from subpsi.provenance import sha256
CONFIG=ROOT/'configs/low_compute/benchmark.json'
def configuration():return json.loads(CONFIG.read_text())
def definitions(c,target,aggregate=False):
 groups=[Group(x['name'],tuple(tuple(t) for t in x['selectors']),x['level']) for x in c['groups']]
 if aggregate:groups=[g for g in groups if g.level=='aggregate']
 bins={f:NumericBins(tuple(float(e) for e in b['edges'])) for f,b in c['bins'].items()}
 plan=CollectionPlan(tuple((g.name,target) for g in groups),c['min_reference'],c['horizon'])
 return dict(bins=bins,groups=groups,plan=plan,alpha=c['alpha'],draws=c['draws'],inferential=True,channels=c['channels'])
def frame(c,file):
 path=ROOT/file['path']
 if sha256(path)!=file['sha256']:raise ValueError('Replay hash mismatch')
 with np.load(path,allow_pickle=False) as a:
  result=pd.DataFrame(a['values'],columns=c['features'],index=a['ids'])
 if len(result)!=file['n']:raise ValueError('Record count changed')
 return result

def replays(c,cell,prefix=20):
 yield frame(c,cell['files'][0])
 for file in cell['files'][1:prefix+1]:yield file['look'],frame(c,file)
