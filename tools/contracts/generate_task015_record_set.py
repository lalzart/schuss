#!/usr/bin/env python3
"""Generate the schema-only Task 015 successor record set."""
from __future__ import annotations
import argparse, copy, hashlib, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'tools/contracts'))
import record_set_rules, validator_core as core
PARENT=ROOT/'contracts/record-sets/task014-build-execution-v1.json'
OUTPUT=ROOT/'contracts/record-sets/task015-minimal-direct-frontend-v1.json'
PATHS=('schemas/direct-frontend-result-v0.schema.json','schemas/normalized-dsp-module-v0.schema.json')
def generated_bytes():
 p=core.load_json(PARENT)
 def member(rel):
  s=core.load_json(ROOT/rel); return {'schema_version':s['$id'].removesuffix('.schema.json'),'portable_path':rel,'byte_sha256':core.sha256_file(ROOT/rel)}
 m={'schema_version':'record-set-v0','canonical_profile':'schuss-canonical-json-v1','record_set_id':'schuss-record-set-000009','revision':1,'content_hash':'sha256:'+'0'*64,'purpose':'prospective-task','parent_reference':{'status':'included',**{k:p[k] for k in ('record_set_id','revision','content_hash')}},'schema_members':sorted([*copy.deepcopy(p['schema_members']),*[member(x) for x in PATHS]],key=lambda x:(x['schema_version'],x['portable_path'])),'record_members':copy.deepcopy(p['record_members']),'enforced_directories':copy.deepcopy(p['enforced_directories'])}
 s=core.load_json(ROOT/record_set_rules.RECORD_SET_SCHEMA); m['content_hash']=core.record_content_hash(m,s); return core.canonical_json(m).encode()+b'\n'
def main():
 a=argparse.ArgumentParser(); a.add_argument('--check',action='store_true'); n=a.parse_args(); b=generated_bytes(); current=OUTPUT.read_bytes() if OUTPUT.is_file() else None
 if n.check and current!=b: print('Task 015 record set is stale',file=sys.stderr); return 1
 if not n.check: OUTPUT.write_bytes(b)
 print('Task 015 record set '+('passed' if n.check else 'generated')+': bytes_sha256='+hashlib.sha256(b).hexdigest()); return 0
if __name__=='__main__': raise SystemExit(main())
