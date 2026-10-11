#!/usr/bin/env python3
"""Run a local check and append its actual command, timing, output and exit code."""
import argparse,datetime,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('command',nargs=argparse.REMAINDER);args=p.parse_args()
command=args.command[1:] if args.command and args.command[0]=='--' else args.command
if not command:raise SystemExit('Supply a command after --')
started=datetime.datetime.now(datetime.timezone.utc).isoformat();start=time.perf_counter()
process=subprocess.Popen(command,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=1)
lines=[]
for line in process.stdout:
 print(line,end='',flush=True);lines.append(line)
returncode=process.wait()
result=subprocess.CompletedProcess(command,returncode,''.join(lines))
record={'started_at_utc':started,'cwd':str(ROOT),'argv':command,'exit_code':result.returncode,'elapsed_seconds':time.perf_counter()-start}
log=ROOT/'records/validation_commands.json';existing=json.loads(log.read_text()) if log.exists() else [];existing.append(record);log.write_text(json.dumps(existing,indent=2)+'\n')
with (ROOT/'records/validation_output.txt').open('a') as output:
 output.write(json.dumps(record)+'\n'+result.stdout.rstrip()+'\n')
raise SystemExit(result.returncode)
