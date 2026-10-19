#!/usr/bin/env python3
"""R2 three-zone request builder preserving native proxy graphical records.

Clone complete native hardware, proxy, comparison-table, OR, selector, and
Activity-port records. Existing control objects remain byte-identical. The new
composition is experimental until CCT opening and simulation are reported.
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E

N = '{http://johnsoncontrols.com/MetasysIII/2002/3/Core}'
MAIN = '8-1/575_1'
EXPECTED = '9f05228f92915c9cd7c9077d90a13b2165c18ae302def96be884727e953d7286'


def parse(xml):
    root = E.fromstring(xml)
    objs = root.findall(N + 'object')
    result = {o.get('ref'): o for o in objs}
    assert len(result) == len(objs)
    return result


def prop(obj, pid):
    node = obj.find(f"{N}property[@id='{pid}']/{N}data")
    return node[0] if node is not None and len(node) else None


def new_value(kind, value=None, **attrs):
    node = E.Element(N + kind, nsmap={None: N[1:-1]}, **{k: str(v) for k, v in attrs.items()})
    if value is not None:
        node.text = str(value)
    return node


def set_prop(obj, pid, value):
    node = obj.find(f"{N}property[@id='{pid}']")
    if node is None:
        node = E.SubElement(obj, N + 'property', id=str(pid))
        data = E.SubElement(node, N + 'data')
    else:
        data = node.find(N + 'data')
        for child in list(data):
            data.remove(child)
    data.append(value)
    for sim in obj.findall(f"{N}simulationProperty[@id='{pid}']"):
        obj.remove(sim)


def array(kind, values):
    node = new_value(kind)
    for value in values:
        node.append(value)
    return node


def struct(values):
    node = new_value('struct')
    for value in values:
        E.SubElement(node, N + 'structElement').append(value)
    return node


def edge(values):
    return struct([new_value('unsignedShort', v) for v in values])


def position(x, y, mode):
    return struct([new_value('float', x), new_value('float', y), new_value('unsignedShort', mode)])


def metadata():
    return struct([new_value('boolean', 'false'), new_value('string')])


def bare_bytes(node):
    return E.tostring(node, encoding='utf-8').replace(
        b' xmlns="http://johnsoncontrols.com/MetasysIII/2002/3/Core"', b'').replace(
        b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"', b'')


def replace_property_bytes(raw, pid, node):
    pattern = rb'<property id="' + str(pid).encode() + rb'">.*?</property>'
    matches = list(re.finditer(pattern, raw, re.S))
    assert len(matches) == 1, pid
    m = matches[0]
    replacement = b'<property id="' + str(pid).encode() + b'"><data>' + bare_bytes(node) + b'</data></property>'
    return raw[:m.start()] + replacement + raw[m.end():]


class NativeClones:
    def __init__(self, existing):
        self.old = existing
        self.new = {}
        self.next_id = 400000
        self.used_numbers = {int(o.get('objectid')) for o in existing.values()}
        self.sources = []

    def allocate(self):
        while self.next_id in self.used_numbers:
            self.next_id += 1
        result = self.next_id
        self.next_id += 1
        self.used_numbers.add(result)
        return result

    def clone(self, source, parent):
        originals = [o for ref, o in self.old.items() if ref == source or ref.startswith(source + '.')]
        assert originals and originals[0].get('ref') == source
        originals.sort(key=lambda o: (o.get('ref').count('.'), list(self.old).index(o.get('ref'))))
        refs = {}
        id_map = {}
        for old in originals:
            ref = old.get('ref')
            oid = self.allocate()
            cid = prop(old, 75).get('id')
            old_id = prop(old, 75).text
            id_map[(cid, old_id)] = oid
            segment = old.get('ref').rsplit('.', 1)[-1].split('_')[0]
            refs[ref] = (parent if ref == source else refs[ref.rsplit('.', 1)[0]]) + f'.{segment}_{oid}'
        root = None
        for old in originals:
            obj = copy.deepcopy(old)
            old_ref = old.get('ref')
            obj.set('ref', refs[old_ref])
            obj.set('objectid', str(id_map[(prop(old, 75).get('id'), prop(old, 75).text)]))
            for node in obj.iter():
                if node.text in refs:
                    node.text = refs[node.text]
                if E.QName(node).localname == 'BACoid' and (node.get('id'), node.text) in id_map:
                    node.text = str(id_map[(node.get('id'), node.text)])
            for node in obj.findall(N + 'simulationProperty'):
                obj.remove(node)
            assert obj.get('ref') not in self.old and obj.get('ref') not in self.new
            self.new[obj.get('ref')] = obj
            if old_ref == source:
                root = obj
        self.sources.append({'source': source, 'clone': root.get('ref'), 'object_count': len(originals)})
        return root

    def clone_port(self, source, parent, port_id, label, enum_set=649):
        obj = self.clone(source, parent)
        assert len([k for k in self.new if k.startswith(obj.get('ref') + '.')]) == 0
        set_prop(obj, 3365, new_value('enum', port_id, set=509))
        set_prop(obj, 2390, new_value('string', label))
        set_prop(obj, 74, new_value('unsignedShort', 2))
        set_prop(obj, 931, new_value('enum', enum_set, set=802))
        set_prop(obj, 3113, new_value('enum', 0, set=enum_set))
        set_prop(obj, 110, array('listof', [new_value('string', 'Inactive'), new_value('string', 'Active')]))
        return obj

    def direct_port(self, obj, port_id):
        children = [o for ref, o in self.new.items() if ref.rsplit('.', 1)[0] == obj.get('ref')
                    and prop(o, 3365) is not None and prop(o, 3365).text == str(port_id)]
        assert len(children) == 1, (obj.get('ref'), port_id)
        return children[0]


def run(src, dest, report):
    assert hashlib.sha256(src.read_bytes()).hexdigest() == EXPECTED
    with ZipFile(src) as z:
        assert z.testzip() is None and len(z.infolist()) == 1
        info = z.infolist()[0]
        original = z.read(info.filename)
        comment = z.comment
    old = parse(original)
    assert len(old) == 2143
    raw = {m.group(1).decode(): m.group(0) for m in re.finditer(rb'<object\s+ref="([^"]+)"[^>]*>.*?</object>', original, re.S)}
    clones = NativeClones(old)
    patches = {}
    source_parent = old['8-1/307_2.910_10004']
    source_feature = [s for s in prop(source_parent, 1248)
                      if 'tempoccupancy' in list(s.itertext())]
    assert len(source_feature) == 1
    sensor_proxies = [old[MAIN + '.556_300143']]
    new_sensor_points = []
    for number, sensor_id in [(2, 10005), (3, 10006)]:
        parent = f'8-1/307_2.910_{sensor_id}'
        hw = clones.clone('8-1/307_2.910_10004.5_300143', parent)
        oid = int(hw.get('objectid'))
        name = f'ZN{number}-TOCC'
        set_prop(hw, 2390, new_value('string', name))
        feature = copy.deepcopy(source_feature[0])
        references = [n for n in feature.iter(N + 'BACoid') if n.get('id') == '5' and n.text == '300143']
        assert len(references) == 1
        references[0].text = str(oid)
        data = copy.deepcopy(prop(old[parent], 1248))
        assert not any('tempoccupancy' in list(s.itertext()) for s in data)
        data.append(feature)
        patches[parent] = replace_property_bytes(raw[parent], 1248, data)
        proxy = clones.clone(MAIN + '.556_300143', MAIN)
        # Native hardware proxies use the same instance number as their hardware point.
        proxy_oldref = proxy.get('ref')
        proxy_newref = MAIN + f'.556_{oid}'
        cloned_items = [(ref, o) for ref, o in list(clones.new.items())
                        if ref == proxy_oldref or ref.startswith(proxy_oldref + '.')]
        for ref, obj in cloned_items:
            del clones.new[ref]
            newref = proxy_newref + ref[len(proxy_oldref):]
            obj.set('ref', newref)
            if ref == proxy_oldref:
                obj.set('objectid', str(oid))
                set_prop(obj, 75, new_value('BACoid', oid, id=556))
            set_prop(obj, 32527, new_value('string', newref))
            clones.new[newref] = obj
        set_prop(proxy, 2390, new_value('string', name))
        external = copy.deepcopy(prop(proxy, 3399))
        bindings = list(external.iter(N + 'attrref'))
        assert len(bindings) == 1
        bindings[0].text = hw.get('ref')
        set_prop(proxy, 3399, external)
        for source in clones.sources:
            if source['clone'] == proxy_oldref:
                source['clone'] = proxy_newref
        sensor_proxies.append(proxy)
        new_sensor_points.append({'name': name, 'hardware_ref': hw.get('ref'), 'application_ref': proxy.get('ref')})

    # Start with a complete, CCT-authored custom Activity container. Its previous
    # children are not copied; every new child below is a complete native clone.
    activity_source = old[MAIN + '.536_86470']
    activity = copy.deepcopy(activity_source)
    activity_id = clones.allocate()
    activity_ref = MAIN + f'.536_{activity_id}'
    activity.set('ref', activity_ref)
    activity.set('objectid', str(activity_id))
    set_prop(activity, 32527, new_value('string', activity_ref))
    set_prop(activity, 75, new_value('BACoid', activity_id, id=536))
    set_prop(activity, 2390, new_value('string', 'ZONE-TOCC-OR'))
    clones.new[activity_ref] = activity
    inputs = [clones.clone_port(MAIN + '.536_86470.19_300130', activity_ref, 7000 + i,
                               f'ZN{i+1} Request') for i in range(3)]
    output = clones.clone_port(MAIN + '.536_86470.19_300132', activity_ref, 8000, 'Any Zone Request')

    tables = []
    for i in range(3):
        table = clones.clone(MAIN + '.536_86466.543_299716', activity_ref)
        set_prop(table, 2390, new_value('string', f'ZN{i+1} Request Active'))
        ip = clones.direct_port(table, 7000)
        set_prop(ip, 74, new_value('unsignedShort', 2))
        set_prop(ip, 931, new_value('enum', 649, set=802))
        # Rule table is the unchanged native 0 -> false, 1 -> true translation.
        assert [list(s.itertext()) for s in prop(table, 3138)] == [['0', '0', '0'], ['1', '0', '1']]
        tables.append(table)
    ors = [clones.clone(MAIN + '.536_81051.559_108889', activity_ref) for _ in range(2)]
    for label, obj in zip(['Zone 1 OR Zone 2', 'Any Zone Active'], ors):
        set_prop(obj, 2390, new_value('string', label))
        assert prop(obj, 518).text == '2' and prop(obj, 3670).text == '25'
    mux = clones.clone(MAIN + '.536_86466.562_265240', activity_ref)
    set_prop(mux, 2390, new_value('string', 'Active Inactive Request'))
    for port_id, default in [(85, 0), (7000, 0), (7001, 1)]:
        port = clones.direct_port(mux, port_id)
        set_prop(port, 74, new_value('unsignedShort', 2))
        set_prop(port, 931, new_value('enum', 649, set=802))
        set_prop(port, 3113, new_value('enum', default, set=649))
    blocks = [*inputs, *tables, *ors, mux, output]
    wires = [[i, 663, 3+i, 7000] for i in range(3)] + [
        [3, 32520, 6, 7000], [4, 32520, 6, 7001],
        [6, 85, 7, 7000], [5, 32520, 7, 7001],
        [7, 85, 8, 961], [8, 85, 9, 513],
    ]
    set_prop(activity, 3375, array('array', [copy.deepcopy(prop(o, 75)) for o in blocks]))
    set_prop(activity, 3117, array('array', [new_value('unsignedShort', i) for i in range(len(blocks))]))
    set_prop(activity, 3383, array('listof', [position(*v) for v in [
        (-600, -100, 22), (-600, 0, 22), (-600, 100, 22),
        (-420, -100, 10), (-420, 0, 10), (-420, 100, 10),
        (-240, -50, 2), (-100, 0, 2), (80, 0, 10), (270, 0, 23),
    ]]))
    set_prop(activity, 3118, array('array', [edge(e) for e in wires]))
    set_prop(activity, 3384, array('listof', [metadata() for _ in wires]))
    set_prop(activity, 3184, array('array', [new_value('enum', v, set=509) for v in [7000, 7001, 8000, 7002]]))

    main = copy.deepcopy(old[MAIN])
    main_blocks = copy.deepcopy(prop(main, 3375))
    new_top = [sensor_proxies[1], sensor_proxies[2], activity]
    main_blocks.extend(copy.deepcopy(prop(o, 75)) for o in new_top)
    top_indices = [103, 104, 105]
    order = copy.deepcopy(prop(main, 3117))
    order.extend(new_value('unsignedShort', i) for i in top_indices)
    geometry = copy.deepcopy(prop(main, 3383))
    native_refs = [MAIN + f".{v.get('id')}_{v.text}" for v in prop(old[MAIN], 3375)]
    def native_position(source, x, y):
        record = copy.deepcopy(prop(old[MAIN], 3383)[native_refs.index(source)])
        coordinates = list(record.iter(N + 'float'))
        assert len(coordinates) == 2
        coordinates[0].text, coordinates[1].text = str(x), str(y)
        return record
    geometry.extend([native_position(MAIN + '.556_300143', -1300, 550),
                     native_position(MAIN + '.556_300143', -1300, 640),
                     native_position(MAIN + '.536_86470', -1050, 550)])
    main_wires = copy.deepcopy(prop(main, 3118))
    existing = [[int(t.text) for t in e.iter(N + 'unsignedShort')] for e in main_wires]
    assert existing[130] == [98, 8000, 59, 3110]
    main_wires[130] = edge([105, 8000, 59, 3110])
    main_wires.extend(edge([s, 8000, 105, d]) for s, d in [(98, 7000), (103, 7001), (104, 7002)])
    meta = copy.deepcopy(prop(main, 3384))
    meta.extend(metadata() for _ in range(3))
    proxy_list = copy.deepcopy(prop(main, 3927))
    proxy_list.extend(copy.deepcopy(prop(o, 75)) for o in sensor_proxies[1:])
    changed = {3375: main_blocks, 3117: order, 3383: geometry,
               3118: main_wires, 3384: meta, 3927: proxy_list}
    main_raw = raw[MAIN]
    for pid, data in changed.items():
        main_raw = replace_property_bytes(main_raw, pid, data)
    patches[MAIN] = main_raw

    def patch_object(match):
        ref = match.group(1).decode()
        return patches.get(ref, match.group(0))
    xml = re.sub(rb'<object\s+ref="([^"]+)"[^>]*>.*?</object>', patch_object, original, flags=re.S)
    insertion = xml.index(b'<object ref="8-1/575_1.536_86473"')
    additions = b''.join(bare_bytes(o) for o in clones.new.values())
    xml = xml[:insertion] + additions + xml[insertion:]
    result = parse(xml)
    assert set(result) == set(old) | set(clones.new)
    assert len(result) == len(old) + 35
    assert all(E.tostring(result[ref]) == E.tostring(o) for ref, o in old.items() if ref not in patches)
    assert len(prop(result[MAIN], 3375)) == len(prop(result[MAIN], 3117)) == len(prop(result[MAIN], 3383)) == 106
    assert len(prop(result[MAIN], 3118)) == len(prop(result[MAIN], 3384)) == 145
    assert prop(result[MAIN + '.2_300134'], 3113).text == '3600'
    for o in result.values():
        for pid in [3399, 3672]:
            data = prop(o, pid)
            if data is not None:
                assert all(t.text in result for t in data.iter() if t.text and t.text.startswith('8-1/'))
        for t in o.iter():
            if t.text and t.text.startswith('8-1/'):
                assert t.text in result, (o.get('ref'), E.QName(t).localname, t.text)
    report_data = {
        'input': str(src), 'input_sha256': EXPECTED,
        'output': str(dest),
        'status': 'EXPERIMENTAL - STATIC CHECKS ONLY; CCT OPENING AND SIMULATION PENDING',
        'new_sensor_points': new_sensor_points,
        'activity_ref': activity_ref,
        'new_objects': sorted(clones.new),
        'modified_existing_objects': sorted(patches),
        'old_object_count': len(old), 'new_object_count': len(result),
        'main_blocks': 106, 'main_wires': 145,
        'main_wire_change': {'index': 130, 'old': [98, 8000, 59, 3110], 'new': [105, 8000, 59, 3110]},
        'activity_logic': 'Enum 649 requests -> native per-sensor enum-to-Boolean tables -> two native ORs -> native Boolean MUX with enum 649 values -> existing occupancy temporary request port 3110',
        'native_templates': clones.sources,
        'override_timeout_seconds': 3600,
        'sequence_scope': 'Three-zone temporary occupancy only. CIP, DCV, thermal demand and other sequence changes are not implemented in this candidate.',
        'cct_help_basis': {'Boolean OR': 'printed page 1637, Table 1336',
                           'Selection / translation': 'printed pages 1689-1690, Table 1366',
                           'Activity containers': 'printed pages 1658-1659, Table 1351'},
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(dest, 'w') as z:
        z.comment = comment
        z.writestr(info, xml)
    with ZipFile(dest) as z:
        assert z.testzip() is None and z.read(info.filename) == xml
    report_data['output_sha256'] = hashlib.sha256(dest.read_bytes()).hexdigest()
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(report_data, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report_data.items() if k not in ['new_objects', 'native_templates', 'activity_logic']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.output, args.report)
