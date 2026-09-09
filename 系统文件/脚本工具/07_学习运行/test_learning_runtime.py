"""Behavioral regressions. All artificial learner records stay in temporary dirs."""
import copy
from datetime import date
import json
import os
from pathlib import Path
import tempfile
import unittest
import uuid

import learning_runtime as lr


PROJECT = Path(os.environ.get('LEARNING_RUNTIME_TEST_PROJECT', str(Path(__file__).resolve().parents[3])))


def budget(**changes):
    value = {'unit': 'tokens', 'unit_name': 'tokens', 'week_start': '2026-09-07',
             'limit': 100, 'used': 40, 'reserved': 10, 'estimate': 30, 'retry_reserve': 10,
             'max_input_tokens_per_call': None, 'max_output_tokens_per_call': None}
    value.update(changes)
    return value


def feedback():
    return {'schema_version': 'offline-assessment-summary-v1.0.0',
            'summary_id': str(uuid.uuid4()), 'exam_track': 'MATH1',
            'summary_scope': 'whole_exam', 'reported_assessment_kind': 'self_practice',
            'completed_at': '2026-09-08T12:00:00+08:00',
            'verified_at': '2026-09-08T13:00:00+08:00',
            'earned_points': 100, 'maximum_points': 150, 'duration_seconds': 10800,
            'is_timed': True,
            'student_verification': {'mode': 'external_authoritative_self_check',
                'score_confirmed_by_student': True, 'answer_checked_after_first_pass': True,
                'teacher_answer_access': False},
            'dimensions': {k: None for k in lr.DIMENSIONS},
            'independent_measurement_status': 'unverified'}


class BudgetTests(unittest.TestCase):
    def check(self, **changes):
        return lr.budget_preflight(budget(**changes), date(2026, 9, 9))

    def test_known_budget_accounts_for_reservation_and_retry(self):
        r = self.check()
        self.assertTrue(r['allowed']); self.assertEqual(r['remaining_after_batch'], 10)
        self.assertFalse(r['reservation_created']); self.assertFalse(r['external_call_performed'])

    def test_unknown_cap_usage_or_estimate_denies(self):
        for key in ('limit', 'used', 'reserved', 'estimate', 'retry_reserve'):
            with self.subTest(key=key): self.assertFalse(self.check(**{key: None})['allowed'])

    def test_retry_cannot_fit_denies(self):
        self.assertFalse(self.check(retry_reserve=21)['allowed'])

    def test_cap_reached_stops_even_zero_estimate(self):
        self.assertFalse(self.check(used=100, reserved=0, estimate=0, retry_reserve=0)['allowed'])

    def test_old_week_and_non_monday_denied(self):
        for week in ('2026-08-31', '2026-09-08', None):
            self.assertFalse(self.check(week_start=week)['allowed'])

    def test_calls_need_input_and_output_bounds(self):
        self.assertFalse(self.check(unit='calls', unit_name='calls')['allowed'])
        self.assertTrue(self.check(unit='calls', unit_name='calls', max_input_tokens_per_call=100,
                                   max_output_tokens_per_call=100)['allowed'])

    def test_nonfinite_boolean_negative_and_fractional_tokens_denied(self):
        for value in (True, float('inf'), float('nan'), -1, 1.5):
            self.assertFalse(self.check(estimate=value)['allowed'])

    def test_unknown_fields_denied(self):
        self.assertFalse(self.check(automatic_approval=True)['allowed'])


class SummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.runtime = lr.schema_runtime(PROJECT)

    def test_whole_exam_can_be_validated_without_question_id(self):
        self.assertEqual(lr.validate_summary(feedback(), self.runtime), [])

    def test_identity_and_answer_fields_rejected(self):
        for key in ('question_id', 'paper_id', 'year', 'source', 'answer', 'notes', 'pool_handle'):
            r = feedback(); r[key] = 'synthetic'
            self.assertTrue(lr.validate_summary(r, self.runtime))

    def test_nested_extra_field_and_identity_in_id_rejected(self):
        r = feedback(); r['student_verification']['paper_id'] = 'synthetic'
        self.assertTrue(lr.validate_summary(r, self.runtime))
        r = feedback(); r['summary_id'] = 'M1-2008'
        self.assertTrue(lr.validate_summary(r, self.runtime))

    def test_numeric_values_cannot_impersonate_confirmation_booleans(self):
        r = feedback(); r['student_verification']['score_confirmed_by_student'] = 1
        self.assertTrue(lr.validate_summary(r, self.runtime))

    def test_score_bounds_and_finite_required(self):
        for field, value in [('earned_points', 151), ('earned_points', -1),
                             ('maximum_points', 0), ('earned_points', float('nan'))]:
            r = feedback(); r[field] = value
            self.assertTrue(lr.validate_summary(r, self.runtime))

    def test_invalid_time_and_chronology_rejected(self):
        for value in ('2026-09-08T11:00:00+08:00', '2026-09-08T13:00:00', 'not-a-date'):
            r = feedback(); r['verified_at'] = value
            self.assertTrue(lr.validate_summary(r, self.runtime))

    def test_total_score_cannot_imply_dimensions(self):
        for key in lr.DIMENSIONS:
            r = feedback(); r['dimensions'][key] = 'pass'
            self.assertTrue(lr.validate_summary(r, self.runtime))

    def test_claimed_sealed_report_does_not_activate_measurement(self):
        r = feedback(); r['reported_assessment_kind'] = 'sealed_exam'
        with tempfile.TemporaryDirectory() as tmp:
            result = lr.append_summary(Path(tmp) / 'log', r, self.runtime)
            self.assertFalse(result['independent_measurement_activated'])
        r['independent_measurement_status'] = 'verified'
        self.assertTrue(lr.validate_summary(r, self.runtime))

    def test_append_preserves_history_and_duplicate_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / 'log'; first = feedback()
            lr.append_summary(log, first, self.runtime); before = log.read_bytes()
            with self.assertRaises(ValueError): lr.append_summary(log, first, self.runtime)
            self.assertEqual(log.read_bytes(), before)
            lr.append_summary(log, feedback(), self.runtime)
            self.assertTrue(log.read_bytes().startswith(before))
            self.assertEqual(len(lr.jsonl(log.read_text())), 2)

    def test_corrupted_history_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / 'log'; log.write_text('{bad json}\n'); before = log.read_bytes()
            with self.assertRaises(ValueError): lr.append_summary(log, feedback(), self.runtime)
            self.assertEqual(log.read_bytes(), before)

    def test_missing_final_newline_remains_append_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / 'log'; before = json.dumps(feedback()).encode(); log.write_bytes(before)
            lr.append_summary(log, feedback(), self.runtime)
            self.assertTrue(log.read_bytes().startswith(before))
            self.assertEqual(len(lr.jsonl(log.read_text())), 2)


class IndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = lr.read(PROJECT / lr.POLICY)
        cls.data = lr.build(PROJECT, cls.policy)

    def test_canonical_and_core_not_double_counted(self):
        r = self.data['readiness.json']
        self.assertEqual((r['question_count'], r['core_question_count'], r['core_paper_count']), (8024, 1277, 37))

    def test_human_unresolved_not_confused_with_assistant_review(self):
        r = self.data['readiness.json']
        self.assertEqual(r['human_issue_questions_by_track'], {})
        self.assertEqual(r['human_issue_question_count'], 0)
        self.assertFalse(r['human_signoff_inferred'])

    def test_no_feedback_does_not_imply_unlearned_or_zero(self):
        r = self.data['readiness.json']
        self.assertEqual(r['attempt_record_count'], 0)
        for key in ('learner_state', 'current_frontier', 'review_queue'): self.assertIsNone(r[key])
        for key in ('F', 'C', 'V'): self.assertIsNone(r['formal_E'][key])

    def test_navigation_complete_and_unbatched_explicit(self):
        r = self.data['readiness.json']
        self.assertEqual((r['scope_count'], r['section_count'], r['batch_count']), (166, 479, 208))
        orphan = [s for c in self.data['course_navigation.json']['courses'] for s in c['sections'] if not s['batch_ids']]
        self.assertEqual(len(orphan), 12)
        self.assertTrue(all(s['scope_status'] == 'out_of_scope_candidate' for s in orphan))

    def test_known_teacher_exposure_does_not_assert_student_exposure(self):
        rows = self.data['teacher_exposure.json']['records']
        self.assertEqual(len(rows), 1277)
        self.assertTrue(all(r['student_seen_status'] == 'unknown_current' and
                            not r['hidden_measurement_eligible'] for r in rows))

    def test_E_qualification_requires_only_necessary_checks(self):
        d = {k: True for k in lr.E_CHECKS}; d['all_L3_verified'] = False
        self.assertTrue(lr.qualify_paper(d)['eligible'])
        for key in lr.E_CHECKS:
            partial = dict(d); partial[key] = None
            self.assertFalse(lr.qualify_paper(partial)['eligible'])
        self.assertFalse(lr.qualify_paper()['eligible'])

    def test_duplicate_overlay_or_modified_L0_rejected(self):
        r = {'question_id': 'test', 'l0': {'points': 1}, 'l1': {}}
        b = {'record_count': 1, 'records': [r]}
        with self.assertRaises(ValueError): lr.merge_annotations([('l1', b), ('a', b), ('b', b)])
        changed = copy.deepcopy(b); changed['records'][0]['l0']['points'] = 2
        with self.assertRaises(ValueError): lr.merge_annotations([('l1', b), ('a', changed)])

    def test_snapshot_tampering_detected_and_overwrite_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'snapshot'
            lr.write_build(PROJECT, output, self.policy)
            self.assertEqual(lr.check_build(PROJECT, output, self.policy)['status'], 'PASS')
            with self.assertRaises(ValueError): lr.write_build(PROJECT, output, self.policy)
            (output / 'readiness.json').write_text('{}')
            self.assertEqual(lr.check_build(PROJECT, output, self.policy)['status'], 'FAIL')

    def test_path_escape_rejected(self):
        with self.assertRaises(ValueError): lr.inside(PROJECT, '../outside')


if __name__ == '__main__':
    unittest.main()
