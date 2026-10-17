#!/usr/bin/env python3
"""Read-only inventories and rendering-metadata comparisons for observed CAFs.

This is an empirical inspection tool, not a CAF compiler or generator. Native
examples define observed combinations; an unobserved combination is evidence
to investigate, not proof of the cause of a CCT failure.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as E

N = '{http://johnsoncontrols.com/MetasysIII/2002/3/Core}'
POINTS = {526: ('input', 'float'), 527: ('output', 'float'),
          528: ('input', 'enum'), 529: ('output', 'enum'),
          530: ('input', 'boolean'), 531: ('output', 'boolean')}


def prop(obj, number):
    data = obj.find(f"{N}property[@id='{number}']/{N}data")
    return data[0] if data is not None and len(data) else None


def scalar(obj, number):
    value = prop(obj, number)
    return value.text if value is not None else None


def typed(value):
    if value is None:
        return None
    kind = value.tag.removeprefix(N)
    if len(value):
        result = {'kind': kind, 'children': [typed(v) for v in value]}
    else:
        result = {'kind': kind, 'value': value.text}
    if value.attrib:
        result['attributes'] = dict(value.attrib)
    return result


def digest(data):
    return hashlib.sha256(data).hexdigest()


class CAF:
    def __init__(self, path):
        self.path = Path(path)
        self.bytes = self.path.read_bytes()
        with ZipFile(self.path) as archive:
            if archive.testzip() is not None or len(archive.infolist()) != 1:
                raise ValueError('Expected one intact XML archive member')
            info = archive.infolist()[0]
            self.member = info.filename
            self.zip_method = info.compress_type
            self.xml = archive.read(info.filename)
        root = E.fromstring(self.xml)
        self.objects = root.findall(N+'object')
        self.by = {o.get('ref'): o for o in self.objects}
        if len(self.by) != len(self.objects):
            raise ValueError('Duplicate full object references')
        self.children = defaultdict(list)
        for o in self.objects:
            self.children[o.get('ref').rsplit('.', 1)[0]].append(o)
        mains = [o for o in self.objects if o.get('classid') == '575']
        if len(mains) != 1:
            raise ValueError('Expected exactly one main application')
        self.main = mains[0]
        self.graphs = [self.graph(o) for o in self.objects if prop(o, 3375) is not None]

    def port(self, obj):
        cid = int(obj.get('classid'))
        return {'ref': obj.get('ref'), 'class_id': cid,
                'port_id': int(scalar(obj, 3365)),
                'direction': POINTS.get(cid, ('unknown', 'unknown'))[0],
                'type': POINTS.get(cid, ('unknown', 'unknown'))[1],
                'explicit_name': scalar(obj, 2390), 'role_id': scalar(obj, 3670),
                'units_enum': scalar(obj, 117), 'enum_set': scalar(obj, 931),
                'enum_count': scalar(obj, 74), 'enum_labels': typed(prop(obj, 110)),
                'default': typed(prop(obj, 3113)), 'published': scalar(obj, 3807),
                'simulation_properties': {p.get('id'): typed(p.find(N+'data')[0])
                                          for p in obj.findall(N+'simulationProperty')
                                          if p.find(N+'data') is not None and len(p.find(N+'data'))},
                'property_ids': [int(p.get('id')) for p in obj.findall(N+'property')]}

    def graph(self, obj):
        block_refs = [obj.get('ref')+f".{v.get('id')}_{v.text}" for v in prop(obj, 3375)]
        order, positions, wires, metadata = [prop(obj, n) for n in [3117, 3383, 3118, 3384]]
        issues = []
        for number, value in zip([3117, 3383], [order, positions]):
            if value is None:
                issues.append(f'missing diagram property {number}')
        if (wires is None) != (metadata is None):
            issues.append('only one of the connection/metadata properties is present')
        if order is not None and positions is not None and len({len(block_refs), len(order), len(positions)}) != 1:
            issues.append('block/order/position count mismatch')
        if wires is not None and metadata is not None and len(wires) != len(metadata):
            issues.append('wire/metadata count mismatch')
        entries = []
        for index, ref in enumerate(block_refs):
            block = self.by.get(ref)
            if block is None:
                issues.append('unresolved block '+ref)
            row = positions[index] if positions is not None and index < len(positions) else None
            codes = list(row.iter(N+'unsignedShort')) if row is not None else []
            entries.append({'index': index, 'ref': ref,
                            'class_id': int(block.get('classid')) if block is not None else None,
                            'role_id': scalar(block, 3670) if block is not None else None,
                            'display_code': int(codes[0].text) if len(codes) == 1 else None})
        edge_values = []
        for edge in wires if wires is not None else []:
            values = [int(v.text) for v in edge.iter(N+'unsignedShort')]
            edge_values.append(values)
            if len(values) != 4 or not (0 <= values[0] < len(entries) and 0 <= values[2] < len(entries)):
                issues.append('invalid edge '+str(values))
        return {'ref': obj.get('ref'), 'scope': 'main' if obj is self.main else 'nested',
                'block_count': len(block_refs), 'wire_count': len(edge_values),
                'connection_arrays': 'both omitted' if wires is None and metadata is None else 'present',
                'blocks': entries, 'edges': edge_values, 'issues': issues}

    def catalog(self):
        main_graph = next(g for g in self.graphs if g['ref'] == self.main.get('ref'))
        modules = []
        for entry in main_graph['blocks']:
            obj = self.by[entry['ref']]
            prefix = obj.get('ref')+'.'
            subtree = [o for o in self.objects if o is obj or o.get('ref').startswith(prefix)]
            graphs = [g for g in self.graphs if g['ref'] == obj.get('ref') or g['ref'].startswith(prefix)]
            ports = [self.port(c) for c in self.children[obj.get('ref')] if prop(c, 3365) is not None]
            exports = prop(obj, 3184)
            attribute_refs = sorted({v.text for o in subtree for v in o.iter(N+'attrref')
                                     if v.text and not v.text.startswith(prefix) and v.text != obj.get('ref')})
            modules.append({**entry, 'explicit_name': scalar(obj, 2390),
                            'export_order': [int(v.text) for v in exports] if exports is not None else [],
                            'generated_state_port': scalar(obj, 3634),
                            'property_ids': [int(v.get('id')) for v in obj.findall(N+'property')],
                            'subtree_object_count': len(subtree),
                            'subtree_sha256': digest(b''.join(E.tostring(o) for o in subtree)),
                            'nested_graphs': len(graphs),
                            'nested_connections': sum(g['wire_count'] for g in graphs),
                            'nested_class_counts': dict(sorted(Counter(o.get('classid') for o in subtree).items())),
                            'external_attribute_refs': attribute_refs, 'ports': ports})
        return {'source': self.path.name, 'sha256': digest(self.bytes), 'bytes': len(self.bytes),
                'xml_member': self.member, 'xml_sha256': digest(self.xml),
                'serialized_format_version': scalar(self.main, 3671),
                'serialized_save_value': scalar(self.main, 3632),
                'evidence': 'User-supplied native module reference; no behavioral simulation report supplied',
                'objects': len(self.objects), 'class_counts': dict(sorted(Counter(o.get('classid') for o in self.objects).items())),
                'main_blocks': main_graph['block_count'], 'main_connections': main_graph['wire_count'],
                'graph_count': len(self.graphs), 'internal_connections': sum(g['wire_count'] for g in self.graphs if g['scope'] != 'main'),
                'graphs_with_omitted_connection_arrays': [g['ref'] for g in self.graphs if g['connection_arrays'] == 'both omitted'],
                'structural_issues': [{'graph': g['ref'], 'issues': g['issues']} for g in self.graphs if g['issues']],
                'modules': modules}


def profile(cafs, by_role=False):
    result = defaultdict(lambda: defaultdict(list))
    for caf in cafs:
        for graph in caf.graphs:
            for block in graph['blocks']:
                if block['class_id'] is None:
                    continue
                key = f"{graph['scope']}:{block['class_id']}"
                if by_role:
                    key += ':'+str(block['role_id'])
                result[key][block['display_code']].append({'source': caf.path.name,
                                                          'graph': graph['ref'], 'ref': block['ref']})
    return {key: {str(code): {'count': len(examples), 'examples': examples[:3]}
                  for code, examples in sorted(codes.items(), key=lambda x: str(x[0]))}
            for key, codes in sorted(result.items())}


def audit(candidate, references):
    observed = profile(references)
    roles = profile(references, by_role=True)
    discrepancies = []
    unsupported_classes = Counter()
    for graph in candidate.graphs:
        for block in graph['blocks']:
            key = f"{graph['scope']}:{block['class_id']}"
            role_key = key+':'+str(block['role_id'])
            codes = roles.get(role_key, observed.get(key))
            if codes is None:
                unsupported_classes[key] += 1
                continue
            if str(block['display_code']) not in codes:
                discrepancies.append({'graph': graph['ref'], 'scope': graph['scope'], **block,
                                      'observed_codes': list(codes),
                                      'comparison_scope': 'class and role' if role_key in roles else 'class only'})
    return {'candidate': candidate.path.name, 'sha256': digest(candidate.bytes),
            'references': [{'source': c.path.name, 'sha256': digest(c.bytes)} for c in references],
            'status': 'Observational rendering-metadata comparison only; CCT execution not performed',
            'structural_issues': [{'graph': g['ref'], 'issues': g['issues']} for g in candidate.graphs if g['issues']],
            'unobserved_display_combinations': discrepancies,
            'unobserved_combination_counts': dict(Counter(f"{v['scope']}:{v['class_id']}:{v['display_code']}" for v in discrepancies)),
            'classes_not_covered_by_references': dict(unsupported_classes),
            'limitation': 'Unobserved codes identify a discrepancy, not a universal invalidity rule or isolated root cause. Coordinates, order, ports, roles and other metadata also require review.'}


def module_detail(caf, ref):
    """Expose the complete original subtree and its graphs without cloning it."""
    if ref not in caf.by:
        raise ValueError('Unknown full object reference: '+ref)
    subtree = [o for o in caf.objects if o.get('ref') == ref or o.get('ref').startswith(ref+'.')]
    return {'source': caf.path.name, 'source_sha256': digest(caf.bytes), 'ref': ref,
            'object_count': len(subtree),
            'objects': [{'attributes': dict(o.attrib),
                         'properties': {p.get('id'): typed(p.find(N+'data')[0])
                                        for p in o.findall(N+'property') if p.find(N+'data') is not None and len(p.find(N+'data'))},
                         'xml_rendering': E.tostring(o, encoding='unicode')}
                        for o in subtree],
            'graphs': [g for g in caf.graphs if g['ref'] == ref or g['ref'].startswith(ref+'.')],
            'note': 'XML renderings are parser serializations for inspection, not byte-identical CAF fragments. Original CAF bytes remain authoritative.'}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2)+'\n')


def build_index(paths, output):
    cafs = [CAF(path) for path in paths]
    output.mkdir(parents=True, exist_ok=True)
    summary = []
    lines = ['# Native module index', '',
             'Generated from the four untouched user-supplied CAFs. Names are literal property 2390 values; an unnamed module is identified by its class and role. The catalogs preserve exact port order, typed defaults, enum descriptors, object references, subtree counts and fingerprints. No module behavior or cloning procedure is certified by this index.', '']
    for caf in cafs:
        data = caf.catalog()
        filename = caf.path.stem+'.json'
        write_json(output/filename, data)
        summary.append({k: v for k, v in data.items() if k != 'modules'})
        lines += ['## '+caf.path.name, '',
                  f"{data['objects']:,} objects; {data['main_blocks']} top-level blocks; {data['main_connections']} top-level connections; {data['internal_connections']:,} internal connections.", '',
                  f"Detailed port/configuration catalog: [{filename}]({filename}).", '',
                  '| Index | Serialized name | Class / role | Full object ref | Subtree objects | Internal wires | Exported ports |',
                  '|---:|---|---|---|---:|---:|---:|']
        for m in data['modules']:
            name = (m['explicit_name'] or '(unnamed)').replace('|', '\\|').replace('\n', ' ')
            lines.append(f"| {m['index']} | {name} | {m['class_id']} / {m['role_id']} | `{m['ref']}` | {m['subtree_object_count']} | {m['nested_connections']} | {len(m['export_order'])} |")
        lines.append('')
    write_json(output/'summary.json', summary)
    write_json(output/'display-code-profile.json', profile(cafs))
    write_json(output/'display-code-profile-by-role.json', profile(cafs, by_role=True))
    (output/'INDEX.md').write_text('\n'.join(lines)+'\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    index = commands.add_parser('index')
    index.add_argument('caf', nargs='+', type=Path)
    index.add_argument('--output-dir', type=Path, required=True)
    compare = commands.add_parser('audit-display')
    compare.add_argument('candidate', type=Path)
    compare.add_argument('--reference', type=Path, nargs='+', required=True)
    compare.add_argument('--output', type=Path, required=True)
    module = commands.add_parser('module')
    module.add_argument('caf', type=Path)
    module.add_argument('--ref', required=True)
    module.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'index':
        summary = build_index(args.caf, args.output_dir)
        print(json.dumps([{k: v for k, v in row.items() if k in ['source', 'objects', 'main_blocks', 'main_connections', 'graph_count', 'internal_connections', 'structural_issues']} for row in summary], indent=2))
    elif args.command == 'audit-display':
        report = audit(CAF(args.candidate), [CAF(p) for p in args.reference])
        write_json(args.output, report)
        print(json.dumps({k: v for k, v in report.items() if k != 'unobserved_display_combinations'}, indent=2))
    else:
        detail = module_detail(CAF(args.caf), args.ref)
        write_json(args.output, detail)
        print(json.dumps({k: v for k, v in detail.items() if k not in ['objects', 'graphs']}, indent=2))
