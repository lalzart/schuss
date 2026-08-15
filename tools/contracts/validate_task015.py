#!/usr/bin/env python3
"""Read-only Task 015 normalized-DSP/direct-frontend validator."""
from __future__ import annotations
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'tools/contracts')]
from packages.schuss_core.control_plane import load_repository_context,dispatch_operation
from packages.schuss_core.direct_frontend import lower_minimal_direct
import generate_task015_record_set as generator,record_set_rules,validator_core as core
RECORD=ROOT/'contracts/record-sets/task015-minimal-direct-frontend-v1.json';EVIDENCE=ROOT/'evidence/task015-completion-v1/validation-summary.json'
def validate():
 if RECORD.read_bytes()!=generator.generated_bytes(): raise ValueError('Task 015 record set is stale')
 loaded=record_set_rules.load_record_set(ROOT,RECORD);c=load_repository_context(record_set_path=RECORD)
 r=next(x for x in c.records['request'] if x['build_request_id']=='schuss-build-request-000001' and x['revision']==2);ref={k:r[k] for k in ('build_request_id','revision','content_hash')}
 p=dispatch_operation({'schema_version':'schuss-operation-request-v4','canonical_profile':'schuss-canonical-json-v1','operation':'build.plan','payload':{'build_request_reference':ref}},c)['value'];g=next(x for x in c.records['graphs'] if x['graph_id']=='schuss-graph-000001');co=next(x for x in c.records['contracts'] if x['component_contract_id']=='schuss-component-contract-000003');o=lower_minimal_direct(p,g,co)
 if core.schema_errors(o['module'],c.schemas['normalized_dsp_module'],c.schemas['normalized_dsp_module']) or core.schema_errors(o,c.schemas['direct_frontend_result'],c.schemas['direct_frontend_result']): raise ValueError('Task 015 result schema validation failed')
 syntax=subprocess.run(['clang++','-x','c++','-std=c++17','-fsyntax-only','-'],input=o['generated_cpp']['text'].encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if syntax.returncode: raise ValueError('generated C++ syntax check failed')
 e=core.load_json(EVIDENCE);b=core.canonical_json(o).encode();m=core.canonical_json(o['module']).encode();sm=core.canonical_json(o['source_map']).encode()
 facts=(e['record_set_reference']==loaded.reference and e['input_plan_sha256']==o['input_plan_sha256'] and e['generated_cpp']['byte_sha256']==o['generated_cpp']['byte_sha256'] and e['normalized_module']['byte_sha256']==hashlib.sha256(m).hexdigest() and e['source_map']['byte_sha256']==hashlib.sha256(sm).hexdigest() and e['canonical_result']['byte_sha256']==hashlib.sha256(b).hexdigest() and [x['status'] for x in e['evidence_levels']]==['passed']*4+['not-run']*4 and not e['legacy_bridge_used'] and not e['arm_toolchain_used'] and not e['device_actions_performed'])
 if not facts: raise ValueError('retained Task 015 evidence differs')
 return {'schema_version':'task015-validator-result-v1','status':'valid','record_set_reference':loaded.reference,'manifest_byte_sha256':hashlib.sha256(RECORD.read_bytes()).hexdigest(),'generated_cpp_sha256':o['generated_cpp']['byte_sha256'],'focused_test_count':8,'evidence_levels':e['evidence_levels']}
def main():
 try:r=validate()
 except (OSError,ValueError) as x:print('Task 015 validation failed: '+str(x),file=sys.stderr);return 1
 print(json.dumps(r,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
