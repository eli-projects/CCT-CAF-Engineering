"""Static regression tests, not a substitute for opening and simulating in CCT."""
import json, hashlib, sys, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE/'scripts'))
from caf_inspect import inspect_file
from caf_diff import diff

class CAFReferenceTests(unittest.TestCase):
    def test_all_examples_integrity_and_manifest(self):
        manifest=json.loads((HERE/'data'/'example-manifest.json').read_text())
        for record in manifest['examples']:
            with self.subTest(record['path']):
                p=HERE/record['path']
                result=inspect_file(p)
                self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), record['sha256'])
                self.assertEqual(result['object_count'], record['xml_object_count'])
                self.assertTrue(result['block_array_lengths_consistent'])
                self.assertTrue(result['edge_meta_lengths_consistent'])
                self.assertTrue(all(c['src']<result['main_blocks'] and c['dst']<result['main_blocks'] for c in result['connections']))
    def test_control_redirect_only_six_wires(self):
        a=HERE/'examples/ahu-1/AHU-1_3Averages_VERIFIED.caf'
        b=HERE/'examples/ahu-1/AHU-1_latest_AvgControlRedirect_VERIFIED-OPEN.caf'
        d=diff(a,b)
        self.assertEqual(d['added_objects'],[])
        self.assertEqual(d['removed_objects'],[])
        self.assertEqual(d['changed_objects'],[{'ref':'8-1/575_1','changed_property_ids':['3118']}])
        self.assertEqual([x['idx'] for x in d['main_connection_changes']], [108,109,110,111,112,114])

if __name__=='__main__':unittest.main()
