#!/usr/bin/env python3
"""Integrity and failure-path checks for the offline Math I annotation release."""
import argparse
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import build_math1_l23 as builder

PROJECT = Path('/home/elexs/Dynamic-learning-program')
SCHEMA_DIR = PROJECT / builder.SCHEMA_DIR


class Math1AnnotationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload=builder.generate(PROJECT)
        cls.bundle=json.loads(cls.payload[builder.BUNDLE])

    def with_bundle(self,bundle):
        payload=dict(self.payload)
        payload[builder.BUNDLE]=builder.json_bytes(bundle)
        return payload

    def check_bundle(self,bundle):
        return builder.validate_data(PROJECT,SCHEMA_DIR,self.with_bundle(bundle))

    def test_complete_scope_and_existing_schema_compatibility(self):
        result=builder.validate_data(PROJECT,SCHEMA_DIR,self.payload)
        self.assertEqual(result['status'],'PASS',result['errors'])
        counts={}
        for r in self.bundle['records']:
            counts[r['l0']['year']]=counts.get(r['l0']['year'],0)+1
        self.assertEqual(counts,{y:(23 if y<2021 else 22) for y in range(2008,2027)})
        runtime=builder.load_module('test_old_schema_runtime',PROJECT/builder.TOOL_DIR/'json_schema_runtime.py')
        l1=builder.read_json(PROJECT/builder.L1_PATH)
        self.assertEqual(runtime.SchemaRuntime(PROJECT/builder.SCHEMA_DIR/'question_annotations_bundle.schema.json').validate(l1),[])
        self.assertTrue(runtime.SchemaRuntime(PROJECT/builder.SCHEMA_DIR/'question_annotations_bundle.schema.json').validate(self.bundle))

    def test_no_fabricated_subpoint_allocation(self):
        value=copy.deepcopy(self.bundle)
        r=next(x for x in value['records'] if x['l0']['question_type']=='analytical')
        unit=r['l3']['score_units'][0];unit['points']/=2
        second=copy.deepcopy(unit);second['unit_id']=r['question_id']+':S1'
        r['l3']['score_units'].append(second)
        self.assertEqual(self.check_bundle(value)['status'],'FAIL')

    def test_answer_and_role_payload_rejected(self):
        for key in ('answer','solution','data_role','student_score'):
            with self.subTest(key=key):
                value=copy.deepcopy(self.bundle);value['records'][0]['l3'][key]='forbidden'
                self.assertEqual(self.check_bundle(value)['status'],'FAIL')

    def test_locked_layers_cannot_change(self):
        for layer,field,new in [('l0','original_points',999),('l1','official_scope_coarse','altered')]:
            with self.subTest(layer=layer):
                value=copy.deepcopy(self.bundle);value['records'][0][layer][field]=new
                self.assertEqual(self.check_bundle(value)['status'],'FAIL')

    def test_missing_field_needs_explicit_reason(self):
        value=copy.deepcopy(self.bundle);value['records'][0]['l2'].pop('main_knowledge')
        # main knowledge is mandatory for this release, even though v1.1 permits declared omissions.
        self.assertEqual(self.check_bundle(value)['status'],'FAIL')
        value=copy.deepcopy(self.bundle);value['records'][0]['l2'].pop('primary_method')
        result=self.check_bundle(value)
        self.assertTrue(any('undeclared omission' in x for x in result['errors']))

    def test_omission_not_replaced_by_a_guess(self):
        r=next(x for x in self.bundle['records'] if x['question_id']=='M1-16-F-T12')
        self.assertIn('primary_method',r['l2'])
        self.assertEqual(r['l2']['review_status_by_field']['primary_method'],'verified')

    def test_partial_evidence_retains_unaffected_task(self):
        r=next(x for x in self.bundle['records'] if x['question_id']=='M1-21-A-T22')
        steps=r['l3']['evidence_steps'][0]['steps']
        self.assertTrue(steps)
        self.assertEqual(r['l3']['review_status_by_field']['evidence_steps'],'verified')

    def test_foreign_record_cannot_replace_math1(self):
        value=copy.deepcopy(self.bundle)
        value['records'][0]['question_id']='M2-08-C-T01'
        self.assertEqual(self.check_bundle(value)['status'],'FAIL')

    def test_dangling_or_reverse_dependency_rejected(self):
        for target in ('missing',None):
            value=copy.deepcopy(self.bundle)
            r=next(x for x in value['records'] if x['l3']['inter_question_dependency']['relations'])
            edge=r['l3']['inter_question_dependency']['relations'][0]
            edge['to_question_id']=target or edge['from_question_id']
            self.assertEqual(self.check_bundle(value)['status'],'FAIL')

    def test_isomorphism_requires_reciprocity(self):
        value=copy.deepcopy(self.bundle)
        r=next(x for x in value['records'] if x['l3'].get('isomorphic_relation'))
        r['l3']['isomorphic_relation']['related_question_ids'].append('M1-00-C-T01')
        self.assertEqual(self.check_bundle(value)['status'],'FAIL')

    def test_knowledge_registry_checked(self):
        value=copy.deepcopy(self.bundle)
        value['records'][0]['l2']['main_knowledge']['id']='unknown'
        self.assertEqual(self.check_bundle(value)['status'],'FAIL')

    def test_source_drift_requires_new_review(self):
        with tempfile.TemporaryDirectory() as temp:
            review=Path(temp)/'review';shutil.copytree(builder.REVIEW_DIR,review)
            lock=builder.read_json(review/'source_lock_v1.json')
            first=next(iter(lock['source_files']));lock['source_files'][first]='0'*64
            (review/'source_lock_v1.json').write_bytes(builder.json_bytes(lock))
            with self.assertRaisesRegex(ValueError,'Source changed since review'):
                builder.generate(PROJECT,review)

    def test_build_reuse_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'snapshot'
            built=builder.run(PROJECT,output,schema_dir=SCHEMA_DIR)
            self.assertEqual(built['mode'],'built')
            reused=builder.run(PROJECT,output,schema_dir=SCHEMA_DIR)
            self.assertEqual(reused['mode'],'reused')
            (output/builder.BUNDLE).write_text('{}\n')
            with self.assertRaisesRegex(ValueError,'Snapshot content changed'):
                builder.run(PROJECT,output,'check',schema_dir=SCHEMA_DIR)

    def test_changed_review_cannot_reuse_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);review=root/'review';shutil.copytree(builder.REVIEW_DIR,review)
            output=root/'snapshot';builder.run(PROJECT,output,review_dir=review,schema_dir=SCHEMA_DIR)
            p=review/'2008.tsv';p.write_text(p.read_text()+'# reviewed input changed\n')
            with self.assertRaisesRegex(ValueError,'Snapshot inputs changed'):
                builder.run(PROJECT,output,review_dir=review,schema_dir=SCHEMA_DIR)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',type=Path,default=PROJECT)
    parser.add_argument('--schema-dir',type=Path)
    args,remaining=parser.parse_known_args()
    PROJECT=args.project.resolve();SCHEMA_DIR=(args.schema_dir or PROJECT/builder.SCHEMA_DIR).resolve()
    unittest.main(argv=[__file__]+remaining)
