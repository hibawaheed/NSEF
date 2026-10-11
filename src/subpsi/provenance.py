import hashlib,json,platform,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
import importlib.metadata


def sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path,data):
    Path(path).write_text(json.dumps(data,indent=2,allow_nan=False,sort_keys=True)+'\n')


def environment():
    return {"python":sys.version,"platform":platform.platform(),"processor":platform.processor(),
            "versions":{m:importlib.metadata.version(m) for m in ['numpy','pandas','scipy','matplotlib','pytest','statsmodels']}}


def source_hashes(root):
    return {str(p.relative_to(root)):sha256(p) for directory in ['src','scripts','configs'] for p in sorted((root/directory).rglob('*')) if p.is_file() and '__pycache__' not in str(p)}


def manifest(root,config_path):
    return {"created_at_utc":datetime.now(timezone.utc).isoformat(),"config_sha256":sha256(config_path),
            "environment":environment(),"source_hashes":source_hashes(root),
            "git_head":subprocess.run(['git','rev-parse','--verify','HEAD'],cwd=root,capture_output=True,text=True).stdout.strip() or None,
            "ai_role":"AI-assisted code, tests, and plotting; numbers computed by executable code"}


def verify_inputs(base,entries):
    for name,expected in entries.items():
        if sha256(Path(base)/name)!=expected: raise ValueError(f'provenance hash mismatch: {name}')


def save_snapshot(root,out):
    import zipfile
    target=Path(out)/'source_snapshot.zip'
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        names=list(source_hashes(root))+['pyproject.toml','requirements-lock.txt']
        for name in names:
            path=Path(root)/name
            if path.exists(): archive.write(path,name)
    return sha256(target)
