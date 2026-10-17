#!/usr/bin/env python3
"""One offline AHU-1 sensor-cleanup experiment; CCT acceptance is unverified.

Preserve XML bytes outside named object/property changes. Delete only the
obsolete NS8000 subtree and five unused application proxy subtrees, readdress
the retained sensors, and send effective occupancy to their existing displays.
Do not alter any operating sequence, setpoint, safety, or timer.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E

N = '{http://johnsoncontrols.com/MetasysIII/2002/3/Core}'
MAIN = '8-1/575_1'
EXPECTED = '078e1aa20f084e82212f205480f858bb17fad45a81081a74f74e4d429530bd26'
OBSOLETE = [
    '8-1/307_2.910_10000', MAIN + '.556_10002',
    MAIN + '.556_10006', MAIN + '.555_2086',
    MAIN + '.556_299726', MAIN + '.556_300140',
]


def prop(obj, pid):
    node = obj.find(f"{N}property[@id='{pid}']/{N}data")
    assert node is not None and len(node) == 1, (obj.get('ref'), pid)
    return node[0]


def objects(xml):
    root = E.fromstring(xml)
    items = root.findall(N + 'object')
    byref = {o.get('ref'): o for o in items}
    assert len(items) == len(byref), 'duplicate full object reference'
    return byref


def records(raw, pid, container, pattern):
    pat = (rb'(<property id="' + str(pid).encode() + rb'"><data><'
           + container.encode() + rb'>)(.*?)(</' + container.encode()
           + rb'></data></property>)')
    matches = list(re.finditer(pat, raw, re.S))
    assert len(matches) == 1, pid
    m = matches[0]
    parts = re.findall(pattern, m.group(2), re.S)
    assert b''.join(parts) == m.group(2), ('unexpected serialization', pid)
    return m, parts


def replace_records(raw, pid, container, pattern, transform):
    m, parts = records(raw, pid, container, pattern)
    updated = b''.join(transform(parts))
    return raw[:m.start(2)] + updated + raw[m.end(2):]


def wire(values):
    return b'<struct>' + b''.join(
        b'<structElement><unsignedShort>' + str(v).encode()
        + b'</unsignedShort></structElement>' for v in values
    ) + b'</struct>'


def edges(obj):
    return [[int(v.text) for v in row.iter(N + 'unsignedShort')]
            for row in prop(obj, 3118)]


def block_refs(obj):
    return [obj.get('ref') + f".{n.get('id')}_{n.text}"
            for n in prop(obj, 3375)]


def semantic_edges(obj):
    refs = block_refs(obj)
    return [(refs[a], b, refs[c], d) for a, b, c, d in edges(obj)]


def run(src, dest, report_path):
    assert hashlib.sha256(src.read_bytes()).hexdigest() == EXPECTED, 'wrong baseline'
    with ZipFile(src) as z:
        assert z.testzip() is None and len(z.infolist()) == 1
        info = z.infolist()[0]
        original = z.read(info.filename)
        archive_comment = z.comment
    old = objects(original)
    assert len(old) == 2167
    raw_matches = list(re.finditer(rb'<object\s+ref="([^"]+)"[^>]*>.*?</object>', original, re.S))
    raw = {m.group(1).decode(): m.group(0) for m in raw_matches}
    assert set(raw) == set(old)
    remove = {ref for ref in old if any(
        ref == prefix or ref.startswith(prefix + '.') for prefix in OBSOLETE)}
    assert len(remove) == 24
    main = old[MAIN]
    old_blocks = block_refs(main)
    gone = {i for i, ref in enumerate(old_blocks) if ref in remove}
    assert gone == {63, 64, 65, 66, 102}
    retained = [i for i in range(len(old_blocks)) if i not in gone]
    index = {before: after for after, before in enumerate(retained)}
    old_edges = edges(main)
    affected = [i for i, e in enumerate(old_edges) if e[0] in gone or e[2] in gone]
    assert affected == [113] and old_edges[113] == [59, 50032, 65, 7000]
    assert not any(e[2] in [88, 92, 96] for e in old_edges), 'display already driven'
    assert old_blocks[88] == MAIN + '.555_300059'
    assert old_blocks[92] == MAIN + '.555_300074'
    assert old_blocks[96] == MAIN + '.555_300089'

    # The source and each retained display are the same enum set, Occupancy 345.
    occ = old[MAIN + '.524_51131']
    ports = [o for ref, o in old.items() if ref.startswith(occ.get('ref') + '.')
             and o.find(f"{N}property[@id='3365']/{N}data") is not None
             and prop(o, 3365).text == '50032']
    assert len(ports) == 1 and prop(ports[0], 931).text == '345'
    for ref in [MAIN + '.555_300059', MAIN + '.555_300074', MAIN + '.555_300089']:
        children = [o for k, o in old.items() if k.startswith(ref + '.')
                    and o.find(f"{N}property[@id='3365']/{N}data") is not None
                    and prop(o, 3365).text == '7000']
        assert len(children) == 1 and prop(children[0], 931).text == '345'

    new_edges = []
    for i, (a, b, c, d) in enumerate(old_edges):
        if i == 113:
            c = 88
        new_edges.append([index[a], b, index[c], d])
    new_edges.extend([[index[59], 50032, index[i], 7000] for i in [92, 96]])

    bac = rb'<BACoid id="\d+">\d+</BACoid>'
    ushort = rb'<unsignedShort>\d+</unsignedShort>'
    structure = rb'<struct>.*?</struct>'
    wire_pattern = rb'<struct>(?:<structElement><unsignedShort>\d+</unsignedShort></structElement>){4}</struct>'
    newmain = raw[MAIN]
    newmain = replace_records(newmain, 3375, 'array', bac,
                              lambda parts: [parts[i] for i in retained])
    newmain = replace_records(newmain, 3117, 'array', ushort,
                              lambda parts: [b'<unsignedShort>' + str(index[int(re.search(rb'>(\d+)<', x).group(1))]).encode()
                                             + b'</unsignedShort>' for x in parts
                                             if int(re.search(rb'>(\d+)<', x).group(1)) not in gone])
    newmain = replace_records(newmain, 3383, 'listof', structure,
                              lambda parts: [parts[i] for i in retained])
    newmain = replace_records(newmain, 3118, 'array', wire_pattern,
                              lambda parts: [wire(e) for e in new_edges])
    # Use the native display-wire metadata for its two additional destinations.
    newmain = replace_records(newmain, 3384, 'listof', structure,
                              lambda parts: parts + [parts[113], parts[113]])
    removed_proxy_keys = {(prop(old[r], 75).get('id'), prop(old[r], 75).text)
                          for r in OBSOLETE[1:]}
    def keep_proxy_records(parts):
        kept = []
        removed = 0
        for record in parts:
            node = E.fromstring(record)
            if (node.get('id'), node.text) in removed_proxy_keys:
                removed += 1
            else:
                kept.append(record)
        assert removed == 3  # T/H proxies weren't in this auxiliary list.
        return kept
    newmain = replace_records(newmain, 3927, 'listof', bac, keep_proxy_records)

    replacements = {MAIN: newmain}
    addresses = []
    for oid, before, after, label in [(10004, 200, 199, 'ZN1'), (10005, 201, 200, 'ZN2'), (10006, 202, 201, 'ZN3')]:
        ref = f'8-1/307_2.910_{oid}'
        assert prop(old[ref], 2858).text == str(before)
        a = b'<property id="2858"><data><unsignedByte>' + str(before).encode() + b'</unsignedByte></data></property>'
        b = b'<property id="2858"><data><unsignedByte>' + str(after).encode() + b'</unsignedByte></data></property>'
        assert raw[ref].count(a) == 1
        replacements[ref] = raw[ref].replace(a, b, 1)
        addresses.append({'sensor': label, 'old_address': before, 'new_address': after})

    # Copy all original inter-object bytes; replace/remove only selected objects.
    chunks = []
    cursor = 0
    for m in raw_matches:
        ref = m.group(1).decode()
        chunks.append(original[cursor:m.start()])
        chunks.append(b'' if ref in remove else replacements.get(ref, m.group(0)))
        cursor = m.end()
    chunks.append(original[cursor:])
    result = b''.join(chunks)
    new = objects(result)
    assert set(new) == set(old) - remove
    assert len(new) == 2143
    for ref in new:
        if ref not in replacements:
            assert E.tostring(new[ref]) == E.tostring(old[ref]), ref
    # Verify no references to any removed subtree survive anywhere in typed strings.
    for obj in new.values():
        for node in obj.iter():
            if node.text:
                assert not any(node.text == r or node.text.startswith(r + '.') for r in OBSOLETE), (obj.get('ref'), node.text)
    # All removed proxy references have left the main BACoid properties.
    for node in new[MAIN].iter(N + 'BACoid'):
        assert (node.get('id'), node.text) not in removed_proxy_keys

    changed_main = new[MAIN]
    assert len(prop(changed_main, 3375)) == len(prop(changed_main, 3117)) == len(prop(changed_main, 3383)) == 103
    assert sorted(int(x.text) for x in prop(changed_main, 3117)) == list(range(103))
    assert len(prop(changed_main, 3118)) == len(prop(changed_main, 3384)) == 142
    assert edges(changed_main) == new_edges
    assert all(k in new for k in block_refs(changed_main))
    # All previously existing functional wires must have the same identities.
    before_semantic = semantic_edges(main)
    after_semantic = semantic_edges(changed_main)
    assert [e for i, e in enumerate(before_semantic) if i != 113] == [e for i, e in enumerate(after_semantic[:140]) if i != 113]
    display_edges = [after_semantic[113], *after_semantic[140:]]
    assert display_edges == [(MAIN + '.524_51131', 50032, MAIN + f'.555_{oid}', 7000) for oid in [300059, 300074, 300089]]
    assert prop(new[MAIN + '.2_300134'], 3113).text == '3600'
    assert len([o for o in new.values() if o.get('classid') == '910']) == 3
    assert sorted(int(prop(o, 2858).text) for o in new.values() if o.get('classid') == '910') == [199, 200, 201]
    # Only the explicitly documented property values may change.
    allowed = {MAIN: {'3117', '3118', '3375', '3383', '3384', '3927'},
               **{f'8-1/307_2.910_{i}': {'2858'} for i in [10004, 10005, 10006]}}
    for ref, o in new.items():
        previous = {p.get('id'): E.tostring(p) for p in old[ref].findall(N + 'property')}
        current = {p.get('id'): E.tostring(p) for p in o.findall(N + 'property')}
        changed = {k for k in previous.keys() | current.keys() if previous.get(k) != current.get(k)}
        assert changed == allowed.get(ref, set()), (ref, changed)

    dest.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(dest, 'w') as z:
        z.comment = archive_comment
        z.writestr(info, result)
    with ZipFile(dest) as z:
        assert z.testzip() is None and z.read(info.filename) == result
    report = {
        'input': str(src), 'input_sha256': EXPECTED,
        'output': str(dest), 'output_sha256': hashlib.sha256(dest.read_bytes()).hexdigest(),
        'status': 'STATIC CHECKS PASS; CCT OPENING/SIMULATION NOT YET TESTED',
        'archive_member_preserved': info.filename,
        'old_objects': len(old), 'new_objects': len(new), 'added_objects': [],
        'removed_objects': sorted(remove),
        'changed_object_properties': {k: sorted(v, key=int) for k, v in allowed.items()},
        'old_main_blocks': 108, 'new_main_blocks': 103,
        'old_main_connections': 140, 'new_main_connections': 142,
        'unchanged_functional_connections_by_object_identity': 139,
        'occupancy_display_connections': display_edges,
        'sensor_addresses': addresses,
        'retained_temporary_occupancy_request': 'ZN1-TOCC only; three-sensor combination still pending',
        'temporary_occupancy_timeout_seconds': 3600,
        'checks': ['CRC/XML', 'unique full refs', 'diagram list lengths/order',
                   'all graph block references resolve', 'no removed-subtree references remain',
                   'all unrelated objects byte-identical', 'only intended property changes',
                   'all 139 control wires preserved by object identity',
                   'same enum set 345 at all new display destinations',
                   'unique NS8000 addresses 199/200/201', 'override timeout preserved'],
        'limitations': ['CCT compatibility unverified', 'no CCT runtime available here',
                        'current AHU sequence/submittal attachment unavailable',
                        'no full sequence or field validation'],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ['removed_objects', 'checks', 'occupancy_display_connections']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.output, args.report)
