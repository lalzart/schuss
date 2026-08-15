from __future__ import annotations
import copy, json, os, random, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; sys.path[:0]=[str(ROOT),str(ROOT/'tools/contracts')]
from packages.schuss_core.control_plane import load_repository_context,dispatch_operation
from packages.schuss_core.direct_frontend import evaluate_linear_mix_q27,lower_minimal_direct,Q27_SCALE
import validator_core as core
RECORD=ROOT/'contracts/record-sets/task015-minimal-direct-frontend-v1.json'
class Task015DirectFrontendTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.context=load_repository_context(record_set_path=RECORD)
  r=next(x for x in cls.context.records['request'] if x['build_request_id']=='schuss-build-request-000001' and x['revision']==2)
  ref={k:r[k] for k in ('build_request_id','revision','content_hash')}
  cls.plan=dispatch_operation({'schema_version':'schuss-operation-request-v4','canonical_profile':'schuss-canonical-json-v1','operation':'build.plan','payload':{'build_request_reference':ref}},cls.context)['value']
  cls.graph=next(x for x in cls.context.records['graphs'] if x['graph_id']=='schuss-graph-000001')
  cls.contract=next(x for x in cls.context.records['contracts'] if x['component_contract_id']=='schuss-component-contract-000003')
  cls.result=lower_minimal_direct(cls.plan,cls.graph,cls.contract)
 def test_schemas_and_exact_result(self):
  self.assertEqual([],core.schema_errors(self.result['module'],self.context.schemas['normalized_dsp_module'],self.context.schemas['normalized_dsp_module']))
  self.assertEqual([],core.schema_errors(self.result,self.context.schemas['direct_frontend_result'],self.context.schemas['direct_frontend_result']))
  self.assertFalse(self.result['legacy_bridge_used']); self.assertEqual(['passed']*4+['not-run']*4,[x['status'] for x in self.result['evidence_levels']])
 def test_cpp_is_deterministic_portable_and_legacy_free(self):
  second=lower_minimal_direct(copy.deepcopy(self.plan),copy.deepcopy(self.graph),copy.deepcopy(self.contract))
  self.assertEqual(core.canonical_json(self.result),core.canonical_json(second))
  text=self.result['generated_cpp']['text']; self.assertNotIn('/Users/',text); self.assertNotIn('.axp',text); self.assertNotIn('java',text.lower()); self.assertNotIn('ksoloti',text.lower())
 def test_cpp_syntax(self):
  p=subprocess.run(['clang++','-x','c++','-std=c++17','-fsyntax-only','-'],input=self.result['generated_cpp']['text'].encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  self.assertEqual(0,p.returncode,p.stderr.decode())
 def test_reference_vectors(self):
  self.assertEqual(10,evaluate_linear_mix_q27(10,20,0)); self.assertEqual(20,evaluate_linear_mix_q27(10,20,Q27_SCALE)); self.assertEqual(15,evaluate_linear_mix_q27(10,20,Q27_SCALE//2))
  self.assertEqual(-(1<<31),evaluate_linear_mix_q27(-(1<<31),-(1<<31),Q27_SCALE//2)); self.assertEqual((1<<31)-1,evaluate_linear_mix_q27((1<<31)-1,(1<<31)-1,Q27_SCALE//2))
 def test_compiled_vectors_match_reference(self):
  rng=random.Random(15001); vectors=[(-(1<<31),(1<<31)-1,c) for c in (-1,0,1,Q27_SCALE//2,Q27_SCALE,Q27_SCALE+1)]+[(rng.randint(-(1<<31),(1<<31)-1),rng.randint(-(1<<31),(1<<31)-1),rng.randint(-100,Q27_SCALE+100)) for _ in range(32)]
  rows=',\n'.join('{'+f'{a},{b},{c}'+'}' for a,b,c in vectors)
  harness=self.result['generated_cpp']['text']+'\n#include <cstdio>\nint main(){std::int32_t v[][3]={'+rows+'}; for(auto &r:v){std::int32_t o=0;schuss_blend_process_q27(&r[0],&r[1],r[2],&o,1);std::printf("%d\\n",o);}return 0;}\n'
  with tempfile.TemporaryDirectory() as t:
   src=Path(t)/'x.cpp'; exe=Path(t)/'x'; src.write_text(harness,encoding='utf-8'); c=subprocess.run(['clang++','-std=c++17',str(src),'-o',str(exe)],stdout=subprocess.PIPE,stderr=subprocess.PIPE); self.assertEqual(0,c.returncode,c.stderr.decode()); out=subprocess.check_output([str(exe)],text=True)
  self.assertEqual([evaluate_linear_mix_q27(*v) for v in vectors],[int(x) for x in out.splitlines()])
 def test_failed_plan_rejected(self):
  p=copy.deepcopy(self.plan);p['status']='unresolved'
  with self.assertRaisesRegex(ValueError,'DIRECT_PLAN_NOT_SUCCESSFUL'): lower_minimal_direct(p,self.graph,self.contract)
 def test_stale_graph_and_contract_rejected(self):
  g=copy.deepcopy(self.graph);g['content_hash']='sha256:'+'0'*64
  with self.assertRaisesRegex(ValueError,'DIRECT_GRAPH_UNSUPPORTED'): lower_minimal_direct(self.plan,g,self.contract)
  c=copy.deepcopy(self.contract);c['revision']=2
  with self.assertRaisesRegex(ValueError,'DIRECT_CONTRACT_UNSUPPORTED'): lower_minimal_direct(self.plan,self.graph,c)
 def test_multi_node_and_bad_mapping_rejected(self):
  g=copy.deepcopy(self.graph);g['nodes'].append(copy.deepcopy(g['nodes'][0]))
  with self.assertRaisesRegex(ValueError,'DIRECT_GRAPH_SHAPE_UNSUPPORTED'): lower_minimal_direct(self.plan,g,self.contract)
  g=copy.deepcopy(self.graph);g['parameter_bindings']=[]
  with self.assertRaisesRegex(ValueError,'DIRECT_PUBLIC_MAPPING_UNSUPPORTED'): lower_minimal_direct(self.plan,g,self.contract)
if __name__=='__main__': unittest.main()
