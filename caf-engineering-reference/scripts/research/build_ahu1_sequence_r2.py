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
import re
from zipfile import ZipFile
import copy

import make_ahu_sensor_cleanup_candidate as cleanup
import make_ahu_three_tocc_candidate_r2 as requests
import build_ahu_sequence_r2 as sequence
from caf_native_builder_r2 import parse, prop, replace_property_bytes, N, MAIN

BASE_SHA = '078e1aa20f084e82212f205480f858bb17fad45a81081a74f74e4d429530bd26'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repair_hardware_registry(baseline, target):
    """Re-pair the original native GUID/ref registries by full point identity.

    New NS8000 request proxies inherit the source proxy's registry value, which
    is zero in this native file. No GUID values are invented.
    """
    with ZipFile(baseline) as z:
        original = parse(z.read(z.namelist()[0]))
    with ZipFile(target) as z:
        info, comment = z.infolist()[0], z.comment
        xml = z.read(info.filename)
    current = parse(xml)
    old_ids, old_refs = prop(original[MAIN], 3926), prop(original[MAIN], 3927)
    assert len(old_ids) == len(old_refs) == 70
    mapping = {(r.get('id'), r.text): copy.deepcopy(g) for g, r in zip(old_ids, old_refs)}
    assert len(mapping) == len(old_refs)
    clone_sources = {('556', '400000'): ('556', '300143'),
                     ('556', '400004'): ('556', '300143')}
    identifiers = copy.deepcopy(old_ids)
    for child in list(identifiers):
        identifiers.remove(child)
    new_refs = prop(current[MAIN], 3927)
    for item in new_refs:
        key = (item.get('id'), item.text)
        source = clone_sources.get(key, key)
        assert source in mapping, ('unknown hardware registry source', key)
        if key in clone_sources:
            assert MAIN + f'.{key[0]}_{key[1]}' in current
        # The user-opened baseline already contains inactive registry entries
        # without live proxy objects. Preserve their native pairing; do not
        # delete them or assume every registry row is a diagram object.
        identifiers.append(copy.deepcopy(mapping[source]))
    assert len(identifiers) == len(new_refs) == 69
    raw = re.search(rb'<object\s+ref="8-1/575_1"[^>]*>.*?</object>', xml, re.S)
    assert raw is not None
    replacement = replace_property_bytes(raw.group(0), 3926, identifiers)
    xml = xml[:raw.start()] + replacement + xml[raw.end():]
    with ZipFile(target, 'w') as z:
        z.comment = comment
        z.writestr(info, xml)
    return {'paired_properties': [3926, 3927], 'baseline_entries': 70,
            'final_entries': 69, 'source': 'Baseline entries matched by full proxy identity; cloned request entries inherit ZN1-TOCC registry value.'}


def build(baseline, destination, repair_registry=True):
    assert sha(baseline) == BASE_SHA, 'Use the exact last user-reported CCT-open baseline'
    destination.mkdir(parents=True, exist_ok=True)
    stages = destination/'stages'
    stages.mkdir(exist_ok=True)
    clean = stages/'AHU-1_Sensors_R2.caf'
    three = stages/'AHU-1_Three_Requests_R2.caf'
    revision = 'R2'
    final = destination/f'AHU-1_Sequence_{revision}_CCT_TEST.caf'
    manifest = destination/f'AHU-1_Sequence_{revision}_Manifest.json'
    cleanup.run(baseline, clean, stages/'sensor-cleanup.json')
    stage_report = json.loads((stages/'sensor-cleanup.json').read_text())
    stage_report['limitations'] = ['CCT acceptance unverified; no CCT runtime here',
                                   'Sensor cleanup is one stage; the final build applies the AHU-1 sequence.']
    (stages/'sensor-cleanup.json').write_text(json.dumps(stage_report, indent=2)+'\n')
    requests.run(clean, three, stages/'three-requests.json')
    sequence.build(three, final, manifest, sha(three))
    data = json.loads(manifest.read_text())
    if repair_registry:
        data['hardware_registry_repair'] = repair_hardware_registry(baseline, final)
    data['output_sha256'] = sha(final)
    data.update({
        'revision': 'R2.1' if repair_registry else 'R2',
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
    parser.add_argument('--graphics-only-r2', action='store_true', help='Reproduce the superseded graphical-only R2 draft without registry repair.')
    args = parser.parse_args()
    final, manifest = build(args.baseline, args.destination, repair_registry=not args.graphics_only_r2)
    print(json.dumps({'caf': str(final), 'sha256': sha(final), 'manifest': str(manifest)}, indent=2))
