#!/usr/bin/env python3
"""Offline regression checks for the 2009–2012 CS408 annotation release."""
import argparse
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import build_cs408_l23 as builder

PROJECT=Path('/home/elexs/Dynamic-learning-program')
SCHEMA_DIR=None


class CS408AnnotationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload=builder.generate(PROJECT)
        cls.bundle=json.loads(cls.payload[builder.BUNDLE])
        cls.scores=json.loads(cls.payload['scoring_evidence_v1.json'])

    def record(self,bundle,qid):
        return next(r for r in bundle['records'] if r['question_id']==qid)

    def validate(self,bundle=None,scoring=None,payload=None):
        value=dict(self.payload if payload is None else payload)
        if bundle is not None:value[builder.BUNDLE]=builder.json_bytes(bundle)
        if scoring is not None:value['scoring_evidence_v1.json']=builder.json_bytes(scoring)
        return builder.validate_data(PROJECT,SCHEMA_DIR,value)

    def test_exact_four_year_scope_and_cumulative_layers(self):
        result=self.validate()
        self.assertEqual(result['status'],'PASS',result['errors'])
        for y in range(2009,2013):
            records=[r for r in self.bundle['records'] if r['l0']['year']==y]
            self.assertEqual(len(records),47)
            self.assertEqual(sum(r['l0']['question_type']=='choice' for r in records),40)
        baseline={r['question_id']:r for r in builder.read_json(PROJECT/builder.L1_PATH)['records']}
        for r in self.bundle['records']:
            self.assertEqual(r['l0'],baseline[r['question_id']]['l0'])
            self.assertEqual(r['l1'],baseline[r['question_id']]['l1'])

    def test_complete_local_rubrics_are_promoted(self):
        expected={'408-09-A-T41':[4,6],'408-09-A-T43':[2,1,1,1,1,1,1],'408-12-A-T41':[5,2,3]}
        for q,points in expected.items():
            self.assertEqual([u['points'] for u in self.record(self.bundle,q)['l3']['score_units']],points)

    def test_unprovided_split_is_rejected_even_if_sum_matches(self):
        value=copy.deepcopy(self.bundle);r=self.record(value,'408-10-A-T44')
        unit=r['l3']['score_units'][0];unit['points']=5
        other=copy.deepcopy(unit);other['unit_id']=r['question_id']+':S1'
        r['l3']['score_units'].append(other)
        self.assertEqual(self.validate(value)['status'],'FAIL')

    def test_modified_known_rubric_is_rejected(self):
        value=copy.deepcopy(self.bundle);r=self.record(value,'408-09-A-T41')
        r['l3']['score_units'][0]['points']=5
        r['l3']['score_units'][1]['points']=5
        self.assertEqual(self.validate(value)['status'],'FAIL')

    def test_conflicting_total_not_silently_resolved(self):
        q='408-12-A-T43';r=self.record(self.bundle,q)
        self.assertEqual(r['l0']['original_points'],8)
        self.assertIsNone(r['l3']['score_units'][0]['points'])
        self.assertEqual(sum(x['points'] for x in self.record(self.scores,q)['documented_subpoints']),10)
        self.assertTrue(r['l2']['main_knowledge'])
        self.assertTrue(r['l3']['evidence_steps'][0]['steps'])
        for guess in (8,10):
            value=copy.deepcopy(self.bundle)
            self.record(value,q)['l3']['score_units'][0]['points']=guess
            self.assertEqual(self.validate(value)['status'],'FAIL')

    def test_algorithm_rule_does_not_create_remaining_points(self):
        q='408-12-A-T42';r=self.record(self.bundle,q)
        self.assertEqual([u['points'] for u in r['l3']['score_units']],[15])
        rules=self.record(self.scores,q)['conditional_rules']
        self.assertEqual([x['points'] for x in rules],[12,9,None,None])
        self.assertTrue(all(x['target_task_ids']==[] and x['scope_status']=='needs_review' for x in rules))
        self.assertEqual(r['l3']['review_status_by_field']['score_units'],'needs_review')

    def test_partial_scores_preserved_without_remainder_inference(self):
        q='408-12-A-T44'
        self.assertEqual([u['points'] for u in self.record(self.bundle,q)['l3']['score_units']],[10])
        parts=self.record(self.scores,q)['documented_subpoints']
        self.assertEqual([u['points'] for u in parts],[2,2,1,1])
        self.assertTrue(all(x['promoted_unit_id'] is None and x['count_separately'] is False for x in parts))

    def test_conditional_and_partial_evidence_cannot_be_added_twice(self):
        for q,key,field in [('408-09-A-T42','conditional_rules','additive'),('408-12-A-T44','documented_subpoints','count_separately')]:
            value=copy.deepcopy(self.scores);self.record(value,q)[key][0][field]=True
            self.assertEqual(self.validate(scoring=value)['status'],'FAIL')

    def test_source_lines_and_score_evidence_cannot_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            review=Path(temp)/'review';shutil.copytree(builder.REVIEW_DIR,review)
            plan=builder.read_json(review/'scoring_plan_v1.json')
            plan['questions']['408-09-A-T41']['units'][0]['anchor']['line']=10
            (review/'scoring_plan_v1.json').write_bytes(builder.json_bytes(plan))
            with self.assertRaisesRegex(ValueError,'anchor outside question'):
                builder.generate(PROJECT,review)

    def test_every_rubric_cue_requires_review(self):
        with tempfile.TemporaryDirectory() as temp:
            review=Path(temp)/'review';shutil.copytree(builder.REVIEW_DIR,review)
            plan=builder.read_json(review/'scoring_plan_v1.json')
            plan['questions'].pop('408-11-A-T47')
            (review/'scoring_plan_v1.json').write_bytes(builder.json_bytes(plan))
            with self.assertRaisesRegex(ValueError,'rubric cues must all be reviewed'):
                builder.generate(PROJECT,review)

    def test_source_or_image_hash_change_requires_review(self):
        for field in ('source_files','images'):
            with tempfile.TemporaryDirectory() as temp:
                review=Path(temp)/'review';shutil.copytree(builder.REVIEW_DIR,review)
                lock=builder.read_json(review/'source_lock_v1.json')
                lock[field][next(iter(lock[field]))]='0'*64
                (review/'source_lock_v1.json').write_bytes(builder.json_bytes(lock))
                with self.assertRaises(ValueError):builder.generate(PROJECT,review)

    def test_2013_or_other_subject_record_cannot_replace_scope(self):
        for bad in ('408-13-C-T01','M1-09-C-T01'):
            value=copy.deepcopy(self.bundle);value['records'][0]['question_id']=bad
            self.assertEqual(self.validate(value)['status'],'FAIL')

    def test_locked_layer_changes_rejected(self):
        for layer,field,new in [('l0','original_points',999),('l1','official_scope_coarse','changed')]:
            value=copy.deepcopy(self.bundle);value['records'][0][layer][field]=new
            self.assertEqual(self.validate(value)['status'],'FAIL')

    def test_omission_needs_grounded_reason_and_status(self):
        value=copy.deepcopy(self.bundle);value['records'][0]['l2'].pop('primary_method')
        self.assertEqual(self.validate(value)['status'],'FAIL')
        value=copy.deepcopy(self.bundle);r=self.record(value,'408-12-A-T43')
        r['field_omissions']=[];r['l3']['review_status_by_field']['score_units']='verified'
        self.assertEqual(self.validate(value)['status'],'FAIL')

    def test_one_main_and_secondary_count_constraint(self):
        value=copy.deepcopy(self.bundle);value['records'][0]['l2'].pop('main_knowledge')
        self.assertEqual(self.validate(value)['status'],'FAIL')
        value=copy.deepcopy(self.bundle);r=next(r for r in value['records'] if r['l0']['question_type']=='choice')
        r['l2']['secondary_knowledge']=[r['l2']['main_knowledge']]*2
        self.assertEqual(self.validate(value)['status'],'FAIL')

    def test_dependency_targets_and_direction_checked(self):
        for target in ('missing',None):
            value=copy.deepcopy(self.bundle)
            r=next(r for r in value['records'] if r['l3']['inter_question_dependency']['relations'])
            edge=r['l3']['inter_question_dependency']['relations'][0]
            edge['to_question_id']=target or edge['from_question_id']
            self.assertEqual(self.validate(value)['status'],'FAIL')

    def test_isomorphism_reciprocity_and_registry(self):
        value=copy.deepcopy(self.bundle)
        r=next(r for r in value['records'] if r['l3']['isomorphic_relation'])
        r['l3']['isomorphic_relation']['related_question_ids'].append('408-13-C-T01')
        self.assertEqual(self.validate(value)['status'],'FAIL')
        value=copy.deepcopy(self.bundle);value['records'][0]['l2']['main_knowledge']['id']='unknown'
        self.assertEqual(self.validate(value)['status'],'FAIL')

    def test_answer_roles_students_rejected_in_core_and_sidecars(self):
        for key in ('answer','solution','data_role','student_score'):
            value=copy.deepcopy(self.bundle);value['records'][0]['l3'][key]='forbidden'
            self.assertEqual(self.validate(value)['status'],'FAIL')
            value=copy.deepcopy(self.scores);value[key]='forbidden'
            self.assertEqual(self.validate(scoring=value)['status'],'FAIL')

    def test_scoring_evidence_coverage_and_value_integrity(self):
        value=copy.deepcopy(self.scores);value['records'].pop()
        self.assertEqual(self.validate(scoring=value)['status'],'FAIL')
        value=copy.deepcopy(self.scores)
        self.record(value,'408-12-A-T44')['documented_subpoints'][0]['points']=4
        self.assertEqual(self.validate(scoring=value)['status'],'FAIL')

    def test_build_reuse_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'snapshot'
            self.assertEqual(builder.run(PROJECT,output,schema_dir=SCHEMA_DIR)['mode'],'built')
            self.assertEqual(builder.run(PROJECT,output,schema_dir=SCHEMA_DIR)['mode'],'reused')
            (output/'scoring_evidence_v1.json').write_text('{}\n')
            with self.assertRaisesRegex(ValueError,'Snapshot content changed'):
                builder.run(PROJECT,output,'check',schema_dir=SCHEMA_DIR)

    def test_changed_review_cannot_reuse_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);review=root/'review';shutil.copytree(builder.REVIEW_DIR,review)
            output=root/'snapshot';builder.run(PROJECT,output,review_dir=review,schema_dir=SCHEMA_DIR)
            p=review/'2009.psv';p.write_text(p.read_text()+'# input changed\n')
            with self.assertRaisesRegex(ValueError,'Snapshot inputs changed'):
                builder.run(PROJECT,output,review_dir=review,schema_dir=SCHEMA_DIR)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',type=Path,default=PROJECT)
    parser.add_argument('--schema-dir',type=Path)
    args,rest=parser.parse_known_args()
    PROJECT=args.project.resolve();SCHEMA_DIR=(args.schema_dir or PROJECT/builder.SCHEMA_DIR).resolve()
    unittest.main(argv=[__file__]+rest)
