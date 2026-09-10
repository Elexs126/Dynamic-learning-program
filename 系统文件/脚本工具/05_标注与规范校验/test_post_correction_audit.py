import math
import os
from pathlib import Path
import unittest
import audit_after_source_corrections as a


def sample(points=13):
    return {'l0': {'original_points': points}, 'l3': {'evidence_steps': [
        {'steps': ['[Q#T01] first step', '[Q#T02] second step']}]}}


def partition(points=(4, 8), mode='whole'):
    return {'mode': mode, 'documented_units': [
        {'points': points[0], 'step_refs': ['1.1'], 'anchor': {'line': 1}},
        {'points': points[1], 'step_refs': ['2.1'], 'anchor': {'line': 2}}]}


class ScoringTests(unittest.TestCase):
    def test_total_claim_is_distinct_from_subquestion_points(self):
        c = a.declared_totals('（本题满分 15 分）\n（1）操作（2 分）', 10)
        self.assertEqual([x['points'] for x in c], [15])
        self.assertEqual(len(a.total_conflicts(13, c)), 1)

    def test_matching_declared_total_is_not_flagged(self):
        self.assertEqual(a.total_conflicts(15, a.declared_totals('本题满分15分', 10)), [])

    def test_whole_mode_does_not_erase_full_partition_conflict(self):
        x = a.covering_partition_conflict(sample(), partition())
        self.assertEqual(x['documented_points_sum'], 12)
        self.assertEqual(x['metadata_points'], 13)

    def test_incomplete_scoring_does_not_imply_conflicting_total(self):
        p = partition(); p['documented_units'].pop()
        self.assertIsNone(a.covering_partition_conflict(sample(), p))

    def test_matching_partition_is_not_flagged(self):
        self.assertIsNone(a.covering_partition_conflict(sample(12), partition()))

    def test_duplicate_ids_are_rejected(self):
        with self.assertRaises(ValueError): a.keyset([{'question_id': 'Q'}, {'question_id': 'Q'}])

    def test_two_revised_coordinate_options_agree_for_two_integrands(self):
        # Numerical cross-check of the reviewed coordinate-domain proof, never
        # used to invent a replacement option or change a source answer.
        def simpson(f, lo, hi, n=2000):
            h = (hi - lo) / n
            return h / 3 * (f(lo) + f(hi) + sum((4 if i % 2 else 2) * f(lo + i*h) for i in range(1, n)))
        root2 = math.sqrt(2)
        cylinder_constant = 2*math.pi*simpson(lambda r: r*(math.sqrt(4-r*r)-r), 0, root2)
        sphere_constant = 2*math.pi*(1-math.cos(math.pi/4))*8/3
        cylinder_radial_square = 2*math.pi*simpson(
            lambda r: r*(r*r*(math.sqrt(4-r*r)-r) + ((4-r*r)**1.5-r**3)/3), 0, root2)
        sphere_radial_square = 2*math.pi*(1-math.cos(math.pi/4))*32/5
        self.assertAlmostEqual(cylinder_constant, sphere_constant, places=8)
        self.assertAlmostEqual(cylinder_radial_square, sphere_radial_square, places=8)


class CurrentRepositoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p = Path(os.environ.get('POST_CORRECTION_PROJECT', '/home/elexs/Dynamic-learning-program'))
        cls.report = a.audit(p, run_checks=False)

    def test_current_source_count_and_merged_fragment_ids(self):
        self.assertEqual(self.report['counts']['actual_canonical'], 8022)
        self.assertEqual(self.report['missing_ids_from_current_sources'], [])
        self.assertEqual(set(self.report['retired_id_mapping']['merges']), {'WD-OS-C-2.2-T00', 'WD-OS-C-2.2-T27'})
        self.assertEqual(self.report['counts']['ocr_suspicious_characters_remaining'], 0)

    def test_current_source_conflicts_survive_empty_omission_lists(self):
        self.assertTrue(all(c['stored_field_omission_question_count'] == 0 for c in self.report['cohorts']))
        self.assertEqual(self.report['counts']['score_conflict_questions'], 0)
        self.assertEqual(self.report['counts']['semantic_choice_issues'], 0)
        self.assertTrue(self.report['dependent_l1_execution_allowed'])
        self.assertEqual(self.report['status'], 'PASS')

    def test_whole_paper_score_check_and_candidate_scope_are_separate(self):
        self.assertEqual(self.report['counts']['paper_total_mismatches'], 0)
        self.assertEqual(self.report['counts']['core_course_only_routes_by_track'], {})
        self.assertTrue(self.report['dependent_l1_executed'])


if __name__ == '__main__': unittest.main()
