"""Read-only integrity check of the delivered evidence; standard library only.

This does not rerun experiments, rewrite receipts or certify their assumptions.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify(entries):
    for name, expected in entries.items():
        path = (ROOT/name).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError('Manifest path outside repository')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Evidence mismatch: '+name)
    return len(entries)


def main():
    checks = [
        ('records/revision4/RESULTS_FREEZE.json', 'files'),
        ('records/revision4/PREPARATION_MANIFEST.json', 'files'),
        ('records/correction/FREEZE.json', 'evidence_sha256'),
        ('results/summary/revision4/preparation-02/preserved_inventory.json', None),
    ]
    for name, key in checks:
        document = json.loads((ROOT/name).read_text())
        count = verify(document if key is None else document[key])
        print(f'PASS: {count} file hashes in {name}')
    print('Integrity verified without changing files. Numerical replay and source-cache checks are separate.')


if __name__ == '__main__':
    main()
