#!/usr/bin/env python3
"""Offline acceptance and corruption checks for all 2013–2026 CS408 annotations."""
import argparse,copy,json,shutil,tempfile,unittest
from pathlib import Path
import build_cs408_2013_2026_l23 as b
PROJECT=Path('/home/elexs/Dynamic-learning-program')
class ReleaseTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.payload=b.generate(PROJECT);cls.bundle=json.loads(cls.payload[b.BUNDLE]);cls.scores=json.loads(cls.payload['scoring_evidence_v1.json'])
 def rec(self,obj,q):return next(x for x in obj['records'] if x['question_id']==q)
 def validate(self,bundle=None,scores=None,payload=None,review=None):
  p=dict(payload or self.payload)
  if bundle is not None:p[b.BUNDLE]=b.json_bytes(bundle)
  if scores is not None:p['scoring_evidence_v1.json']=b.json_bytes(scores)
  return b.validate_data(PROJECT,None,p,review or b.REVIEW_DIR)
 def test_01_all_fourteen_years_and_original_layers(self):
  result=self.validate();self.assertEqual(result['status'],'PASS',result['errors'])
  self.assertEqual(len(self.bundle['records']),658)
  baseline={r['question_id']:r for r in b.read_json(PROJECT/b.L1_PATH)['records']}
  for y in range(2013,2027):
   rr=[r for r in self.bundle['records'] if r['l0']['year']==y];self.assertEqual(len(rr),47)
   self.assertEqual(sum(r['l0']['question_type']=='choice' for r in rr),40)
  for r in self.bundle['records']:
   self.assertEqual(r['l0'],baseline[r['question_id']]['l0']);self.assertEqual(r['l1'],baseline[r['question_id']]['l1'])
 def test_02_full_partitions_include_fractional_points(self):
  for q,pts in [('408-13-A-T47',[.5]*12+[1]*3),('408-24-A-T43',[2,3,2,2,2,2]),('408-25-A-T41',[4,7,2])]:
   self.assertEqual([u['points'] for u in self.rec(self.bundle,q)['l3']['score_units']],pts)
 def test_03_missing_subpoints_do_not_become_invented_partitions(self):
  x=copy.deepcopy(self.bundle);r=self.rec(x,'408-18-A-T41');unit=r['l3']['score_units'][0];unit['points']=5
  other=copy.deepcopy(unit);other['unit_id']=r['question_id']+':S1';r['l3']['score_units'].append(other)
  self.assertEqual(self.validate(bundle=x)['status'],'FAIL')
 def test_04_known_partition_cannot_be_redistributed(self):
  x=copy.deepcopy(self.bundle);u=self.rec(x,'408-24-A-T41')['l3']['score_units'];u[0]['points']=5;u[1]['points']=8
  self.assertEqual(self.validate(bundle=x)['status'],'FAIL')
 def test_05_conflict_keeps_other_labels(self):
  q='408-17-A-T41';r=self.rec(self.bundle,q);s=self.rec(self.scores,q)
  self.assertEqual(r['l0']['original_points'],15)
  self.assertEqual(sum(u['points'] for u in r['l3']['score_units']),15)
  self.assertEqual(sum(v['points'] for v in s['documented_subpoints']),15)
  self.assertTrue(r['l2']['primary_method']);self.assertTrue(r['l3']['evidence_steps'][0]['steps'])
  x=copy.deepcopy(self.bundle);self.rec(x,q)['l3']['score_units'][0]['points']=99
  self.assertEqual(self.validate(bundle=x)['status'],'FAIL')
 def test_06_stated_full_mark_conflict_even_when_subpoints_match_metadata(self):
  for q in ['408-26-A-T41','408-26-A-T44']:
   s=self.rec(self.scores,q);self.assertEqual(s['mode'],'whole')
   self.assertEqual(s['effective_total_points'],13)
 def test_07_conditional_credit_above_bad_metadata_is_preserved_not_added(self):
  s=self.rec(self.scores,'408-17-A-T41');rules=s['conditional_rules']
  self.assertIn(15,[v['points'] for v in rules]);self.assertTrue(all(v['additive'] is False for v in rules))
  self.assertEqual(s['effective_total_points'],15)
 def test_08_unknown_condition_scope_has_no_guessed_targets(self):
  rules=self.rec(self.scores,'408-13-A-T41')['conditional_rules']
  self.assertTrue(rules);self.assertTrue(all(v['scope_status']=='verified' and len(v['target_task_ids'])>0 for v in rules))
 def test_09_partial_points_equal_total_still_do_not_create_zero_for_ungraded_task(self):
  s=self.rec(self.scores,'408-24-A-T44');self.assertEqual(s['mode'],'whole')
  self.assertEqual([v['points'] for v in s['documented_subpoints']],[3,5])
  self.assertEqual(len(self.rec(self.bundle,s['question_id'])['l3']['score_units']),1)
  self.assertTrue(all(v['promoted_unit_id'] is None for v in s['documented_subpoints']))
 def test_10_sidecar_scores_never_double_count(self):
  for q,key,field in [('408-17-A-T41','conditional_rules','additive'),('408-24-A-T44','documented_subpoints','count_separately')]:
   x=copy.deepcopy(self.scores);self.rec(x,q)[key][0][field]=True
   self.assertEqual(self.validate(scores=x)['status'],'FAIL')
 def test_11_all_local_grading_cues_must_be_reviewed(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)/'review';shutil.copytree(b.REVIEW_DIR,r);p=b.read_json(r/'scoring_plan_v1.json');p['questions'].pop('408-26-A-T44');(r/'scoring_plan_v1.json').write_bytes(b.json_bytes(p))
   with self.assertRaisesRegex(ValueError,'rubric cues'):b.generate(PROJECT,r)
 def test_12_score_anchor_line_and_fragment_are_bound(self):
  for change in ['line','match']:
   with tempfile.TemporaryDirectory() as t:
    r=Path(t)/'review';shutil.copytree(b.REVIEW_DIR,r);p=b.read_json(r/'scoring_plan_v1.json');a=p['questions']['408-26-A-T41']['explicit_total_claims'][0]['anchor'];a[change]=1 if change=='line' else 'nonexistent fragment';(r/'scoring_plan_v1.json').write_bytes(b.json_bytes(p))
    with self.assertRaisesRegex(ValueError,'anchor'):b.generate(PROJECT,r)
 def test_13_source_and_image_drift_are_rejected(self):
  for field in ['source_files','images']:
   with tempfile.TemporaryDirectory() as t:
    r=Path(t)/'review';shutil.copytree(b.REVIEW_DIR,r);p=b.read_json(r/'source_lock_v1.json');p[field][next(iter(p[field]))]='0'*64;(r/'source_lock_v1.json').write_bytes(b.json_bytes(p))
    with self.assertRaises(ValueError):b.generate(PROJECT,r)
 def test_14_foreign_or_duplicate_question_ids_are_rejected(self):
  for q in ['408-12-C-T01',self.bundle['records'][1]['question_id']]:
   x=copy.deepcopy(self.bundle);x['records'][0]['question_id']=q;self.assertEqual(self.validate(bundle=x)['status'],'FAIL')
 def test_15_original_layers_cannot_change(self):
  for layer,key in [('l0','original_points'),('l1','official_scope_coarse')]:
   x=copy.deepcopy(self.bundle);x['records'][0][layer][key]=999 if layer=='l0' else 'changed';self.assertEqual(self.validate(bundle=x)['status'],'FAIL')
 def test_16_feasible_fields_cannot_be_omitted_silently(self):
  x=copy.deepcopy(self.bundle);x['records'][0]['l2'].pop('primary_method');self.assertEqual(self.validate(bundle=x)['status'],'FAIL')
  x=copy.deepcopy(self.bundle);self.rec(x,'408-26-A-T41')['field_omissions']=[{'field_path':'l2.primary_method','reason':'invented omission'}];self.assertEqual(self.validate(bundle=x)['status'],'FAIL')
 def test_17_registered_but_wrong_semantic_label_is_rejected(self):
  x=copy.deepcopy(self.bundle);x['records'][0]['l2']['primary_method']=x['records'][1]['l2']['primary_method'];self.assertEqual(self.validate(bundle=x)['status'],'FAIL')
 def test_18_cross_question_dependency_and_shared_context_remain_distinct(self):
  r=self.rec(self.bundle,'408-14-A-T43');self.assertTrue(any(d['from_question_id']=='408-14-A-T42#T03' for d in r['l3']['inter_question_dependency']['relations']))
  evidence=[json.loads(v) for v in self.payload['field_evidence_v1.jsonl'].decode().splitlines()]
  for q in ['408-16-C-T33','408-24-A-T44']:
   e=next(e for e in evidence if e['question_id']==q);self.assertTrue(e['context_sources'])
   self.assertFalse(any(d['from_question_id'].split('#')[0]!=q for d in self.rec(self.bundle,q)['l3']['inter_question_dependency']['relations']))
 def test_19_cycle_across_two_questions_is_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)/'review';shutil.copytree(b.REVIEW_DIR,r);f=r/'2014.psv';lines=f.read_text().splitlines()
   for i,line in enumerate(lines):
    if line.startswith('14A42|'):
     c=line.split('|');c[10]='@14A43#T01>3';lines[i]='|'.join(c)
   f.write_text('\n'.join(lines)+'\n');payload=b.generate(PROJECT,r);result=self.validate(payload=payload,review=r)
   self.assertEqual(result['status'],'FAIL');self.assertTrue(any('Cyclic' in e for e in result['errors']))
 def test_20_context_source_cannot_be_swapped(self):
  p=dict(self.payload);ee=[json.loads(v) for v in p['field_evidence_v1.jsonl'].decode().splitlines()];e=next(v for v in ee if v['context_sources']);e['context_sources']=[];p['field_evidence_v1.jsonl']=''.join(json.dumps(v,ensure_ascii=False,sort_keys=True)+'\n' for v in ee).encode();self.assertEqual(self.validate(payload=p)['status'],'FAIL')
 def test_21_isomorphic_reciprocity_and_registry(self):
  x=copy.deepcopy(self.bundle);r=next(v for v in x['records'] if v['l3']['isomorphic_relation']);r['l3']['isomorphic_relation']['related_question_ids'].append('408-12-C-T01');self.assertEqual(self.validate(bundle=x)['status'],'FAIL')
  x=copy.deepcopy(self.bundle);x['records'][0]['l2']['main_knowledge']['id']='unknown';self.assertEqual(self.validate(bundle=x)['status'],'FAIL')
 def test_22_answer_student_and_role_payload_is_rejected(self):
  for key in ['answer','reference_solution','student_score','usage_role']:
   x=copy.deepcopy(self.scores);x[key]='forbidden';self.assertEqual(self.validate(scores=x)['status'],'FAIL')
 def test_23_build_reuse_and_tamper_detection(self):
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'snapshot';self.assertEqual(b.run(PROJECT,out)['mode'],'built');self.assertEqual(b.run(PROJECT,out)['mode'],'reused')
   (out/'scoring_evidence_v1.json').write_text('{}\n')
   with self.assertRaisesRegex(ValueError,'Snapshot content changed'):b.run(PROJECT,out,'check')
 def test_24_changed_inputs_cannot_reuse_snapshot(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)/'review';shutil.copytree(b.REVIEW_DIR,r);out=Path(t)/'snapshot';b.run(PROJECT,out,review_dir=r)
   f=r/'2013.psv';f.write_text(f.read_text()+'# changed review\n')
   with self.assertRaisesRegex(ValueError,'Snapshot inputs changed'):b.run(PROJECT,out,review_dir=r)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--project',type=Path,default=PROJECT);args,rest=parser.parse_known_args();PROJECT=args.project.resolve();unittest.main(argv=[__file__]+rest)
