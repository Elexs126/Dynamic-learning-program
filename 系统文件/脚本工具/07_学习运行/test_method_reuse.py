"""Method reuse must not imply mastery, full solutions, or blind-test hints."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import daily_practice as dp
import method_reuse as mr
from test_daily_practice import PROJECT, DAY, question, attempt


def library(records):
    methods = {mid: {'name': 'method-' + mid, 'exam_track': 'MATH1',
                     'principle': 'shared operation', 'conditions': 'check conditions',
                     'boundaries': 'not a whole solution', 'decision_use': 'next repair'}
               for mid in ['P', 'R']}
    return {'version': mr.VERSION, 'methods': methods,
            'links': [{'question_id': qid, 'method_id': mid,
                       'question_hash_sha256': records[qid]['l0']['question_hash_sha256'],
                       'status': status, 'extent': extent, 'basis': 'fixture source review'}
                      for qid, mid, status, extent in [('Q1', 'P', 'checked', 'step'),
                          ('Q1', 'R', 'checked', 'whole'), ('Q2', 'P', 'checked', 'step'),
                          ('Q3', 'R', 'candidate', 'whole')]]}


class MethodReuseTests(unittest.TestCase):
    def setUp(self):
        self.records = {qid: question(qid, kid='K' + qid) for qid in ['Q1', 'Q2', 'Q3']}
        self.library = library(self.records)

    def candidates(self, methods=None, rows=None, teacher=None):
        rows = rows or []
        state = dp.derive_state(self.records, rows, [], DAY, 80)[0]
        return dp.prepare_candidates(PROJECT, self.records, state, rows, {'courses': []},
                                     'MATH1', teacher or {}, methods)[0]

    def test_same_question_has_multiple_methods_without_merging_knowledge(self):
        report = mr.report(self.library, self.records, question_id='Q1')
        self.assertEqual({l['method_id'] for l in report['questions'][0]['links']}, {'P', 'R'})
        state = dp.derive_state(self.records, [attempt('Q1'), attempt('Q2')], [], DAY, 80)[0]
        self.assertEqual(set(state['abilities']), {'KQ1', 'KQ2'})
        self.assertTrue(all(a['stage'] == '已接触' for a in state['abilities'].values()))

    def test_step_reuse_is_reported_separately_from_whole_solution(self):
        report = mr.report(self.library, self.records, method_id='P')
        self.assertEqual(report['checked_step_question_ids'], ['Q1', 'Q2'])
        self.assertEqual(report['checked_whole_question_ids'], [])

    def test_candidate_rejected_and_stale_links_never_drive_reuse(self):
        before = copy.deepcopy(self.library)
        self.assertNotIn('Q3', mr.checked_index(self.library, self.records))
        self.records['Q1']['l0']['question_hash_sha256'] = 'f' * 64
        report = mr.report(self.library, self.records, question_id='Q1')
        self.assertEqual({l['effective_status'] for l in report['questions'][0]['links']}, {'stale'})
        self.assertNotIn('Q1', mr.checked_index(self.library, self.records))
        self.assertEqual(self.library, before)
        self.library['links'][2]['status'] = 'rejected'
        self.assertNotIn('Q2', mr.checked_index(self.library, self.records))

    def test_missing_library_is_optional_and_does_not_block_existing_learning(self):
        with tempfile.TemporaryDirectory() as folder:
            empty = mr.load_library(Path(folder), self.records)
        self.assertEqual(empty['links'], [])
        self.assertEqual(dp.derive_state(self.records, [], [], DAY, 80)[0]['abilities'], {})

    def test_unknown_knowledge_links_remain_unreviewed(self):
        self.records['Q4'] = question('Q4', kid='KQ4')
        result = mr.report(self.library, self.records, knowledge_id='KQ4')
        self.assertEqual(result['questions'][0]['links'], [])
        self.assertEqual(result['checked_whole_question_ids'], [])

    def test_method_reuse_needs_explicit_teacher_choice(self):
        original = copy.deepcopy(self.records)
        self.assertEqual(self.candidates(), self.candidates(self.library))
        teacher = {'subjects': {'MATH1': {'preferred_method_ids': ['P']}}}
        selected = self.candidates(self.library, teacher=teacher)
        self.assertEqual({c['question_id'] for c in selected[:2]}, {'Q1', 'Q2'})
        self.assertEqual(selected[2]['preferred_method_ids'], [])
        self.assertEqual(self.records, original)

    def test_method_preference_does_not_override_due_or_required_tasks(self):
        teacher = {'subjects': {'MATH1': {'preferred_method_ids': ['P'], 'required_knowledge_ids': ['KQ3']}}}
        self.assertEqual(self.candidates(self.library, teacher=teacher)[0]['question_id'], 'Q3')
        rows = [attempt('Q3', next_review_at='2026-10-05T09:00:00+08:00')]
        self.assertEqual(self.candidates(self.library, rows, teacher)[0]['question_id'], 'Q3')

    def test_teacher_plan_rejects_unknown_cross_track_or_duplicate_methods(self):
        for mids in [['missing'], ['P', 'P']]:
            with self.assertRaises(ValueError):
                dp.validate_teacher_plan({'version': 'daily-teacher-plan-v1',
                    'subjects': {'MATH1': {'preferred_method_ids': mids}}}, self.records, methods=self.library)
        self.library['methods']['P']['exam_track'] = 'CS408'
        with self.assertRaises(ValueError):
            dp.validate_teacher_plan({'version': 'daily-teacher-plan-v1',
                'subjects': {'MATH1': {'preferred_method_ids': ['P']}}}, self.records, methods=self.library)

    def test_library_validation_checks_provenance_duplicates_and_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / mr.LIBRARY_PATH
            path.parent.mkdir(parents=True)
            path.write_text(dp.lr.dump(self.library))
            self.assertEqual(mr.load_library(root, self.records), self.library)
            for change in [dict(basis=''), dict(question_hash_sha256='bad'),
                           dict(method_id='missing'), dict(extent='optimal')]:
                bad = copy.deepcopy(self.library)
                bad['links'][0].update(change)
                path.write_text(dp.lr.dump(bad))
                with self.assertRaises(ValueError):
                    mr.load_library(root, self.records)
            self.library['links'].append(copy.deepcopy(self.library['links'][0]))
            path.write_text(dp.lr.dump(self.library))
            with self.assertRaises(ValueError):
                mr.load_library(root, self.records)

    def test_reuse_explanation_is_not_exposed_in_maintenance_or_exam(self):
        paper = {'mode': 'repair', 'questions': [
            {'question_id': 'Q1', 'preferred_method_ids': ['P']},
            {'question_id': 'Q2', 'preferred_method_ids': ['P']}]}
        blocks = mr.learning_blocks(paper, self.library, self.records)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(len(blocks[0]['questions']), 2)
        for mode in ['maintenance', 'exam']:
            paper['mode'] = mode
            self.assertEqual(mr.learning_blocks(paper, self.library, self.records), [])

    def test_real_relationships_are_substeps_not_three_full_solutions(self):
        records = dp.load_inputs(PROJECT)[0]
        data = mr.load_library(PROJECT, records)
        result = mr.report(data, records)
        self.assertEqual(len(result['checked_step_question_ids']), 3)
        self.assertEqual(result['checked_whole_question_ids'], [])
        q = mr.report(data, records, question_id='M1-10-F-T10')['questions'][0]
        self.assertEqual(len(q['links']), 2)
        self.assertEqual(dp.derive_state(records, [], [], DAY, 80)[0]['abilities'], {})

    def test_real_repair_preview_round_trip_and_no_exam_method_hints(self):
        qid = 'M1-10-F-T10'
        records = dp.load_inputs(PROJECT)[0]
        method = 'MR_MATH1_PARTS'
        plan = {'version': 'daily-teacher-plan-v1', 'subjects': {'MATH1': {
            'mode': 'repair', 'priority_knowledge_ids': [dp.knowledge(records[qid])],
            'preferred_method_ids': [method]}}}
        with tempfile.TemporaryDirectory() as folder:
            before = (PROJECT / dp.lr.ATTEMPTS).read_bytes()
            day = dp.build_day(PROJECT, DAY, plan)[0]
            self.assertIn(qid, {q['question_id'] for q in day['papers']['MATH1']['questions']})
            dp.write_artifacts(day, Path(folder) / 'preview')
            dp.verify_frozen(Path(folder) / 'preview')
            entrance = (Path(folder) / 'preview/index.html').read_text()
            paper = (Path(folder) / 'preview/数学一.html').read_text()
            self.assertIn('本次复用', entrance)
            self.assertIn('从乘积求导选择分部积分', entrance)
            self.assertNotIn('从乘积求导选择分部积分', paper)
            self.assertNotIn(method, paper)
            self.assertEqual((PROJECT / dp.lr.ATTEMPTS).read_bytes(), before)
        # The exam sample itself must not be selected by the preferred method.
        plan['subjects']['MATH1']['mode'] = 'exam'
        with patch.object(dp, 'prepare_candidates', wraps=dp.prepare_candidates) as prepare:
            day = dp.build_day(PROJECT, DAY, plan)[0]
        self.assertIsNone(prepare.call_args_list[0].args[-1])
        self.assertEqual(day['papers']['MATH1']['method_blocks'], [])


if __name__ == '__main__':
    unittest.main()
