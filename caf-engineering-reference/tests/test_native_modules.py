"""Protect native evidence and retain the user-reported rendering regression."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from caf_module_catalog import CAF, audit, digest, module_detail, prop, scalar


class NativeModuleEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT/'data/module-library-manifest.json').read_text())
        cls.sources = [CAF(ROOT/row['path']) for row in cls.manifest['files']]
        cls.by_name = {caf.path.name: caf for caf in cls.sources}

    def test_native_sources_match_recorded_hashes_and_counts(self):
        total = 0
        for caf, expected in zip(self.sources, self.manifest['files']):
            with self.subTest(caf.path.name):
                self.assertEqual(digest(caf.bytes), expected['sha256'])
                self.assertEqual(len(caf.objects), expected['objects'])
                self.assertFalse([g for g in caf.graphs if g['issues']])
                main = next(g for g in caf.graphs if g['scope'] == 'main')
                self.assertEqual(main['wire_count'], 0)
                total += main['block_count']
        self.assertEqual(total, 520)

    def test_failed_caf_has_known_rendering_discrepancies(self):
        failed = CAF(ROOT/'experiments/failed/AHU-1_Integrated_Sequence_CCT_TEST.caf')
        baseline = CAF(ROOT/'examples/ahu-1/AHU-1_latest_AvgControlRedirect_VERIFIED-OPEN.caf')
        result = audit(failed, self.sources+[baseline])
        self.assertEqual(result['sha256'], '5180b9ea0fe254d844f5385882c547afc74f165fc898f022750dd38957708a88')
        self.assertEqual(len(result['unobserved_display_combinations']), 187)
        nested = [d for d in result['unobserved_display_combinations'] if d['scope'] == 'nested']
        self.assertEqual(len(nested), 166)
        self.assertTrue(all(d['display_code'] == 10 for d in nested))
        self.assertEqual({d['class_id'] for d in nested}, {539, 558, 559, 560, 561})

    def test_same_ref_in_different_files_is_not_same_module(self):
        ref = '8-1/575_1.536_10004'
        names = {scalar(c.by[ref], 2390) for c in self.sources}
        self.assertEqual(len(names), 4)

    def test_native_missing_wire_arrays_are_preserved_as_observations(self):
        omitted = [g for c in self.sources for g in c.graphs if g['connection_arrays'] == 'both omitted']
        self.assertEqual(len(omitted), 3)
        self.assertTrue(all(g['block_count'] == 1 and not g['issues'] for g in omitted))

    def test_two_and_three_input_averages_keep_their_actual_port_order(self):
        misc = self.by_name['Setpoint-Misc_Modules.caf']
        two = misc.by['8-1/575_1.536_10384']
        three = CAF(ROOT/'examples/ahu-1/AHU-1_CCT_AVG_3Inputs.caf').by['8-1/575_1.536_86471']
        self.assertEqual([int(v.text) for v in prop(two, 3184)], [7000, 7001, 8000])
        self.assertEqual([int(v.text) for v in prop(three, 3184)], [7000, 7001, 8000, 7002])
        detail = module_detail(misc, two.get('ref'))
        self.assertEqual(detail['object_count'], 8)
        self.assertEqual(detail['graphs'][0]['wire_count'], 3)

    def test_native_co2_setting_is_recorded_not_replaced_by_help_default(self):
        misc = self.by_name['Setpoint-Misc_Modules.caf']
        root = '8-1/575_1.536_10107'
        high = [o for o in misc.children[root] if scalar(o, 3365) == '7004']
        self.assertEqual(len(high), 1)
        self.assertEqual(scalar(high[0], 3113), '90')


if __name__ == '__main__':
    unittest.main()
