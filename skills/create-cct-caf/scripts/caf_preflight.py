#!/usr/bin/env python3
"""Read-only preflight of the observed CAF structural subset; not CCT validation."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as E
from zipfile import BadZipFile, ZipFile

N = '{http://johnsoncontrols.com/MetasysIII/2002/3/Core}'


def value(obj, pid):
    data = obj.find(f"{N}property[@id='{pid}']/{N}data")
    return data[0] if data is not None and len(data) else None


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(caf, class_cache=None):
    errors, notes = [], []
    report = {
        'caf': str(caf), 'sha256': sha(caf),
        'scope': 'Observed CAF structural subset only',
        'native_cct_executed': False, 'control_behavior_verified': False,
        'limits': ['No native CCT rendering, compiler or resource checks',
                   'No port-type, physical I/O, safety-priority or full property validation',
                   'No Mux truth-table/reliability acceptance; inverted maps can pass',
                   'No native PID/FSM, persistence, communications or equipment execution'],
        'errors': errors, 'notes': notes,
    }
    with ZipFile(caf) as archive:
        if archive.testzip() is not None:
            raise ValueError('Archive CRC check failed')
        members = archive.namelist()
        xml_members = [n for n in members if n.lower().endswith('.xml')]
        report['archive_members'] = members
        if len(xml_members) != 1:
            raise ValueError('Unsupported archive layout: this preflight requires one XML member')
        root = E.fromstring(archive.read(xml_members[0]))
    if root.tag != N+'objects':
        raise ValueError('Unsupported CAF objects namespace/root')
    objects = root.findall(N+'object')
    counts = Counter(o.get('ref') for o in objects)
    if not objects:
        errors.append('No CAF objects found')
    if None in counts or '' in counts:
        errors.append('Object has an empty full reference')
    duplicates = [r for r, c in counts.items() if c > 1]
    if duplicates:
        errors.append({'duplicate_object_refs': duplicates})
    by = {o.get('ref'): o for o in objects}
    report.update(objects=len(objects), distinct_classes=len({o.get('classid') for o in objects}))
    graphs = wires_checked = omitted = 0
    for ref, obj in by.items():
        blocks = value(obj, 3375)
        if blocks is None:
            continue
        graphs += 1
        order, positions, wires, metadata = [value(obj, n) for n in (3117,3383,3118,3384)]
        if order is None or positions is None or len(blocks) != len(order) or len(blocks) != len(positions):
            errors.append({'graph': ref, 'error': 'Block/order/position lengths disagree or are missing'})
        if order is not None:
            try:
                if sorted(int(x.text) for x in order) != list(range(len(blocks))):
                    errors.append({'graph': ref, 'error': 'Display order is not a block-index permutation'})
            except (ValueError, TypeError):
                errors.append({'graph': ref, 'error': 'Non-numeric display order'})
        for b in blocks:
            target = str(ref)+'.'+str(b.get('id'))+'_'+str(b.text)
            if target not in by:
                errors.append({'graph': ref, 'missing_block_ref': target})
        if wires is None and metadata is None:
            omitted += 1
            continue
        if wires is None or metadata is None or len(wires) != len(metadata):
            errors.append({'graph': ref, 'error': 'Wire/graphical-metadata lengths disagree or are missing'})
        if wires is not None:
            for i, wire in enumerate(wires):
                try:
                    fields = [int(x.text) for x in wire.iter(N+'unsignedShort')]
                    if len(fields) != 4 or not (0 <= fields[0] < len(blocks) and 0 <= fields[2] < len(blocks)):
                        errors.append({'graph': ref, 'wire': i, 'error': 'Invalid connection shape or endpoint index'})
                    wires_checked += 1
                except (TypeError, ValueError):
                    errors.append({'graph': ref, 'wire': i, 'error': 'Non-numeric connection'})
    for ref, obj in by.items():
        ids, refs = value(obj,3926), value(obj,3927)
        if (ids is None) != (refs is None) or (ids is not None and len(ids) != len(refs)):
            errors.append({'object': ref, 'error': 'Paired hardware-registry lengths disagree'})
    report.update(graphs_checked=graphs, connections_checked=wires_checked,
                  graphs_omitting_both_wire_arrays=omitted)
    if omitted:
        notes.append('Some graphs omit both wire arrays; this observation is not a universal error')
    if class_cache:
        classes = {c.get('id'): c for c in E.parse(class_cache).getroot().findall('objectClass')}
        if not classes:
            raise ValueError('No objectClass definitions found in the supplied class cache')
        report['class_cache'] = {'path': str(class_cache), 'sha256': sha(class_cache), 'classes':len(classes)}
        uncovered = sorted({o.get('classid') for o in objects if o.get('classid') not in classes}, key=str)
        mismatches = [o.get('ref') for o in objects if o.get('classid') in classes
                      and o.get('classVersion') != classes[o.get('classid')].get('classVersion')]
        if uncovered:
            errors.append({'classes_missing_from_cache': uncovered})
        if mismatches:
            errors.append({'class_version_mismatches': mismatches})
        report['class_coverage'] = 'MATCH' if not uncovered and not mismatches else 'MISMATCH'
    else:
        report['class_coverage'] = 'NOT_CHECKED'
    report['status'] = 'STATIC_FAIL' if errors else 'STATIC_PASS_CCT_NOT_EXECUTED'
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('caf', type=Path)
    ap.add_argument('--class-cache', type=Path)
    ap.add_argument('--report', type=Path)
    args = ap.parse_args()
    inputs = {args.caf.resolve()}
    if args.class_cache:
        inputs.add(args.class_cache.resolve())
    aliases_input = args.report and (args.report.resolve() in inputs or
        (args.report.exists() and any(p.exists() and args.report.samefile(p) for p in inputs)))
    if aliases_input:
        ap.error('Use a separate report file; preserve all inputs')
    try:
        report = inspect(args.caf, args.class_cache)
    except (OSError, ValueError, E.ParseError, BadZipFile) as error:
        report = {'caf':str(args.caf), 'status':'STATIC_FAIL', 'native_cct_executed':False,
                  'control_behavior_verified':False, 'errors':[str(error)]}
    text = json.dumps(report, indent=2)+'\n'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text)
    print(text, end='')
    return 1 if report['status'] == 'STATIC_FAIL' else 0


if __name__ == '__main__':
    sys.exit(main())
