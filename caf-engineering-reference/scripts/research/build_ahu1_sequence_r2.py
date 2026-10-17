#!/usr/bin/env python3
"""Rebuild AHU-1 R2 from the last user-reported CCT-open baseline.

The failed integrated CAF is never used as build input. Intermediate sensor
cleanup and request-combination stages remain unverified by CCT. R2 changes
the graphical metadata construction; the intended sequence is unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path

import make_ahu_sensor_cleanup_candidate as cleanup
import make_ahu_three_tocc_candidate_r2 as requests
import build_ahu_sequence_r2 as sequence

BASE_SHA = '078e1aa20f084e82212f205480f858bb17fad45a81081a74f74e4d429530bd26'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(baseline, destination):
    assert sha(baseline) == BASE_SHA, 'Use the exact last user-reported CCT-open baseline'
    destination.mkdir(parents=True, exist_ok=True)
    stages = destination/'stages'
    stages.mkdir(exist_ok=True)
    clean = stages/'AHU-1_Sensors_R2.caf'
    three = stages/'AHU-1_Three_Requests_R2.caf'
    final = destination/'AHU-1_Sequence_R2_CCT_TEST.caf'
    manifest = destination/'AHU-1_Sequence_R2_Manifest.json'
    cleanup.run(baseline, clean, stages/'sensor-cleanup.json')
    stage_report = json.loads((stages/'sensor-cleanup.json').read_text())
    stage_report['limitations'] = ['CCT acceptance unverified; no CCT runtime here',
                                   'Sensor cleanup is one stage; the final build applies the AHU-1 sequence.']
    (stages/'sensor-cleanup.json').write_text(json.dumps(stage_report, indent=2)+'\n')
    requests.run(clean, three, stages/'three-requests.json')
    sequence.build(three, final, manifest, sha(three))
    data = json.loads(manifest.read_text())
    data.update({
        'revision': 'R2',
        'build_origin': {'path': str(baseline), 'sha256': BASE_SHA,
                         'evidence': 'User-reported CCT opening; complete sequence unverified'},
        'build_stages': [{'stage': 'sensor cleanup', 'sha256': sha(clean)},
                         {'stage': 'three requests with native proxy graphical records', 'sha256': sha(three)}],
        'failed_caf_used_as_input': False,
        'construction_change': 'Copy each native source position record and change only its coordinates. Preserve its display-category value and record shape.',
        'cct_acceptance': 'PENDING - CCT opening, resource checks and native simulation have not been performed',
    })
    manifest.write_text(json.dumps(data, indent=2)+'\n')
    return final, manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    final, manifest = build(args.baseline, args.destination)
    print(json.dumps({'caf': str(final), 'sha256': sha(final), 'manifest': str(manifest)}, indent=2))
