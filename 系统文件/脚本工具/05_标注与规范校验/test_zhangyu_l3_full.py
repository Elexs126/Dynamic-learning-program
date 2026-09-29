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
spec=importlib.util.spec_from_file_location('zy_builder',Path(__file__).with_name('build_zhangyu_l3_full.py'))
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

    def test_full_release_cannot_contain_candidates(self):
        self.change_record('ZY30-GS-01-L1.01',lambda r:r['l2']['review_status_by_field'].update(main_knowledge='candidate'))
        self.assertTrue(any('must not contain candidate' in s for s in self.validate()['errors']))

    def test_all_questions_require_explicit_semantic_review(self):
        reviews=self.folder/'reviews';shutil.copytree(B.REVIEW,reviews)
        path=reviews/'semantic_reviews_v1.json';x=B.read(path);x.pop('ZY30-GS-01-L1.01');path.write_bytes(B.dump(x))
        with self.assertRaisesRegex(ValueError,'all 1917'):B.create(PROJECT,reviews)

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

    def test_recovered_figure_is_source_bound(self):
        rows={r['question_id']:r for r in B.read(self.folder/'zy30/question_annotations_l3_v1.json')['records']}
        self.assertIn('evidence_steps',rows['ZY30-GS-08-L8.11']['l3'])
        evidence=[json.loads(line) for line in (self.folder/'zy30/field_evidence_v1.jsonl').read_text().splitlines()]
        ev=next(e for e in evidence if e['question_id']=='ZY30-GS-08-L8.11')
        self.assertTrue(ev['images_reviewed'])
        self.assertEqual(len(ev['additional_source_evidence']['images']),5)

    def test_source_issues_are_not_hidden(self):
        rows={r['question_id']:r for r in B.read(self.folder/'zy1000/question_annotations_l3_v1.json')['records']}
        self.assertNotIn('evidence_steps',rows['ZY1000-QH-GS18-T12']['l3'])
        self.assertNotIn('primary_method',rows['ZY1000-QH-GL08-T10']['l2'])
        self.assertIn('evidence_steps',rows['ZY1000-QH-GS02-T02']['l3'])
        allrows=[]
        for book in B.COUNTS:allrows+=B.read(self.folder/book/'question_annotations_l3_v1.json')['records']
        self.assertEqual(len(allrows),1917)
        self.assertTrue(all(r['l2']['review_status_by_field']['main_knowledge']=='verified' for r in allrows))
        self.assertEqual(sum(bool(r['field_omissions']) for r in allrows),7)

    def test_auxiliary_source_lock_is_enforced(self):
        reviews=self.folder/'reviews';shutil.copytree(B.REVIEW,reviews)
        path=reviews/'auxiliary_sources_v2.json';x=B.read(path);x[next(iter(x))]='0'*64;path.write_bytes(B.dump(x))
        with self.assertRaisesRegex(ValueError,'Auxiliary source changed'):B.create(PROJECT,reviews)

if __name__=='__main__':unittest.main(argv=[sys.argv[0],*REST])
