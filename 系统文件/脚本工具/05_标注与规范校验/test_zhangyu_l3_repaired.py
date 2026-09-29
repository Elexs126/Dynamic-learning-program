#!/usr/bin/env python3
"""Source/decision binding, omission honesty, and independent repair regressions."""
import argparse
import copy
import importlib.util
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.dont_write_bytecode=True
parser=argparse.ArgumentParser(add_help=False)
parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[3])
ARGS,REST=parser.parse_known_args();PROJECT=ARGS.project.resolve()
spec=importlib.util.spec_from_file_location('zy_repaired',Path(__file__).with_name('build_zhangyu_l3_repaired.py'))
B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)

class RepairedPractice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='zy-v3-tests-');cls.root=Path(cls.temp.name)
        cls.snapshot=cls.root/'baseline';cls.result=B.run(PROJECT,cls.snapshot,B.REVIEW,'build')
        cls.rows={r['question_id']:r for cohort in B.COUNTS for r in B.read(cls.snapshot/cohort/'question_annotations_l3_v1.json')['records']}
        cls.tasks=B.read(cls.snapshot/'task_index_v1.json')['tasks']
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def setUp(self):
        self.folder=self.root/self.id().rsplit('.',1)[-1];shutil.copytree(self.snapshot,self.folder)
    def edit(self,q,fn):
        path=self.folder/B.book(q)/'question_annotations_l3_v1.json';x=B.read(path)
        fn(next(r for r in x['records'] if r['question_id']==q));path.write_bytes(B.dump(x))
    def validate(self):return B.validate(PROJECT,self.folder,B.REVIEW)
    def reviews(self):
        p=self.folder/'reviews';shutil.copytree(B.REVIEW,p);return p
    def edit_review(self,p,q,fn):
        path=p/'decisions_v3.json';x=B.read(path);fn(x[q]);path.write_bytes(B.dump(x))
    def text(self,q):return '；'.join(s for e in self.rows[q]['l3'].get('evidence_steps',[]) for s in e['steps'])

    def test_counts_provenance_and_reproducibility(self):
        self.assertEqual(self.result['status'],'PASS');self.assertEqual(len(self.rows),1917)
        report=B.read(self.folder/'coverage_report.json')
        self.assertEqual((report['fresh_semantic_rechecks'],report['inherited_v2_decisions']),(653,1264))
        generated,_=B.create(PROJECT,B.REVIEW)
        for name,raw in generated.items():self.assertEqual((self.folder/name).read_bytes(),raw,name)

    def test_row_column_swap_requires_similarity_as_well_as_congruence(self):
        q='ZY30-XD-06-L6.09';r=self.rows[q];text=self.text(q)
        self.assertIn('置换矩阵',r['l2']['primary_method']['name'])
        for needed in ('正交','逆','合同','相似'):self.assertIn(needed,text)
        self.assertNotIn('消去交叉项',text)

    def test_sphere_quadratic_requires_norm_preservation(self):
        q='ZY1000-JC-XD06-T16';text=self.text(q)
        for needed in ('正交','单位球面','最大特征值','取得条件'):self.assertIn(needed,text)
        self.assertEqual(self.rows[q]['l3']['alternative_methods'],[])
        # A general invertible congruence with diag(2,1) maps this unit vector
        # to norm 2: it cannot preserve the original constraint.
        unit=(1,0);transformed=(2*unit[0],unit[1])
        self.assertNotEqual(sum(v*v for v in unit),sum(v*v for v in transformed))

    def test_composite_question_covers_area_and_volume(self):
        q='ZY1000-JC-GS13-T14';text=self.text(q)
        for needed in ('面积积分','体积积分','端点'):self.assertIn(needed,text)
        self.assertEqual(len([t for t in self.tasks if t['question_id']==q]),2)
        edge=self.rows[q]['l3']['inter_question_dependency']['relations'][0]
        self.assertEqual((edge['from_question_id'],edge['to_question_id']),(q+'#T01',q+'#T02'))

    def test_trajectory_precedes_curve_integral(self):
        q='ZY1000-QH-GS18-T10';ts=[t for t in self.tasks if t['question_id']==q]
        self.assertIn('轨迹',ts[0]['description']);self.assertNotIn('积分',ts[0]['description'])
        self.assertIn('积分',ts[1]['description'])
        e=self.rows[q]['l3']['inter_question_dependency']['relations'][0]
        self.assertEqual((e['from_question_id'],e['to_question_id']),(q+'#T01',q+'#T02'))

    def test_lifetime_has_three_real_tasks_and_open_parameter_check(self):
        q='ZY30-GL-06-L6.08';ts=[t for t in self.tasks if t['question_id']==q]
        self.assertEqual(len(ts),3)
        self.assertIn('分布',ts[0]['description']);self.assertIn('开放参数',ts[1]['description'])
        self.assertIn('估计存在',ts[2]['description'])
        edges=self.rows[q]['l3']['inter_question_dependency']['relations']
        self.assertEqual([(e['from_question_id'],e['to_question_id']) for e in edges],[(q+'#T01',q+'#T02'),(q+'#T02',q+'#T03')])

    def test_confidence_counterexample_and_unverified_fields(self):
        # iid +/-1 has variance 1 and satisfies the literal stated assumptions.
        # The widest listed interval only covers the mean at k=5,...,11.
        numer=sum(math.comb(16,k) for k in range(5,12))
        self.assertEqual(numer,60502);self.assertLess(numer/(2**16),.95)
        r=self.rows['ZY1000-QH-GL09-T24']
        self.assertNotIn('primary_method',r['l2']);self.assertNotIn('evidence_steps',r['l3'])
        self.assertEqual({o['field_path'] for o in r['field_omissions']},{'l2.primary_method','l3.evidence_steps'})

    def test_partial_series_omission_keeps_ode_solution_task(self):
        q='ZY1000-JC-GS16-T07';r=self.rows[q];text=self.text(q)
        self.assertIn('['+q+'#T01]',text);self.assertNotIn('['+q+'#T02]',text)
        self.assertEqual(r['l3']['review_status_by_field']['evidence_steps'],'needs_review')
        self.assertIn('l3.evidence_steps.U02',[o['field_path'] for o in r['field_omissions']])
        # Literal second-task coefficients have leading harmonic term, hence
        # its convergence claim cannot be accepted from a chapter template.
        for n in (10,100):
            a=1/n+2*(math.cos(n)-1)/(n**3)
            self.assertGreaterEqual(a,1/n-4/(n**3))

    def test_missing_plane_options_do_not_hide_confirmed_rank_task(self):
        q='ZY1000-QH-XD05-T15';r=self.rows[q]
        self.assertIn('['+q+'#T01]',self.text(q));self.assertNotIn('['+q+'#T02]',self.text(q))
        self.assertIn('l3.evidence_steps.U02',[o['field_path'] for o in r['field_omissions']])

    def test_duplicate_mechanisms_removed_and_real_alternatives_retained(self):
        self.assertEqual(self.rows['ZY30-GS-14-L14.11']['l3']['alternative_methods'],[])
        self.assertEqual(B.read(self.folder/'coverage_report.json')['alternative_method_question_count'],34)
        self.assertTrue(self.rows['ZY30-XD-01-L1.04']['l3']['alternative_methods'])

    def test_registered_bayes_method_cannot_replace_matrix_method(self):
        q='ZY30-XD-06-L6.09'
        method=next(r['l2']['primary_method'] for r in self.rows.values() if '贝叶斯' in r['l2'].get('primary_method',{}).get('name',''))
        self.edit(q,lambda r:r['l2'].update(primary_method=copy.deepcopy(method)))
        self.assertTrue(any('decision binding mismatch l2' in e for e in self.validate()['errors']))

    def test_registered_but_wrong_main_knowledge_fails(self):
        q='ZY30-XD-06-L6.09';wrong=self.rows['ZY30-GL-01-L1.02']['l2']['main_knowledge']
        self.edit(q,lambda r:r['l2'].update(main_knowledge=copy.deepcopy(wrong)))
        self.assertEqual(self.validate()['status'],'FAIL')

    def test_bayes_evidence_cannot_pass_without_hash_check(self):
        self.edit('ZY30-XD-06-L6.09',lambda r:r['l3']['evidence_steps'][0].update(steps=['求贝叶斯后验概率']))
        self.assertEqual(self.validate()['status'],'FAIL')

    def test_binding_survives_refreshing_output_hashes(self):
        self.edit('ZY30-XD-06-L6.09',lambda r:r['l3']['evidence_steps'][0].update(steps=['求贝叶斯后验概率']))
        p=self.folder/'run_manifest.json';m=B.read(p)
        rel='zy30/question_annotations_l3_v1.json';m['output_sha256'][rel]=B.file_sha(self.folder/rel);p.write_bytes(B.dump(m))
        self.assertEqual(B.run(PROJECT,self.folder,B.REVIEW,'check')['status'],'FAIL')

    def test_evidence_provenance_is_bound_to_decision(self):
        p=self.folder/'zy30/field_evidence_v1.jsonl';xs=[json.loads(s) for s in p.read_text().splitlines()]
        xs[0]['review_round']='invented_human_review';p.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in xs))
        self.assertEqual(self.validate()['status'],'FAIL')

    def test_task_description_tampering_fails(self):
        p=self.folder/'task_index_v1.json';x=B.read(p);x['tasks'][0]['description']='无关任务';p.write_bytes(B.dump(x))
        self.assertEqual(self.validate()['status'],'FAIL')

    def test_backward_dependency_fails(self):
        def reverse(r):
            e=r['l3']['inter_question_dependency']['relations'][0]
            e['from_question_id'],e['to_question_id']=e['to_question_id'],e['from_question_id']
        self.edit('ZY1000-QH-GS18-T10',reverse)
        self.assertTrue(any('cyclic task dependency' in e for e in self.validate()['errors']))

    def test_synthetic_task_input_is_rejected(self):
        p=self.reviews();self.edit_review(p,'ZY30-XD-06-L6.09',lambda d:d.update(tasks=[['建立矩阵所需的中间对象']]))
        with self.assertRaisesRegex(ValueError,'Synthetic task'):B.create(PROJECT,p)

    def test_duplicate_alternative_mechanism_input_is_rejected(self):
        p=self.reviews()
        def duplicate(d):d['alternatives'][0]['mechanism']=d['primary_mechanism']
        self.edit_review(p,'ZY30-XD-01-L1.04',duplicate)
        with self.assertRaisesRegex(ValueError,'Duplicate method mechanism'):B.create(PROJECT,p)

    def test_partial_task_status_cannot_be_verified(self):
        self.edit('ZY1000-JC-GS16-T07',lambda r:r['l3']['review_status_by_field'].update(evidence_steps='verified'))
        self.assertTrue(any('partial field must need review' in e for e in self.validate()['errors']))

    def test_missing_task_cannot_be_reinserted_as_evidence(self):
        q='ZY1000-JC-GS16-T07'
        self.edit(q,lambda r:r['l3']['evidence_steps'][0]['steps'].append('['+q+'#T02] 证明级数收敛'))
        self.assertTrue(any('partial task omission' in e for e in self.validate()['errors']))

    def test_partial_omission_must_refer_to_real_task(self):
        p=self.reviews();self.edit_review(p,'ZY1000-JC-GS16-T07',lambda d:d.update(blocked=['l3.evidence_steps.U99']))
        with self.assertRaisesRegex(ValueError,'Invalid omission path'):B.create(PROJECT,p)

    def test_points_and_answer_fabrication_fail(self):
        self.edit('ZY30-XD-06-L6.09',lambda r:r.update(answer='invented'))
        self.edit('ZY30-GS-01-L1.01',lambda r:r['l3']['score_units'][0].update(points=4))
        result=self.validate();self.assertEqual(result['status'],'FAIL')
        self.assertTrue(any('forbidden answer' in e for e in result['errors']))

    def test_literal_l1_is_preserved(self):
        self.edit('ZY30-XD-06-L6.09',lambda r:r['l1'].update(source_note='invented'))
        self.assertTrue(any('binding mismatch l1' in e for e in self.validate()['errors']))

    def test_all_questions_need_explicit_decisions(self):
        p=self.reviews();path=p/'decisions_v3.json';d=B.read(path);d.pop('ZY30-XD-06-L6.09');path.write_bytes(B.dump(d))
        with self.assertRaisesRegex(ValueError,'all 1917'):B.create(PROJECT,p)

    def test_stale_question_hash_fails(self):
        p=self.reviews();self.edit_review(p,'ZY30-XD-06-L6.09',lambda d:d.update(question_hash_sha256='0'*64))
        with self.assertRaisesRegex(ValueError,'review is stale'):B.create(PROJECT,p)

    def test_source_lock_and_auxiliary_cannot_be_silently_refreshed(self):
        p=self.reviews();path=p/'source_lock_v1.json';x=B.read(path);x['source_files'][next(iter(x['source_files']))]='0'*64;path.write_bytes(B.dump(x))
        with self.assertRaisesRegex(ValueError,'Locked source'):B.inventory(PROJECT,p)
        path=p/'auxiliary_sources_v2.json';x=B.read(path);x[next(iter(x))]='0'*64;path.write_bytes(B.dump(x))
        with self.assertRaisesRegex(ValueError,'Auxiliary source'):B.inventory(PROJECT,p)

    def test_missing_manifest_hash_is_not_a_bypass(self):
        p=self.folder/'run_manifest.json';x=B.read(p);x['output_sha256'].pop('coverage_report.json');p.write_bytes(B.dump(x))
        self.assertEqual(B.run(PROJECT,self.folder,B.REVIEW,'check')['status'],'FAIL')

    def test_existing_snapshot_never_overwritten(self):
        with self.assertRaisesRegex(ValueError,'Refusing to overwrite'):B.run(PROJECT,self.folder,B.REVIEW,'build')

    def test_recovered_figure_remains_source_bound(self):
        es=[json.loads(s) for s in (self.folder/'zy30/field_evidence_v1.jsonl').read_text().splitlines()]
        e=next(e for e in es if e['question_id']=='ZY30-GS-08-L8.11')
        self.assertTrue(e['images_reviewed']);self.assertEqual(len(e['additional_source_evidence']['images']),5)

if __name__=='__main__':unittest.main(argv=[sys.argv[0],*REST])
