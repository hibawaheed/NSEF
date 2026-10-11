#!/usr/bin/env python3
"""Validate all figure artifacts and their links to saved experiment manifests."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from subpsi.provenance import verify_inputs,sha256

p=argparse.ArgumentParser(); p.add_argument('--figures',default='figures/report'); args=p.parse_args()
out=ROOT/args.figures; index=json.loads((out/'index.json').read_text()); verify_inputs(ROOT,index['run_manifests'])
assert sha256(out/'SubPSI_chart_pack.pdf')==index['chart_pack_sha256']
for entry in index['figures']:
    name=entry['name']; meta=json.loads((out/(name+'.manifest.json')).read_text())
    verify_inputs(out,meta['files']); verify_inputs(ROOT,meta['source_run_manifests'])
    for source in meta['source_run_manifests']:
        manifest=json.loads((ROOT/source).read_text()); verify_inputs((ROOT/source).parent,manifest['result_hashes'])
    from PIL import Image
    im=Image.open(out/(name+'.png'))
    assert min(im.info.get('dpi',(0,0)))>=299
    assert im.width>=1500 and im.height>=1000
    assert (out/(name+'.pdf')).read_bytes().startswith(b'%PDF-')
    assert len((out/(name+'.csv')).read_text().splitlines())>1
print(f"Validated {len(index['figures'])} figures: PDF/SVG/300 dpi PNG, CSV, manifest and source-run hashes.")
