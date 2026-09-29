#!/usr/bin/env python3
"""Regression checks for candidate honesty, source locks and scoring semantics."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.dont_write_bytecode=True
parser=argparse.ArgumentParser(add_help=False)
parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[3])
ARGS,REST=parser.parse_known_args()
PROJECT=ARGS.project.resolve()
spec=importlib.util.spec_from_file_location('zy_builder',Path(__file__).with_name('build_zhangyu_l3.py'))
B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)

class PracticeAnnotations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='zy-l3-tests-')
        cls.root=Path(cls.temp.name)
        cls.snapshot=cls.root/'baseline'
        cls.result=B.run(PROJECT,cls.snapshot,B.REVIEW,'build')

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def setUp(self):
        self.folder=self.root/self.id().rsplit('.',1)[-1]
        shutil.copytree(self.snapshot,self.folder)

    def change_record(self,q,callback):
        path=self.folder/B.book(q)/'question_annotations_l3_v1.json'
        bundle=B.read(path)
        row=next(r for r in bundle['records'] if r['question_id']==q)
        callback(row);path.write_bytes(B.dump(bundle))

    def validate(self):return B.validate(PROJECT,self.folder,B.REVIEW)

    def test_full_coverage_and_reproducibility(self):
        self.assertEqual(self.result['status'],'PASS')
        self.assertEqual(self.result['record_count'],1917)
        generated,_=B.create(PROJECT,B.REVIEW)
        for name,raw in generated.items():self.assertEqual((self.folder/name).read_bytes(),raw,name)

    def test_candidate_cannot_be_claimed_verified(self):
        rows=B.read(self.folder/'zy30/question_annotations_l3_v1.json')['records']
        q=next(r['question_id'] for r in rows if r['l2']['review_status_by_field']['main_knowledge']=='candidate')
        self.change_record(q,lambda r:r['l2']['review_status_by_field'].update(main_knowledge='verified'))
        self.assertTrue(any('unreviewed semantic verification' in s for s in self.validate()['errors']))

    def test_textbook_points_cannot_be_invented(self):
        self.change_record('ZY30-GS-01-L1.01',lambda r:r['l3']['score_units'][0].update(points=4))
        self.assertEqual(self.validate()['status'],'FAIL')

    def test_undeclared_field_omission_fails(self):
        self.change_record('ZY30-GS-01-L1.01',lambda r:r['l2'].pop('main_knowledge'))
        self.assertTrue(any('omission/content conflict' in s for s in self.validate()['errors']))

    def test_l0_type_changes_must_match_source(self):
        self.change_record('ZY30-GS-01-L1.01',lambda r:r['l0'].update(question_type='analytical'))
        self.assertTrue(any('cumulative layer changed' in s for s in self.validate()['errors']))

    def test_isomorphism_must_be_reciprocal(self):
        self.change_record('ZY30-XD-01-L1.01',lambda r:r['l3']['isomorphic_relation'].update(related_question_ids=['ZY30-GS-01-L1.01']))
        self.assertTrue(any('asymmetric isomorphism' in s for s in self.validate()['errors']))

    def test_dependency_cannot_point_backward(self):
        def reverse(r):
            edge=r['l3']['inter_question_dependency']['relations'][0]
            edge['from_question_id'],edge['to_question_id']=edge['to_question_id'],edge['from_question_id']
        self.change_record('ZY30-GS-15-L15.07',reverse)
        self.assertTrue(any('cyclic task dependency' in s for s in self.validate()['errors']))

    def test_answers_are_not_allowed_in_labels(self):
        self.change_record('ZY30-GS-01-L1.01',lambda r:r.update(answer='not permitted'))
        self.assertTrue(any('forbidden answer' in s for s in self.validate()['errors']))

    def test_stale_review_hash_is_rejected(self):
        reviews=self.folder/'reviews';shutil.copytree(B.REVIEW,reviews)
        path=reviews/'semantic_reviews_v1.json';x=B.read(path)
        x['ZY30-GS-01-L1.01']['question_hash_sha256']='0'*64;path.write_bytes(B.dump(x))
        with self.assertRaisesRegex(ValueError,'Semantic review is stale'):B.create(PROJECT,reviews)

    def test_source_lock_cannot_be_silently_refreshed(self):
        reviews=self.folder/'reviews';shutil.copytree(B.REVIEW,reviews)
        path=reviews/'source_lock_v1.json';x=B.read(path)
        key=next(iter(x['source_files']));x['source_files'][key]='0'*64;path.write_bytes(B.dump(x))
        with self.assertRaisesRegex(ValueError,'Locked source'):B.inventory(PROJECT,reviews)

    def test_output_tampering_fails_check(self):
        (self.folder/'coverage_report.json').write_text('{}\n')
        self.assertEqual(B.run(PROJECT,self.folder,B.REVIEW,'check')['status'],'FAIL')

    def test_existing_snapshot_is_never_overwritten(self):
        with self.assertRaisesRegex(ValueError,'Refusing to overwrite'):B.run(PROJECT,self.folder,B.REVIEW,'build')

    def test_option_text_is_not_affirmative_evidence(self):
        p=B.read(B.REVIEW/'profiles_v1.json')
        for body in ['下列说法正确的是。\n- **A.** 最大值\n- **B.** 最小值',
                     '下列说法正确的是。\nA. 最大值 B. 最小值']:
            key,match=B.select_profile('ZY30-GS-01-X99',body,'calculus',p)
            self.assertIsNone(key);self.assertIsNone(match)

    def test_source_issues_and_resolved_sign(self):
        rows={r['question_id']:r for r in B.read(self.folder/'zy30/question_annotations_l3_v1.json')['records']}
        self.assertEqual(rows['ZY30-GS-01-L1.30']['l3']['review_status_by_field']['score_attribution'],'verified')
        bad=rows['ZY30-GS-15-X09']
        self.assertNotIn('常系数',bad['l2']['main_knowledge']['name'])
        self.assertNotIn('primary_method',bad['l2'])
        self.assertNotIn('evidence_steps',bad['l3'])
        self.assertNotIn('score_attribution',rows['ZY30-GL-01-X17']['l3'])

if __name__=='__main__':unittest.main(argv=[sys.argv[0],*REST])
