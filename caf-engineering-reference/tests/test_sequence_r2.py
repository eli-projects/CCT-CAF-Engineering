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

    def test_rebuild_from_last_open_baseline_changes_only_graphical_property(self):
        self.assertFalse(self.manifest['failed_caf_used_as_input'])
        self.assertEqual(self.manifest['build_origin']['sha256'], sha(self.baseline))
        self.assertEqual(sha(self.caf), '23ab292b4bcffabbc32ef7b4a6e5acc90e1dde039b85a15a0afebaa32873c5cd')
        delta = diff(ROOT/'experiments/failed/AHU-1_Integrated_Sequence_CCT_TEST.caf', self.caf)
        self.assertFalse(delta['added_objects'])
        self.assertFalse(delta['removed_objects'])
        self.assertFalse(delta['main_connection_changes'])
        self.assertEqual(len(delta['changed_objects']), 3)
        self.assertTrue(all(o['changed_property_ids'] == ['3383'] for o in delta['changed_objects']))

    def test_revised_categories_are_observed_in_native_sources(self):
        references = [CAF(p) for p in sorted((ROOT/'examples/modules').glob('*.caf'))]
        report = audit(CAF(self.caf), references+[CAF(self.baseline)])
        self.assertFalse(report['structural_issues'])
        self.assertFalse(report['unobserved_display_combinations'])
        self.assertFalse(report['classes_not_covered_by_references'])


if __name__ == '__main__':
    unittest.main()
