"""R2 repairs rendering metadata without changing R1's intended logic.

These regression checks do not certify CCT opening or AHU runtime behavior.
"""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
sys.path.insert(0, str(ROOT/'scripts/research'))
from caf_diff import diff
from caf_module_catalog import CAF, audit
from build_ahu1_sequence_r2 import build, sha


class SequenceR2GraphicalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.baseline = ROOT/'examples/ahu-1/AHU-1_latest_AvgControlRedirect_VERIFIED-OPEN.caf'
        with contextlib.redirect_stdout(io.StringIO()):
            cls.caf, manifest = build(cls.baseline, Path(cls.temp.name))
        cls.manifest = json.loads(manifest.read_text())

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_rebuild_from_last_open_baseline_changes_tool_metadata_not_sequence(self):
        self.assertFalse(self.manifest['failed_caf_used_as_input'])
        self.assertEqual(self.manifest['build_origin']['sha256'], sha(self.baseline))
        self.assertEqual(sha(self.caf), '04463326b0822eeedc3cfdd3caa548bef78ca1144886010825d71c0950ff3bde')
        delta = diff(ROOT/'experiments/failed/AHU-1_Integrated_Sequence_CCT_TEST.caf', self.caf)
        self.assertFalse(delta['added_objects'])
        self.assertFalse(delta['removed_objects'])
        self.assertFalse(delta['main_connection_changes'])
        self.assertEqual(len(delta['changed_objects']), 3)
        changes = {o['ref']: o['changed_property_ids'] for o in delta['changed_objects']}
        self.assertEqual(changes['8-1/575_1'], ['3383', '3926'])
        self.assertTrue(all(ids == ['3383'] for ref, ids in changes.items() if ref != '8-1/575_1'))

    def test_revised_categories_are_observed_in_native_sources(self):
        references = [CAF(p) for p in sorted((ROOT/'examples/modules').glob('*.caf'))]
        report = audit(CAF(self.caf), references+[CAF(self.baseline)])
        self.assertFalse(report['structural_issues'])
        self.assertFalse(report['unobserved_display_combinations'])
        self.assertFalse(report['classes_not_covered_by_references'])
        self.assertFalse(report['hardware_registry_issues'])
        from caf_module_catalog import prop
        current = CAF(self.caf)
        self.assertEqual(len(prop(current.main, 3926)), 69)
        self.assertEqual(len(prop(current.main, 3927)), 69)
        original = CAF(self.baseline)
        pairs = {(r.get('id'), r.text): g.text for g, r in zip(prop(original.main, 3926), prop(original.main, 3927))}
        for g, r in zip(prop(current.main, 3926), prop(current.main, 3927)):
            key = (r.get('id'), r.text)
            source = ('556', '300143') if key in [('556', '400000'), ('556', '400004')] else key
            self.assertEqual(g.text, pairs[source])


if __name__ == '__main__':
    unittest.main()
