"""Local fixtures only: no network and no main records/evaluation."""
import importlib.util,io,zipfile
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('oulad_extract',ROOT/'scripts/revision3/extract_oulad_metadata.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def fixture():
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(module.WANTED):z.writestr(name,'column\n1\n')
        z.writestr('studentVle.csv','unused\n')
    return b.getvalue()


def test_compact_members_are_original_bytes_and_stop_before_clicks():
    data=fixture();prefix,members,manifest=module.extract(io.BytesIO(data))
    assert data.startswith(prefix) and len(prefix)<len(data)
    assert set(members)==module.WANTED and all(v==b'column\n1\n' for v in members.values())
    assert len(manifest)==3


def test_truncated_prefix_fails():
    with pytest.raises(ValueError,match='Incomplete'):module.extract(io.BytesIO(fixture()[:20]))


def test_corrupt_member_crc_fails():
    data=bytearray(fixture());data[14]^=1
    with pytest.raises(ValueError,match='checksum'):module.extract(io.BytesIO(data))
