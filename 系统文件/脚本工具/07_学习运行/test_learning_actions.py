"""Cross-question evidence, cold measurement and unresolved review behavior."""
import copy
from datetime import date
from pathlib import Path
import tempfile
import shutil
import unittest
from unittest.mock import patch

import daily_practice as dp
import learning_actions as la
from test_daily_practice import PROJECT, DAY, question, attempt


def mapping(records, links=None):
    links = links or {q: ['A'] for q in records}
    return {'version': 'capability-map-v1',
            'mechanisms': {'M': {'name': 'mechanism', 'model': 'model', 'boundaries': 'boundary', 'decision_use': 'selection'}},
            'abilities': {a: {'name': a, 'exam_track': 'MATH1', 'mechanism_id': 'M', 'decision_use': 'review'}
                          for a in {a for ids in links.values() for a in ids}},
            'questions': {qid: {'primary_ability_id': ids[0], 'ability_ids': ids,
                                'score_supports_primary': len(ids) == 1,
                                'question_hash_sha256': records[qid]['l0']['question_hash_sha256'], 'basis': 'fixture'}
                          for qid, ids in links.items()}}


def observed(qid, aid='A', score=90, error=None, checked=None, **changes):
    observation = {'ability_id': aid, 'first_score_pct': score,
                   'dimensions': {d: None for d in dp.lr.DIMENSIONS},
                   'error_code': error, 'checked_error_codes': checked or []}
    return attempt(qid, schema_version='attempt-record-v1.1.0', target_ability_id=aid,
                   ability_observations=[observation], first_score_pct=score,
                   primary_error_code=error, **changes)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.records = {qid: question(qid, kid='K' + qid) for qid in ['Q1', 'Q2', 'Q3']}
        self.mapping = mapping(self.records)

    def state(self, rows):
        return dp.derive_state(self.records, rows, [], DAY, 80, self.mapping)[0]

    def test_different_old_tags_accumulate_shared_capability(self):
        state = self.state([attempt('Q1'), attempt('Q2')])
        self.assertEqual(set(state['abilities']), {'A'})
        self.assertEqual(state['abilities']['A']['stage'], '工作掌握')
        self.assertEqual(state['abilities']['A']['independent_certification'], 'unverified')

    def test_different_ids_with_identical_stem_do_not_count_twice(self):
        self.records['Q2']['l0']['question_hash_sha256'] = self.records['Q1']['l0']['question_hash_sha256']
        state = self.state([observed('Q1'), observed('Q2')])
        self.assertEqual(state['abilities']['A']['stage'], '已接触')

    def test_composite_whole_score_does_not_certify_parts(self):
        self.mapping = mapping(self.records, {qid: ['A', 'B'] for qid in self.records})
        state = self.state([attempt('Q1'), attempt('Q2')])
        self.assertNotIn('A', state['abilities'])
        self.assertNotIn('B', state['abilities'])
        state = self.state([observed('Q1'), observed('Q2')])
        self.assertEqual(set(state['abilities']), {'A'})
        self.assertEqual(state['abilities']['A']['stage'], '工作掌握')

    def test_explicit_second_part_updates_only_observed_parts(self):
        self.mapping = mapping(self.records, {qid: ['A', 'B'] for qid in self.records})
        row = observed('Q1')
        row['ability_observations'].append(observed('Q1', 'B', score=20)['ability_observations'][0])
        state = self.state([row])
        self.assertFalse(state['abilities']['A']['weak'])
        self.assertTrue(state['abilities']['B']['weak'])
        self.assertEqual(state['attempt_count'], 1)

    def test_unobserved_composite_keeps_ability_unknown(self):
        row = observed('Q1')
        row['ability_observations'] = []
        state = self.state([row])
        self.assertEqual(state['abilities'], {})
        self.assertEqual(state['attempt_count'], 1)

    def test_ordinary_cold_pass_contributes_without_independent_certification(self):
        state = self.state([observed('Q1'), observed('Q2', attempt_kind='cold_test',
                           interval_hours=72, is_mixed=True, batch_id='cold')])
        self.assertEqual(state['abilities']['A']['stage'], '工作掌握')
        self.assertTrue(state['abilities']['A']['ordinary_cold_test_passed'])
        self.assertEqual(state['abilities']['A']['independent_certification'], 'unverified')

    def test_recent_failure_requires_fresh_working_evidence(self):
        rows = [observed('Q1'), observed('Q2'), observed('Q3', score=20)]
        self.assertEqual(self.state(rows)['abilities']['A']['stage'], '已接触')

    def test_hidden_and_startup_scores_do_not_update_personal_ability(self):
        for role in ['SEALED', 'FIXED_AUDIT', 'STARTUP_TRAINING_ONLY']:
            self.assertEqual(self.state([observed('Q1', usage_role=role)])['abilities'], {})

    def test_two_due_originals_collapse_to_one_capability_task(self):
        rows = [observed(q, next_review_at='2026-10-05T09:00:00+08:00') for q in ['Q1', 'Q2']]
        tasks = self.state(rows)['review_tasks']
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['question_ids'], ['Q1', 'Q2'])
        self.assertTrue(tasks[0]['due'])

    def test_unchecked_misconception_remains_due_after_general_success(self):
        rows = [observed('Q1', score=20, error='procedure', next_review_at='2026-10-05T09:00:00+08:00'), observed('Q2')]
        tasks = self.state(rows)['review_tasks']
        self.assertEqual([t['error_code'] for t in tasks if t['due']], ['procedure'])
        rows[-1]['ability_observations'][0]['checked_error_codes'] = ['procedure']
        self.assertFalse(any(t['due'] for t in self.state(rows)['review_tasks']))

    def test_hinted_success_does_not_clear_misconception_debt(self):
        rows = [observed('Q1', score=20, error='procedure', next_review_at='2026-10-05T09:00:00+08:00'),
                observed('Q2', checked=['procedure'], highest_hint_level_used='L1')]
        self.assertTrue(any(t['due'] for t in self.state(rows)['review_tasks']))

    def test_checked_label_without_prior_error_does_not_invent_debt(self):
        tasks = self.state([observed('Q1', checked=['procedure'])])['review_tasks']
        self.assertEqual([t['error_code'] for t in tasks], [None])

    def test_unrelated_capability_cannot_clear_review(self):
        self.mapping = mapping(self.records, {'Q1': ['A'], 'Q2': ['B'], 'Q3': ['A']})
        rows = [observed('Q1', error='procedure', next_review_at='2026-10-05T09:00:00+08:00'),
                observed('Q2', 'B', checked=['procedure'])]
        self.assertTrue(next(t for t in self.state(rows)['review_tasks'] if t['ability_id'] == 'A')['due'])

    def test_successful_new_probe_does_not_reissue_old_due_original(self):
        rows = [observed('Q1', next_review_at='2026-10-05T09:00:00+08:00'), observed('Q2')]
        state = self.state(rows)
        candidates, due, _ = dp.prepare_candidates(PROJECT, self.records, state, rows, {'courses': []}, 'MATH1', {})
        self.assertEqual(due, set())
        self.assertNotIn('Q1', {c['question_id'] for c in candidates})

    def test_observation_validator_rejects_unlinked_ability_and_untimed_dimension(self):
        with patch.object(la, 'load_map', return_value=self.mapping):
            dp.validate_attempts(PROJECT, [observed('Q1')], self.records)
            for row in [observed('Q1', 'B'), observed('Q1', attempt_kind='cold_test', interval_hours=24)]:
                with self.assertRaises(ValueError):
                    dp.validate_attempts(PROJECT, [row], self.records)
            row = observed('Q1', is_timed=False)
            row['ability_observations'][0]['dimensions']['timed_fluency'] = 'pass'
            with self.assertRaises(ValueError):
                dp.validate_attempts(PROJECT, [row], self.records)

    def test_valid_mixed_ordinary_cold_batch_accepts_teacher_visible_training(self):
        self.mapping = mapping(self.records, {'Q1': ['A'], 'Q2': ['B'], 'Q3': ['A']})
        rows = [observed('Q1', 'A', attempt_kind='cold_test', interval_hours=72, is_mixed=True, batch_id='C'),
                observed('Q2', 'B', attempt_kind='cold_test', interval_hours=72, is_mixed=True, batch_id='C')]
        with patch.object(la, 'load_map', return_value=self.mapping):
            dp.validate_attempts(PROJECT, rows, self.records)

    def test_map_requires_unchanged_source_and_concrete_decision_use(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / la.MAP_PATH
            path.parent.mkdir(parents=True)
            path.write_text(dp.lr.dump(self.mapping))
            la.load_map(root, self.records)
            self.mapping['questions']['Q1']['question_hash_sha256'] = '0' * 64
            path.write_text(dp.lr.dump(self.mapping))
            with self.assertRaises(ValueError):
                la.load_map(root, self.records)

    def test_action_depends_on_observed_obstacle_and_keeps_uncertainty(self):
        ability = self.state([observed('Q1', score=30, error='procedure')])['abilities']['A']
        self.assertIn('单练', la.action_for(ability, self.mapping)['action'])
        ability['primary_error_code'] = None
        self.assertIn('短问题', la.action_for(ability, self.mapping)['action'])


class SelectionTests(unittest.TestCase):
    def test_new_format_feedback_round_trip_appends_once_and_preserves_unobserved(self):
        records = {qid: question(qid, kid=qid) for qid in ['Q1', 'Q2']}
        data = mapping(records, {'Q1': ['A'], 'Q2': ['B']})
        rows = [observed('Q1', 'A', attempt_kind='cold_test', interval_hours=72, is_mixed=True, batch_id='C'),
                observed('Q2', 'B', attempt_kind='cold_test', interval_hours=72, is_mixed=True, batch_id='C')]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for rel in [dp.CONFIG, '系统文件/系统配置/execution_contract_v1.json',
                        '系统文件/数据规范/attempt_record.schema.json', '系统文件/数据规范/attempt_record_v1_1.schema.json',
                        dp.lr.OFFLINE_SCHEMA, '系统文件/脚本工具/05_标注与规范校验/json_schema_runtime.py',
                        '系统文件/脚本工具/05_标注与规范校验/validate_attempt_log.py']:
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(PROJECT / rel, target)
            (root / la.MAP_PATH).write_text(dp.lr.dump(data))
            log = root / dp.lr.ATTEMPTS
            log.parent.mkdir(parents=True)
            log.write_text('')
            def inputs(project):
                return records, dp.lr.jsonl(log.read_text()), [], {'courses': []}, {'runtime_snapshot': 'fixture'}
            with patch.object(dp, 'load_inputs', side_effect=inputs):
                result = dp.generate(root, DAY, root / 'daily', feedback=rows)
                self.assertEqual(result['appended_attempts'], 2)
                self.assertEqual(dp.generate(root, DAY, root / 'daily', feedback=rows)['status'], 'REUSED_FROZEN')
            saved = dp.lr.jsonl(log.read_text())
            self.assertEqual(len(saved), 2)
            self.assertTrue(all(r['schema_version'] == 'attempt-record-v1.1.0' for r in saved))
            state = dp.lr.read(root / 'daily/学习状态与明日计划.json')['state']
            self.assertEqual(set(state['abilities']), {'A', 'B'})
            self.assertTrue(all(v is None for a in state['abilities'].values() for v in a['dimensions'].values()))

    def test_repair_can_use_only_one_type_and_does_not_fill_for_appearance(self):
        q = question('Q1')
        c = {'question_id': 'Q1', 'q': q, 'knowledge_id': 'K1', 'reason': '修补缺口', 'rank': (0,)}
        policy = dp.lr.read(PROJECT / dp.CONFIG)
        speed = dp.estimate_speed({'Q1': q}, [], 'MATH1', policy)
        with patch.object(dp, 'question_body', return_value=('题干', PROJECT / 'README.md')), \
                patch.object(dp, 'render_markdown', return_value='题干'):
            # Existing source file is needed only for provenance hashing.
            q['l0']['source_file'] = 'README.md'
            paper = dp.select_paper(PROJECT, [c], set(), {}, 'MATH1', {'practice_minutes': 4}, speed, policy, 'repair')
        self.assertEqual(paper['status'], 'ready')
        self.assertEqual(paper['counts'], {'choice': 1, 'fill': 0, 'analytical': 0})
        self.assertEqual(paper['estimated_minutes'], 4)

    def test_exam_mode_retains_type_proportion_constraint(self):
        q = question('Q1')
        c = {'question_id': 'Q1', 'q': q, 'knowledge_id': 'K1', 'reason': '练习', 'rank': (0,)}
        policy = dp.lr.read(PROJECT / dp.CONFIG)
        speed = dp.estimate_speed({'Q1': q}, [], 'MATH1', policy)
        paper = dp.select_paper(PROJECT, [c], set(), {}, 'MATH1', {'practice_minutes': 4}, speed, policy, 'exam')
        self.assertNotEqual(paper['status'], 'ready')

    def test_scheduling_review_probe_does_not_finish_review(self):
        records = {qid: question(qid) for qid in ['Q1', 'Q2']}
        state = dp.derive_state(records, [observed('Q1', next_review_at='2026-10-05T09:00:00+08:00')], [], DAY, 80, mapping(records))[0]
        before = copy.deepcopy(state['review_tasks'])
        q = records['Q2']
        q['l0']['source_file'] = 'README.md'
        candidate = {'question_id': 'Q2', 'q': q, 'knowledge_id': 'A', 'reason': '到期复习',
                     'review_tasks': before, 'rank': (0,)}
        policy = dp.lr.read(PROJECT / dp.CONFIG)
        with patch.object(dp, 'question_body', return_value=('题干', PROJECT / 'README.md')), \
                patch.object(dp, 'render_markdown', return_value='题干'):
            paper = dp.select_paper(PROJECT, [candidate], {'Q1'}, {}, 'MATH1', {'practice_minutes': 4},
                                    dp.estimate_speed(records, [], 'MATH1', policy), policy, 'repair')
        self.assertEqual(paper['planned_review_task_ids'], ['A:general'])
        self.assertEqual(paper['unplaced_due_question_ids'], [])
        self.assertEqual(state['review_tasks'], before)

    def test_real_page_fault_links_share_recovery_but_separate_replacement(self):
        records = dp.load_inputs(PROJECT)[0]
        data = la.load_map(PROJECT, records)
        self.assertEqual(la.primary(records['408-19-C-T14'], data), la.primary(records['408-21-C-T21'], data))
        self.assertNotEqual(la.primary(records['408-19-C-T14'], data), la.primary(records['408-22-C-T29'], data))
        self.assertFalse(data['questions']['408-13-C-T30']['score_supports_primary'])


if __name__ == '__main__':
    unittest.main()
