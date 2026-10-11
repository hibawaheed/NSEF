"""Fetch only the leading OULAD ZIP members needed for the compact cohort study.

Reads local ZIP headers, verifies CRC and uncompressed sizes, preserves the
exact downloaded byte prefix. Does not require downloading the 433 MB click
log. --prefix may reuse the beginning of an existing official download.
"""
import argparse,datetime,hashlib,json,struct,urllib.request,zlib,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
URL='https://archive.ics.uci.edu/static/public/349/open+university+learning+analytics+dataset.zip'
WANTED={'courses.csv','studentInfo.csv','studentRegistration.csv'}

def extract(stream):
    prefix=bytearray();members={};manifest=[]
    def read(n):
        data=stream.read(n)
        if len(data)!=n:raise ValueError('Incomplete source prefix')
        prefix.extend(data);return data
    while set(members)!=WANTED:
        start=len(prefix);h=read(30);sig,version,flags,compression,_,_,crc,compressed,uncompressed,nlen,extra=struct.unpack('<IHHHHHIIIHH',h)
        if sig!=0x04034b50 or flags&9 or compression not in (0,8):raise ValueError('Unsupported ZIP format; use full archive fetch')
        name=read(nlen).decode();read(extra)
        if compressed>10_000_000:raise ValueError('Required tables not in compact prefix; use full archive fetch')
        data=read(compressed)
        if name in WANTED:
            content=zlib.decompress(data,-15) if compression==8 else data
            if len(content)!=uncompressed or zlib.crc32(content)!=crc:raise ValueError('Member checksum/size failure')
            members[name]=content;manifest.append({'name':name,'offset':start,'compressed_bytes':compressed,'bytes':len(content),'crc32':crc,'sha256':hashlib.sha256(content).hexdigest()})
    return bytes(prefix),members,manifest

def main():
    p=argparse.ArgumentParser();p.add_argument('--prefix',type=Path);a=p.parse_args()
    out=ROOT/'data/raw/revision3/oulad/metadata';out.mkdir(parents=True,exist_ok=False)
    with (a.prefix.open('rb') if a.prefix else urllib.request.urlopen(URL,timeout=60)) as response:
        prefix,members,manifest=extract(response)
    (out/'source-prefix.bin').write_bytes(prefix)
    for name,data in members.items():(out/name).write_bytes(data)
    receipt={'source_url':URL,'accessed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'download_method':'leading ZIP members; full-archive hash unavailable by design','prefix_bytes':len(prefix),'prefix_sha256':hashlib.sha256(prefix).hexdigest(),'members':manifest,'purpose':'compact schema/support study; no clicks/assessment values read as research features'}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('Verified original ZIP member CRCs and saved',len(prefix),'source bytes;',len(members),'tables')
if __name__=='__main__':main()
