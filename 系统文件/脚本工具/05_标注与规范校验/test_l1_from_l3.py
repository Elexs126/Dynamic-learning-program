"""Current release integrity and mutation-sensitive regression tests."""
from collections import Counter
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
import build_l1_from_l3 as b

P = Path(os.environ.get('L1_FROM_L3_TEST_PROJECT', str(Path(__file__).resolve().parents[3])))


class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=P/b.RELEASE
        cls.l1={r['question_id']:r for r in b.read(cls.root/'L1'/b.L1_NAME)['records']}
        cls.l3={r['question_id']:r for key,_,_,_,name in b.COHORTS for r in b.read(cls.root/key/name)['records']}
        cls.report=b.read(cls.root/'release_report.json')

    def test_01_current_release_and_l3_replay(self):
        result=b.check(P,b.RELEASE)
        self.assertEqual(result['status'],'PASS',result)
        self.assertEqual((result['question_count'],result['core_count'],result['paper_count']),(8022,1277,37))

    def test_02_core_L1_main_matches_reviewed_L2(self):
        for q,r in self.l3.items():
            candidate=self.l1[q]['l1']['candidate_main_knowledge']
            self.assertEqual((candidate['id'],candidate['name']),(r['l2']['main_knowledge']['id'],r['l2']['main_knowledge']['name']))
            self.assertEqual(candidate['role'],'reviewed_l2_reference')

    def test_03_all_123_scope_decisions_resolved(self):
        decisions=b.read(self.root/'review_inputs/scope_resolutions_v1.json')['records']
        self.assertEqual(len(decisions),123)
        for d in decisions:
            r=self.l1[d['question_id']]
            self.assertEqual(r['l1']['review_status_by_field']['official_scope_coarse'],'verified')
            self.assertFalse(set(r['review_flags']) & {'SCOPE_UNMAPPED','SCOPE_AMBIGUOUS'})
        self.assertEqual(sum(len(d['scope_ids'])>1 for d in decisions),24)

    def test_04_noncore_unmapped_not_silently_certified(self):
        pending=[q for q,r in self.l1.items() if set(r['review_flags']) & {'SCOPE_UNMAPPED','SCOPE_AMBIGUOUS'}]
        self.assertEqual(len(pending),93);self.assertFalse(set(pending)&self.l3.keys())

    def test_05_duplicate_review_is_reciprocal_and_keeps_all_ids(self):
        groups=b.read(self.root/'L1/duplicate_review_v1.json')['groups']
        self.assertEqual((len(groups),sum(len(g['question_ids']) for g in groups)),(33,67))
        for g in groups:
            for q in g['question_ids']:
                d=self.l1[q]['l1']['duplicate_candidate']
                self.assertTrue(d['is_candidate']);self.assertEqual(d['status'],'verified')
                self.assertEqual(set(d['possible_duplicate_ids']),set(g['question_ids'])-{q})

    def test_06_no_fingerprint_match_does_not_mean_no_duplicate(self):
        r=next(r for r in self.l1.values() if not r['l1']['duplicate_candidate']['possible_duplicate_ids'])
        self.assertIsNone(r['l1']['duplicate_candidate']['is_candidate'])

    def test_07_isomorphic_records_not_converted_to_duplicates(self):
        for r in self.l3.values():
            iso=r['l3'].get('isomorphic_relation')
            if iso:self.assertFalse(set(iso['related_question_ids']) & set(r['l1']['duplicate_candidate']['possible_duplicate_ids']))

    def test_08_retired_fragment_mapping_has_one_existing_target(self):
        mapping=b.read(self.root/'retired_id_mapping.json')['merges']
        self.assertEqual(set(mapping),{'WD-OS-C-2.2-T00','WD-OS-C-2.2-T27'})
        self.assertFalse(set(mapping)&self.l1.keys())
        self.assertEqual(set(mapping.values()),{'WD-OS-C-2.2-T26'})
        self.assertIn('WD-OS-C-2.2-T26',self.l1)

    def test_09_short_statement_confirmation_only_closes_length_flag(self):
        ids=b.read(self.root/'review_inputs/user_confirmation_v1.json')['short_stem_confirmed_normal_ids']
        self.assertEqual(len(ids),11)
        for q in ids:
            self.assertNotIn('SHORT_OR_EMPTY_STEM',self.l1[q]['review_flags'])
            self.assertIn('SHORT_STEM_CONFIRMED_NORMAL_BY_USER',self.l1[q]['review_flags'])
            self.assertEqual(self.l1[q]['l0']['question_completeness'],'needs_review')

    def test_10_partial_scoring_keeps_whole_total_without_filling_difference(self):
        for q in ('408-12-A-T43','408-14-A-T47','408-26-A-T41','408-26-A-T44'):
            units=self.l3[q]['l3']['score_units']
            self.assertEqual(len(units),1)
            self.assertEqual(units[0]['points'],self.l3[q]['l0']['original_points'])
        self.assertEqual(len(self.report['partial_scoring_normalized']),4)

    def test_11_new_baseline_normalizes_old_alias(self):
        baseline=b.read(self.root/'canonical_sources_v2.json')
        self.assertEqual(baseline['expected_unique_question_records'],8022)
        wd=next(s for s in baseline['sources'] if s['source_id']=='WANGDAO_408')
        self.assertEqual(wd['expected_records'],2895)
        self.assertNotIn('expected_record_count',wd)

    def test_12_no_student_data_or_formal_E_created(self):
        self.assertFalse(self.report['formal_E_activated']);self.assertEqual(self.report['student_records_created'],0)

    def test_13_ambiguous_anchor_is_rejected(self):
        lines=['','match','','match',''];block={'question_id':'Q','line_start':1,'line_end':5}
        with self.assertRaisesRegex(ValueError,'Ambiguous'):
            b.reanchor({'line':1,'match':'match','occurrence':1},block,lines)

    def test_14_existing_valid_anchor_and_unique_relocation(self):
        lines=['','match','','match',''];block={'question_id':'Q','line_start':1,'line_end':5}
        a={'line':2,'match':'match','occurrence':1}
        self.assertEqual(b.reanchor(a,block,lines),a)
        lines[3]='';a['line']=1
        self.assertEqual(b.reanchor(a,block,lines)['line'],2)

    def test_15_source_or_result_tampering_rejected(self):
        for target in ('source','result'):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);release=root/'release';release.mkdir()
                (root/'source').write_text('changed' if target=='source' else 'source')
                (release/'result').write_text('changed' if target=='result' else 'result')
                import hashlib
                digest=lambda x:hashlib.sha256(x.encode()).hexdigest()
                b.write(release/'release_manifest.json',{'builder_sha256':b.sha(Path(b.__file__)),
                    'input_sha256':{'source':digest('source')},'output_sha256':{'result':digest('result')}})
                self.assertEqual(b.check(root,'release')['status'],'FAIL')


if __name__=='__main__':unittest.main()
