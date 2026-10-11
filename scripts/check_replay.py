#!/usr/bin/env python3
"""Compare separately executed smoke/main outputs using preselected seed 0."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for scenario in ['S0','S1','S2','S3','S4','S5']:
    a=json.loads((ROOT/f'results/raw/smoke-v1/{scenario}_0000.json').read_text())
    b=json.loads((ROOT/f'results/raw/synthetic-v1/{scenario}_0000.json').read_text())
    a.pop('runtime_seconds');b.pop('runtime_seconds')
    assert a==b, f'Numerical replay mismatch: {scenario}'
print('All six separately executed smoke/main seed-0 outputs match exactly (excluding runtime).')
