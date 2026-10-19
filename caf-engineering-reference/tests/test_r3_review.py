"""Protect the reviewed correction and its evidence boundaries.

These tests run a limited independent model, never native CCT or equipment.
"""
import contextlib
import hashlib
import io
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT/'experiments/review/2026-10-19'
sys.path.insert(0, str(ROOT/'scripts/research'))
from verify_custom_graph import N, Runtime, p, validate


def load(path):
    with ZipFile(path) as z:
        assert z.testzip() is None
        root = E.fromstring(z.read(z.namelist()[0]))
        return {o.get('ref'): o for o in root.findall(N+'object')}


class R3ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.status = json.loads((ROOT/'data/sequence-r3-review-status.json').read_text())
        cls.edited = SAMPLES/'AHU-1_Sequence_R3_CCT_TEST_Edited.caf'
        cls.corrected = SAMPLES/'AHU-1_R3_MUX_Correction_CCT_TEST.caf'
        cls.before, cls.after = load(cls.edited), load(cls.corrected)

    def test_specimen_hashes_and_exact_72_property_delta(self):
        for row in self.status['files']:
            path = ROOT/row['path']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row['sha256'])
            self.assertEqual(len(load(path)), 3411)
        self.assertEqual(set(self.before), set(self.after))
        changed = {}
        for ref, a in self.before.items():
            b = self.after[ref]
            self.assertEqual(dict(a.attrib), dict(b.attrib))
            if E.tostring(a) == E.tostring(b):
                continue
            def fields(o):
                return {(c.tag, c.get('id')): E.tostring(c) for c in o}
            aa, bb = fields(a), fields(b)
            self.assertEqual(set(aa), set(bb))
            delta = {k for k in aa if aa[k] != bb[k]}
            self.assertEqual(delta, {(N+'property','2381'),(N+'property','3122')})
            self.assertEqual(a.get('classid'), '562')
            self.assertEqual([int(v.text) for v in p(b,2381)], [1,2])
            self.assertEqual(p(b,3122).text, '0')
            changed[ref] = delta
        self.assertEqual(len(changed),36)
        self.assertEqual(sum(len(v) for v in changed.values()),72)

    def test_repair_reproduces_candidate_and_rejects_wrong_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)/'correction.caf'
            cmd = [sys.executable,str(ROOT/'scripts/research/repair_reviewed_mux_maps.py')]
            result = subprocess.run(cmd+[str(self.edited),str(dest)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(dest.read_bytes(),self.corrected.read_bytes())
            original = SAMPLES/'AHU-1_Sequence_R3_CCT_TEST.caf'
            bad = subprocess.run(cmd+[str(original),str(Path(tmp)/'wrong.caf')],capture_output=True,text=True)
            self.assertNotEqual(bad.returncode,0)
            self.assertFalse((Path(tmp)/'wrong.caf').exists())

    def test_all_eight_zone_request_cases_expose_and_correct_inversion(self):
        ref = '8-1/575_1.536_400008'
        for bits in itertools.product((0,1), repeat=3):
            with self.subTest(bits=bits):
                inputs = dict(zip((7000,7001,7002),bits))
                old = Runtime(self.before,ref).step(0,inputs)[8000]
                new = Runtime(self.after,ref).step(0,inputs)[8000]
                self.assertTrue(old.reliable)
                self.assertTrue(new.reliable)
                self.assertEqual(int(new.value),int(any(bits)))
                self.assertEqual(int(old.value),int(not any(bits)))

    def test_native_two_input_mux_uses_one_based_data_input_numbers(self):
        matches = [o for ref,o in self.before.items() if ref.endswith('.562_265243')]
        self.assertEqual(len(matches),1)
        mux = matches[0]
        self.assertEqual([int(v.text) for v in p(mux,2381)],[1,2])
        self.assertEqual(p(mux,3122).text,'0')
        ports = [int(p(o,3365).text) for ref,o in self.before.items()
                 if ref.rsplit('.',1)[0] == mux.get('ref') and p(o,3365) is not None]
        self.assertEqual(sorted(n for n in ports if 7000 <= n < 8000),[7000,7001])

    def test_corrected_independent_model_checks_28_groups(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp)/'model.json'
            with contextlib.redirect_stdout(io.StringIO()):
                validate(self.corrected,ROOT/'data/r3-review/corrected-model-manifest.json',report)
            result = json.loads(report.read_text())
            self.assertEqual(result['scenario_groups'],28)
            self.assertEqual(result['caf_sha256'],self.status['files'][2]['sha256'])
            self.assertIn('CCT NOT EXECUTED',result['status'])


if __name__ == '__main__':
    unittest.main()
