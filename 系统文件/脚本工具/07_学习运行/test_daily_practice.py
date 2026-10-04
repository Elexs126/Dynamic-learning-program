"""Daily recommendation behaviors; artificial attempts stay in temporary dirs."""
import copy
from datetime import date
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import daily_practice as dp

PROJECT = Path(os.environ.get('LEARNING_RUNTIME_TEST_PROJECT', str(Path(__file__).resolve().parents[3])))
DAY = date(2026, 10, 4)


def question(qid, kind='choice', kid='K1', area='calculus', track='MATH1', chapter=None):
    return {'question_id': qid, 'l0': {'exam_track': track, 'subject_area': area,
            'paper_id': 'P-' + track, 'question_type': kind, 'original_points': 5 if kind != 'analytical' else 10,
            'source_file': '核心真题/' + qid + '.md', 'source_locator': qid,
            'question_hash_sha256': dp.digest(qid)},
            'l1': {'official_scope_coarse': chapter or '数学一 > 高等数学 > 函数、极限与连续'},
            'l2': {'main_knowledge': {'id': kid, 'name': kid},
                   'prerequisites': {'hard_prerequisite': [], 'soft_prerequisite': []},
                   'difficulty_band': 'basic', 'review_status_by_field': {'main_knowledge': 'verified'}}, 'l3': None}


def attempt(qid, **changes):
    r = {'schema_version': 'attempt-record-v1.0.0', 'attempt_id': 'A-' + qid,
         'attempted_at': '2026-10-04T09:00:00+08:00', 'verified_at': '2026-10-04T10:00:00+08:00',
         'question_id': qid, 'paper_id': 'P-MATH1', 'exam_track': 'MATH1', 'usage_role': 'TRAIN',
         'attempt_kind': 'near_variant', 'target_ability_id': 'K1', 'batch_id': None,
         'first_score_pct': 90, 'duration_seconds': 300, 'highest_hint_level_used': 'L0',
         'is_unseen': True, 'is_timed': True, 'is_mixed': False, 'interval_hours': None,
         'primary_error_code': None, 'dimensions': {k: None for k in dp.lr.DIMENSIONS},
         'next_review_at': '2026-10-07T09:00:00+08:00',
         'student_verification': {'mode': 'external_authoritative_self_check', 'score_confirmed_by_student': True,
                                  'answer_checked_after_first_pass': True, 'teacher_answer_access': False}, 'notes': ''}
    r.update(changes)
    return r


class RecommendationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = dp.lr.read(PROJECT / dp.CONFIG)
        cls.contract = dp.lr.read(PROJECT / '系统文件/系统配置/execution_contract_v1.json')
        cls.records, cls.rows, cls.summaries, cls.nav, cls.selector = dp.load_inputs(PROJECT)

    def test_integer_apportionment_tracks_blueprints(self):
        for track in dp.TRACKS:
            base = self.policy['blueprints'][track]['counts']
            for n in range(self.policy['minimum_questions'][track], sum(base.values()) + 1):
                counts = dp.proportional_counts(n, base)
                self.assertEqual(sum(counts.values()), n)
                for k in base:
                    self.assertLess(abs(counts[k] - n * base[k] / sum(base.values())), 1)
        self.assertEqual(dp.proportional_counts(22, {'choice': 10, 'fill': 6, 'analytical': 6}), {'choice': 10, 'fill': 6, 'analytical': 6})

    def test_daily_budget_reserves_teaching_and_tracks_weekday(self):
        b = dp.time_budgets(self.contract, self.policy, {}, date(2026, 10, 5))
        self.assertEqual(b['MATH1']['practice_minutes'], 120)
        self.assertEqual(sum(x['net_minutes'] for x in b.values()), 480)
        b = dp.time_budgets(self.contract, self.policy, {}, date(2026, 10, 6))
        self.assertEqual(b['CS408']['practice_minutes'], 90)

    def test_weekly_allocation_respects_contract_floors_and_week(self):
        teacher = {'weekly_allocation': {'MATH1': 15, 'CS408': 35}, 'effective_week_start': '2026-10-05'}
        b = dp.time_budgets(self.contract, self.policy, teacher, date(2026, 10, 5))
        self.assertEqual(b['MATH1']['net_minutes'], 144)
        for changes in [{'effective_week_start': '2026-09-28'}, {'weekly_allocation': {'MATH1': 10, 'CS408': 40}},
                        {'weekly_allocation': {'MATH1': 30, 'CS408': 25}}]:
            with self.assertRaises(ValueError):
                dp.time_budgets(self.contract, self.policy, dict(teacher, **changes), date(2026, 10, 5))

    def test_practice_override_cannot_exceed_subject_budget(self):
        teacher = {'subjects': {'MATH1': {'practice_minutes': 241}}}
        with self.assertRaises(ValueError):
            dp.time_budgets(self.contract, self.policy, teacher, date(2026, 10, 5))

    def test_personal_speed_requires_three_comparable_first_passes(self):
        records = {qid: question(qid) for qid in ('Q1', 'Q2', 'Q3', 'Q4')}
        rows = [attempt('Q1', duration_seconds=600), attempt('Q2', duration_seconds=1200)]
        self.assertEqual(dp.estimate_speed(records, rows, 'MATH1', self.policy)['choice']['basis'], 'cold_start_estimate')
        rows += [attempt('Q3', duration_seconds=900), attempt('Q4', duration_seconds=60, highest_hint_level_used='L2')]
        self.assertEqual(dp.estimate_speed(records, rows, 'MATH1', self.policy)['choice']['minutes'], 15)

    def test_unknown_dimensions_and_empty_logs_remain_unknown(self):
        st, usable = dp.derive_state({'Q1': question('Q1')}, [], [], DAY, 80)
        self.assertEqual(st['abilities'], {})
        self.assertIsNone(st['unobserved_ability_status'])
        st, _ = dp.derive_state({'Q1': question('Q1')}, [attempt('Q1')], [], DAY, 80)
        self.assertTrue(all(v is None for v in st['abilities']['K1']['dimensions'].values()))
        self.assertIsNone(st['E_metrics'])

    def test_future_and_not_yet_verified_attempts_not_used(self):
        records = {'Q1': question('Q1'), 'Q2': question('Q2')}
        rows = [attempt('Q1', attempted_at='2026-10-05T08:00:00+08:00', verified_at='2026-10-05T09:00:00+08:00'),
                attempt('Q2', verified_at='2026-10-05T01:00:00+08:00')]
        self.assertEqual(dp.derive_state(records, rows, [], DAY, 80)[0]['attempt_count'], 0)

    def test_two_distinct_variants_only_working_mastery_not_certification(self):
        records = {qid: question(qid) for qid in ('Q1', 'Q2')}
        st, _ = dp.derive_state(records, [attempt('Q1'), attempt('Q2')], [], DAY, 80)
        self.assertEqual(st['abilities']['K1']['stage'], '工作掌握')
        self.assertEqual(st['abilities']['K1']['independent_certification'], 'unverified')
        st, _ = dp.derive_state(records, [attempt('Q1'), attempt('Q2', highest_hint_level_used='L2')], [], DAY, 80)
        self.assertEqual(st['abilities']['K1']['stage'], '已接触')

    def test_primary_knowledge_only_updated_by_integrated_question(self):
        q = question('Q1')
        q['l2']['secondary_knowledge'] = [{'id': 'K2', 'name': 'secondary'}]
        st, _ = dp.derive_state({'Q1': q}, [attempt('Q1', first_score_pct=30)], [], DAY, 80)
        self.assertEqual(set(st['abilities']), {'K1'})
        self.assertTrue(st['abilities']['K1']['weak'])

    def test_two_coarse_scope_questions_do_not_certify_fine_ability(self):
        records = {qid: question(qid) for qid in ('Q1', 'Q2')}
        for q in records.values():
            q['l2'] = None
        st, _ = dp.derive_state(records, [attempt('Q1'), attempt('Q2')], [], DAY, 80)
        self.assertEqual(next(iter(st['abilities'].values()))['stage'], '已接触')

    def candidates(self, records, rows=None, teacher=None):
        st, usable = dp.derive_state(records, rows or [], [], DAY, 80)
        return dp.prepare_candidates(PROJECT, records, st, usable, self.nav, 'MATH1', teacher or {})[0]

    def test_due_question_prioritized_and_seen_not_reissued_otherwise(self):
        records = {qid: question(qid) for qid in ('Q1', 'Q2')}
        row = attempt('Q1', next_review_at='2026-10-05T09:00:00+08:00')
        cs = self.candidates(records, [row])
        self.assertEqual(cs[0]['question_id'], 'Q1')
        self.assertEqual(cs[0]['reason'], '到期复习')
        self.assertNotIn('Q1', {c['question_id'] for c in self.candidates(records, [attempt('Q1')])})

    def test_teacher_priorities_select_matching_knowledge(self):
        records = {'Q1': question('Q1'), 'Q2': question('Q2', kid='K2')}
        teacher = {'subjects': {'MATH1': {'priority_knowledge_ids': ['K2']}}}
        self.assertEqual(self.candidates(records, teacher=teacher)[0]['question_id'], 'Q2')

    def test_known_insufficient_hard_prerequisite_blocks_new_work(self):
        records = {'Q1': question('Q1'), 'Q2': question('Q2', kid='K2')}
        records['Q2']['l2']['prerequisites']['hard_prerequisite'] = [{'id': 'K1', 'name': 'prior'}]
        self.assertNotIn('Q2', {c['question_id'] for c in self.candidates(records, [attempt('Q1', first_score_pct=20)])})
        cs = self.candidates(records)
        self.assertTrue(next(c for c in cs if c['question_id'] == 'Q2')['preparation'])

    def test_hidden_role_and_duplicate_fingerprint_excluded(self):
        records = {'Q1': question('Q1'), 'Q2': question('Q2')}
        records['Q2']['l0']['question_hash_sha256'] = records['Q1']['l0']['question_hash_sha256']
        self.assertEqual(self.candidates(records, [attempt('Q1', usage_role='SEALED', batch_id='B1')]), [])

    def test_scope_order_prefers_exact_long_name_over_short_substring(self):
        q = question('Q1', area='linear_algebra', chapter='数学一 > 线性代数 > 矩阵的特征值和特征向量')
        order = dp.scope_order(self.nav, {'Q1': q})
        self.assertGreater(order[dp.scope(q)], 1)

    def test_one_attempt_does_not_advance_whole_course_chapter(self):
        records = {'Q1': question('Q1'), 'Q2': question('Q2', kid='K2', chapter='数学一 > 高等数学 > 一元函数微分学')}
        self.assertNotIn('Q2', {c['question_id'] for c in self.candidates(records, [attempt('Q1')])})

    def test_live_log_changes_allowed_but_annotation_drift_rejected(self):
        report = {'errors': ['source_changed: ' + dp.lr.ATTEMPTS, 'source_changed: ' + dp.lr.OFFLINE_LOG]}
        with patch.object(dp.lr, 'check_build', return_value=report):
            dp.load_inputs(PROJECT)
        with patch.object(dp.lr, 'check_build', return_value={'errors': ['source_changed: question_annotations.json']}):
            with self.assertRaises(ValueError):
                dp.load_inputs(PROJECT)

    def test_teacher_plan_rejects_unknown_and_cross_subject_keys(self):
        records = {'Q1': question('Q1'), 'Q2': question('Q2', kid='K2', track='CS408', area='data_structure')}
        for subjects in [{'MATH1': {'priority_knowledge_ids': ['missing']}}, {'MATH1': {'priority_knowledge_ids': ['K2']}},
                         {'MATH1': {'made_up_score_gain': 0.5}}]:
            with self.assertRaises(ValueError):
                dp.validate_teacher_plan({'version': 'daily-teacher-plan-v1', 'subjects': subjects}, records)

    def test_real_catalog_papers_fit_budget_and_use_all_types(self):
        day, _, _ = dp.build_day(PROJECT, DAY)
        for track, paper in day['papers'].items():
            self.assertEqual(paper['status'], 'ready')
            self.assertLessEqual(paper['estimated_minutes'], paper['budget']['practice_minutes'])
            self.assertTrue(all(paper['counts'].values()))
            self.assertEqual(len({q['question_id'] for q in paper['questions']}), len(paper['questions']))
            for q in paper['questions']:
                self.assertNotIn('参考答案', q['body_html'])
                self.assertNotIn('正确答案', q['body_html'])
                self.assertEqual(self.records[q['question_id']]['l0']['exam_track'], track)
                points = self.records[q['question_id']]['l0']['original_points']
                if points is not None:
                    self.assertEqual(q['points'], points)


class RenderingAndLogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.q = question('Q1')
        self.source = self.root / self.q['l0']['source_file']
        self.source.parent.mkdir(parents=True)
        self.source.write_text('### 【Q1】第1题\n\n设 $x^2=1$，选择。\n\n- **A.** 1\n- **B.** 2\n- **C.** 3\n- **D.** 4\n\n> **【唯一编号】** `Q1`\n<details>参考答案SECRET</details>\n### 【Q2】第2题\nNEXT', encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def test_body_excludes_answers_metadata_and_next_question(self):
        body, _ = dp.question_body(self.root, self.q)
        for term in ('SECRET', '唯一编号', 'NEXT', 'details'):
            self.assertNotIn(term, body)

    def test_duplicate_options_and_flattened_math_rejected(self):
        original = self.source.read_text()
        self.source.write_text(original.replace('**D.** 4', '**D.** 1'))
        with self.assertRaises(ValueError):
            dp.question_body(self.root, self.q)
        self.source.write_text(original.replace('$x^2=1$', '$∫0xf(x)dx$'))
        with self.assertRaises(ValueError):
            dp.question_body(self.root, self.q)

    def test_next_chapter_tail_not_included_as_question_figure(self):
        text = self.source.read_text().replace('> **【唯一编号】**', '第2 章\n物理层\n\n> **【唯一编号】**')
        self.source.write_text(text)
        with self.assertRaises(ValueError):
            dp.question_body(self.root, self.q)

    def test_tex_preserved_br_code_and_multiline_options_rendered(self):
        rendered = dp.render_markdown('$x_{1}$<br>二行\n\n- **A.** $x$\n  \n- **B.** $y$\n\n```c\nif(x<2) {}\n```', self.source, self.root)
        self.assertIn('$x_{1}$', rendered)
        self.assertNotIn('&lt;br', rendered)
        self.assertIn('<strong>A.</strong>', rendered)
        self.assertIn('x&lt;2', rendered)

    def test_double_escaped_commands_normalized_but_matrix_rows_preserved(self):
        text = r'$f(x)=\\begin{cases}\\frac{1}{x}, & x>0 \\ b, & x\\le0 \\end{cases}$'
        rendered = dp.render_markdown(text, self.source, self.root)
        self.assertIn(r'\begin{cases}', rendered)
        self.assertNotIn(r'\\begin{cases}', rendered)
        self.assertIn(r'\\ b', rendered)

    def test_plain_option_lines_render_separately(self):
        rendered = dp.render_markdown('A. $x$\nB. $y$\nC. $z$\nD. $w$', self.source, self.root)
        self.assertEqual(rendered.count('<li>'), 4)

    def test_images_embedded_and_missing_or_escape_rejected(self):
        (self.source.parent / 'image.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
        rendered = dp.render_markdown('![figure](image.svg)', self.source, self.root)
        self.assertIn('data:image/svg+xml;base64,', rendered)
        for path in ('missing.svg', '../../../etc/passwd'):
            with self.assertRaises(ValueError):
                dp.render_markdown(f'![]( {path})', self.source, self.root)

    def test_log_schema_chronology_and_score_validation(self):
        record = attempt('Q1')
        dp.validate_attempts(PROJECT, [record], {'Q1': self.q})
        for change in [{'first_score_pct': 101}, {'verified_at': '2026-10-03T08:00:00+08:00'},
                       {'attempted_at': '2026-10-04T08:00:00'}, {'exam_track': 'CS408'}, {'question_id': 'missing'}]:
            with self.assertRaises(ValueError):
                dp.validate_attempts(PROJECT, [dict(record, **change)], {'Q1': self.q})

    def test_log_repeat_cannot_claim_unseen(self):
        a, b = attempt('Q1'), attempt('Q1', attempt_id='other')
        with self.assertRaises(ValueError):
            dp.validate_attempts(PROJECT, [a, b], {'Q1': self.q})

    def test_insufficient_pool_does_not_emit_wrong_proportions(self):
        policy = dp.lr.read(PROJECT / dp.CONFIG)
        speed = dp.estimate_speed({'Q1': self.q}, [], 'MATH1', policy)
        candidate = {'question_id': 'Q1', 'q': self.q, 'knowledge_id': 'K1', 'reason': '学习前沿', 'rank': (1,)}
        p = dp.select_paper(self.root, [candidate], {'Q1'}, {}, 'MATH1', {'practice_minutes': 120}, speed, policy)
        self.assertEqual(p['questions'], [])
        self.assertEqual(p['unplaced_due_question_ids'], ['Q1'])

    def test_frozen_file_tampering_detected(self):
        directory = self.root / 'frozen'
        directory.mkdir()
        (directory / 'paper.html').write_text('original')
        (directory / 'manifest.json').write_text(dp.lr.dump({'output_sha256': {'paper.html': dp.lr.sha(directory / 'paper.html')}}))
        dp.verify_frozen(directory)
        (directory / 'paper.html').write_text('changed')
        with self.assertRaises(ValueError):
            dp.verify_frozen(directory)

    def test_daily_close_appends_once_and_reuses_frozen_paper(self):
        # Build a miniature project using real schemas and policy, never its log.
        for rel in [dp.CONFIG, '系统文件/系统配置/execution_contract_v1.json',
                    '系统文件/数据规范/attempt_record.schema.json', dp.lr.OFFLINE_SCHEMA,
                    '系统文件/脚本工具/05_标注与规范校验/json_schema_runtime.py',
                    '系统文件/脚本工具/05_标注与规范校验/validate_attempt_log.py']:
            target = self.root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PROJECT / rel, target)
        log = self.root / dp.lr.ATTEMPTS
        log.parent.mkdir(parents=True)
        log.write_text('')
        records = {'Q1': self.q}
        def fake_inputs(project):
            return records, dp.lr.jsonl(log.read_text()), [], {'courses': []}, {'runtime_snapshot': 'fixture'}
        with patch.object(dp, 'load_inputs', side_effect=fake_inputs):
            r = dp.generate(self.root, DAY, self.root / 'daily', feedback=[attempt('Q1')])
            self.assertEqual(r['appended_attempts'], 1)
            r = dp.generate(self.root, DAY, self.root / 'daily', feedback=[attempt('Q1')])
            self.assertEqual(r['status'], 'REUSED_FROZEN')
            self.assertEqual(len(dp.lr.jsonl(log.read_text())), 1)
            with self.assertRaises(ValueError):
                dp.generate(self.root, DAY, self.root / 'daily', feedback=[attempt('Q1', first_score_pct=20)])
            with self.assertRaises(ValueError):
                dp.generate(self.root, DAY, self.root / 'daily', feedback=[attempt('Q1', attempt_id='new', is_unseen=False)])
            with self.assertRaises(ValueError):
                dp.generate(self.root, date(2026, 10, 5), self.root / 'daily')

    def test_render_failure_leaves_log_untouched(self):
        log = self.root / dp.lr.ATTEMPTS
        log.parent.mkdir(parents=True)
        log.write_text('')
        fake_day = {'target_date': '2026-10-05'}
        with patch.object(dp, 'build_day', return_value=(fake_day, [attempt('Q1')], [attempt('Q1')])), \
                patch.object(dp, 'write_artifacts', side_effect=ValueError('render failed')):
            with self.assertRaises(ValueError):
                dp.generate(self.root, DAY, self.root / 'daily', feedback=[attempt('Q1')])
        self.assertEqual(log.read_text(), '')
        self.assertFalse((self.root / 'daily').exists())


if __name__ == '__main__':
    unittest.main()
