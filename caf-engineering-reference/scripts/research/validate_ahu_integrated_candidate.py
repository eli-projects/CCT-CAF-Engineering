#!/usr/bin/env python3
"""Static checks and an independent interpreter for the new serialized graphs.

The interpreter models documented block behavior and selected-input MUX quality.
It does not execute CCT, its compiler, existing AHU FSMs, or the PID loops.
"""
import copy
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E

N = '{http://johnsoncontrols.com/MetasysIII/2002/3/Core}'


def p(o, pid):
    d = o.find(f"{N}property[@id='{pid}']/{N}data")
    return d[0] if d is not None and len(d) else None


def edges(o):
    return [[int(v.text) for v in row.iter(N+'unsignedShort')] for row in p(o, 3118)]


def refs(o):
    return [o.get('ref') + f".{v.get('id')}_{v.text}" for v in p(o, 3375)]


def port_type(o):
    cid = int(o.get('classid'))
    if cid in [526, 527]:
        return ('float', None)
    if cid in [530, 531]:
        return ('boolean', None)
    if cid in [528, 529]:
        return ('enum', int(p(o, 931).text) if p(o, 931) is not None else None)
    raise ValueError((o.get('ref'), cid))


@dataclass
class Value:
    value: float | int | bool
    reliable: bool = True


def cell(x):
    return x if isinstance(x, Value) else Value(x)


class Runtime:
    def __init__(self, by, ref):
        self.by, self.root = by, by[ref]
        self.blocks = [by[r] for r in refs(self.root)]
        self.links = edges(self.root)
        self.state = {}
        self.ports = {}
        for ref, obj in by.items():
            number = p(obj, 3365)
            if number is not None:
                key = (ref.rsplit('.', 1)[0], int(number.text))
                self.ports.setdefault(key, []).append(obj)
        self.incoming = {j: [] for j in range(len(self.blocks))}
        for a, b, c, d in self.links:
            self.incoming[c].append((a, b, d))

    def port(self, o, number):
        found = self.ports.get((o.get('ref'), number), [])
        assert len(found) == 1, (o.get('ref'), number, len(found))
        return found[0]

    def default(self, o):
        v = p(o, 3113)
        if v is None:
            return Value(False if int(o.get('classid')) in [530, 531] else 0)
        if v.tag == N+'boolean':
            return Value(v.text == 'true')
        return Value(float(v.text) if v.tag == N+'float' else int(v.text))

    def step(self, time, inputs):
        values, pending = {}, set(range(len(self.blocks)))
        for j, o in enumerate(self.blocks):
            if int(o.get('classid')) in [526, 528, 530]:
                values[(j, 663)] = cell(inputs.get(int(p(o, 3365).text), self.default(o)))
                pending.remove(j)
        for _ in range(len(self.blocks)+1):
            progress = False
            for j in list(pending):
                o = self.blocks[j]
                incoming = self.incoming[j]
                if any((a, b) not in values for a, b, _ in incoming):
                    continue
                data = {d: values[(a, b)] for a, b, d in incoming}
                def get(port):
                    return data[port] if port in data else self.default(self.port(o, port))
                cid, key = int(o.get('classid')), o.get('ref')
                if cid in [527, 529, 531]:
                    value = data.get(513, self.default(o))
                    values[(j, 513)] = value
                    pending.remove(j)
                    progress = True
                    continue
                if cid == 539:
                    result, output = Value(get(513).reliable), 85
                elif cid == 543:
                    x = get(7000)
                    found = []
                    for row in p(o, 3138):
                        terms = row[0][0]
                        assert len(terms) == 1
                        condition = terms[0]
                        assert int(condition[1][0].text) == 0
                        if int(condition[0][0].text) == int(x.value):
                            found.append(bool(int(row[1][0].text)))
                    assert len(found) == 1, (key, x, found)
                    result, output = Value(found[0], x.reliable), 32520
                elif cid == 559:
                    setup = int(p(o, 518).text) if p(o, 518) is not None else 0
                    a = get(7000)
                    if setup == 0:
                        result = Value(not a.value, a.reliable)
                    else:
                        b = get(7001)
                        result = Value(bool(a.value and b.value) if setup == 1 else bool(a.value or b.value), a.reliable and b.reliable)
                        assert setup in [1, 2]
                    output = 85
                elif cid == 561:
                    setup = int(p(o, 518).text)
                    a, b = get(7000), get(7001)
                    op = {12: lambda: a.value/b.value, 13: lambda: a.value-b.value,
                          14: lambda: a.value+b.value, 15: lambda: a.value*b.value,
                          17: lambda: min(a.value, b.value), 18: lambda: max(a.value, b.value)}[setup]
                    try:
                        numeric = op()
                        good = math.isfinite(numeric)
                    except (ZeroDivisionError, OverflowError):
                        numeric, good = 0, False
                    result, output = Value(numeric, a.reliable and b.reliable and good), 85
                elif cid == 560:
                    setup = int(p(o, 518).text) if p(o, 518) is not None else 0
                    a, b, diff = get(50083), get(50084), get(637)
                    previous = bool(self.state.get(key, False))
                    good = a.reliable and b.reliable and diff.reliable
                    if not good:
                        value = previous
                    elif setup == 0:
                        value = a.value > b.value - (diff.value if previous else 0)
                    elif setup == 1:
                        value = a.value < b.value + (diff.value if previous else 0)
                    elif setup == 2:
                        value = a.value <= b.value + (diff.value if previous else 0)
                    elif setup == 3:
                        value = a.value >= b.value - (diff.value if previous else 0)
                    else:
                        raise AssertionError((key, setup))
                    if good:
                        self.state[key] = value
                    result, output = Value(value, good), 85
                elif cid == 562:
                    selector = get(961)
                    choices = [int(v.text) for v in p(o, 2381)]
                    selected = choices[int(bool(selector.value))]
                    result = get(7000+selected)
                    result, output = Value(result.value, selector.reliable and result.reliable), 85
                elif cid == 558:
                    mode = int(get(518).value)
                    a, duration, reset = get(513), get(1080), get(1082)
                    good = a.reliable and duration.reliable and reset.reliable
                    st = self.state.setdefault(key, {'last': False, 'start': None, 'deadline': None, 'latched': False, 'pv': False, 'duration': None})
                    if good:
                        dur = min(3888000, max(1, float(duration.value)))
                        if reset.value:
                            st.update(start=None, deadline=None, latched=False, pv=False)
                        elif mode == 4:
                            if a.value:
                                if st['start'] is None or (st['duration'] is not None and st['duration'] != dur and not st['latched']):
                                    st['start'] = time
                                if time-st['start'] >= dur:
                                    st['latched'] = True
                            elif not st['latched']:
                                st['start'] = None
                            st['pv'] = st['latched']
                        elif mode == 2:
                            if (a.value and not st['last']) or (st['deadline'] is not None and time < st['deadline'] and st['duration'] != dur):
                                st['deadline'] = time+dur
                            st['pv'] = st['deadline'] is not None and time < st['deadline']
                        else:
                            raise AssertionError((key, mode))
                        st['last'], st['duration'] = bool(a.value), dur
                    left = 0
                    if mode == 4 and st['start'] is not None and not st['latched']:
                        left = max(0, float(duration.value)-(time-st['start']))
                    if mode == 2 and st['deadline'] is not None:
                        left = max(0, st['deadline']-time)
                    values[(j, 1081)] = Value(left, good)
                    result, output = Value(st['pv'], good), 85
                else:
                    raise AssertionError((key, cid))
                values[(j, output)] = result
                pending.remove(j)
                progress = True
            if not pending:
                break
            assert progress, ('unresolved dependency/cycle', [self.blocks[n].get('ref') for n in pending])
        assert not pending
        return {int(p(o, 3365).text): values[(j, 513)]
                for j, o in enumerate(self.blocks) if int(o.get('classid')) in [527, 529, 531]}


def validate(caf, manifest_path, report_path):
    manifest = json.loads(manifest_path.read_text())
    with ZipFile(caf) as z:
        assert z.testzip() is None
        xml = z.read(z.namelist()[0])
    root = E.fromstring(xml)
    objects = root.findall(N+'object')
    by = {o.get('ref'): o for o in objects}
    assert len(objects) == len(by) == manifest['object_count']
    assert hashlib.sha256(caf.read_bytes()).hexdigest() == manifest['output_sha256']
    graph_count, connection_count, type_checks = 0, 0, 0
    new_activities = set(manifest['activity_refs'].values())

    def descriptor(o, port):
        if int(o.get('classid')) in [526, 527, 528, 529, 530, 531]:
            return o
        children = [c for ref, c in by.items() if ref.rsplit('.', 1)[0] == o.get('ref')
                    and p(c, 3365) is not None and int(p(c, 3365).text) == port]
        assert len(children) == 1, (o.get('ref'), port)
        return children[0]

    for ref, o in by.items():
        assert int(o.get('objectid')) < 4194303
        for node in o.iter():
            if node.text and node.text.startswith('8-1/'):
                assert node.text in by, (ref, node.text)
        blocks = p(o, 3375)
        if blocks is None:
            continue
        order, pos, wires, meta = [p(o, v) for v in [3117, 3383, 3118, 3384]]
        if any(v is None for v in [order, pos, wires, meta]):
            continue
        graph_count += 1
        connection_count += len(wires)
        assert len(blocks) == len(order) == len(pos)
        assert sorted(int(v.text) for v in order) == list(range(len(blocks)))
        assert len(wires) == len(meta)
        blockrefs = refs(o)
        assert all(r in by for r in blockrefs)
        for a, b, c, d in edges(o):
            assert 0 <= a < len(blocks) and 0 <= c < len(blocks)
            changed_main = ref == '8-1/575_1' and (a >= 106 or c >= 106)
            if ref in new_activities or changed_main:
                at, bt = port_type(descriptor(by[blockrefs[a]], b)), port_type(descriptor(by[blockrefs[c]], d))
                assert at == bt, (ref, a, b, c, d, at, bt)
                type_checks += 1
        if ref in new_activities:
            exported = [int(v.text) for v in p(o, 3184)]
            assert len(exported) == len(set(exported))
            assert set(exported) == {int(p(c, 3365).text) for r, c in by.items()
                                     if r.rsplit('.', 1)[0] == ref and p(c, 3365) is not None}

    sensors = [o for o in objects if o.get('classid') == '910']
    assert sorted(int(p(o, 2858).text) for o in sensors) == [199, 200, 201]
    assert p(by['8-1/575_1.2_300134'], 3113).text == '3600'
    assert int(p(by['8-1/575_1.536_62854.19_160084'], 3113).text) == 0

    base = {'t': 37.5, 'rh': 85, 'co2': 700, 'hsp': 35, 'csp': 40, 'rhsp': 85,
            'occ': 0, 'master': 1, 'sfproof': 1, 'smoke': 0, 'lowtemp': 0, 'highstatic': 0,
            'rotation': 0, 'dat': 37.5, 'pcct': 41}
    interface_by_ref = {v['object_ref']: v for v in manifest['interfaces'] if v['direction'] == 'input'}
    for key, data in manifest['coordinator_inputs'].items():
        if key not in base:
            base[key] = interface_by_ref[data['source_ref']]['default']
    c_ref = manifest['activity_refs']['AHU DEMAND AND CIP']
    g_ref = manifest['activity_refs']['AHU OUTPUT INTERLOCKS']
    out_ports = {k: v['port'] for k, v in manifest['coordinator_outputs'].items()}
    tests = []

    class Scenario:
        def __init__(self, **updates):
            self.runtime = Runtime(by, c_ref)
            self.env = copy.deepcopy(base)
            self.env.update(updates)
        def step(self, time, **updates):
            self.env.update(updates)
            mapped = {data['port']: self.env[key] for key, data in manifest['coordinator_inputs'].items()}
            raw = self.runtime.step(time, mapped)
            return {key: raw[port] for key, port in out_ports.items()}

    def assert_value(output, key, expected):
        actual = output[key]
        assert actual.reliable, (key, 'unreliable', actual)
        assert actual.value == expected, (key, actual.value, expected)
    def passed(name):
        tests.append({'name': name, 'result': 'PASS'})
    def ready(**updates):
        scenario = Scenario(**updates)
        scenario.step(0)
        scenario.step(3600)
        return scenario

    s = Scenario()
    o = s.step(0)
    for key, val in [('permit', False), ('cip', True), ('efpercent', 100)]: assert_value(o, key, val)
    assert_value(s.step(3599), 'permit', False)
    o = s.step(3600)
    for key, val in [('cip', False), ('permit', False), ('refrig', True), ('mid', 37.5), ('rhcontrol', 84.5)]: assert_value(o, key, val)
    passed('Startup hold lasts at least one hour; satisfied occupied zone requests refrigeration')
    s = ready()
    assert_value(s.step(3601, t=42), 'cool', True)
    assert_value(s.step(3602, t=40), 'permit', True)
    assert_value(s.step(3603, t=38), 'cool', True)
    o = s.step(3604, t=37.9)
    assert_value(o, 'cool', False); assert_value(o, 'permit', False)
    passed('Cooling starts at 42 F, holds through 40/38, resets below 38 with native GTE differential semantics')
    s = ready()
    assert_value(s.step(3601, t=33), 'heat', True)
    assert_value(s.step(3602, t=35), 'permit', True)
    assert_value(s.step(3603, t=37), 'heat', True)
    assert_value(s.step(3604, t=37.1), 'heat', False)
    passed('Heating starts at 33 F, holds through 35/37, resets above 37 with native LTE differential semantics')
    s = ready()
    assert_value(s.step(3601, rh=90), 'rh', True)
    assert_value(s.step(3602, rh=85.1), 'permit', True)
    assert_value(s.step(3603, rh=84.9), 'rh', False)
    passed('RH starts at 90%, clears below 85%; inner target crosses the reset edge')
    s = ready()
    assert_value(s.step(3601, co2=1000), 'co2', True)
    assert_value(s.step(3602, co2=950), 'co2', True)
    assert_value(s.step(3603, co2=899), 'co2', False)
    passed('Occupied CO2 starts at 1000 ppm, clears below 900 ppm')
    s = ready(occ=1)
    assert_value(s.step(3601, co2=1200), 'permit', False)
    o = s.step(3602, t=43)
    assert_value(o, 'permit', True); assert_value(o, 'control_occ', 0)
    passed('Unoccupied temperature demand runs; CO2-only demand does not start an unoccupied zone')
    s = ready(t=43)
    assert_value(s.step(3601), 'permit', True)
    o = s.step(3602, cip=True)
    assert_value(o, 'permit', False); assert_value(o, 'efpercent', 100)
    s.step(7202, cip=False)
    assert_value(s.step(10801), 'permit', False)
    assert_value(s.step(10802), 'permit', True)
    passed('CIP immediately stops normal run and the hour begins at completion, not CIP start')
    s = ready(t=43)
    s.step(3601, cip=True); s.step(3700, cip=False)
    s.step(7000, cip=True); s.step(7100, cip=False)
    assert_value(s.step(10699), 'permit', False)
    assert_value(s.step(10700), 'permit', True)
    passed('Repeated CIP resets the hold from the latest completion')
    s = ready(t=43, ciptime=30)
    s.step(3601, cip=True); s.step(3602, cip=False)
    assert_value(s.step(3632), 'permit', False)
    assert_value(s.step(7202), 'permit', True)
    passed('Operator hold value below one hour is clamped to 3600 seconds')
    s = ready(occ=1)
    assert_value(s.step(3601, on=True), 'permit', True)
    assert_value(s.step(3601.1, on=False), 'on', True)
    assert_value(s.step(7201), 'permit', False)
    passed('Momentary On override starts an unoccupied satisfied unit and expires')
    s = ready(t=43)
    assert_value(s.step(3601, off=True), 'permit', False)
    s.step(3601.1, off=False)
    assert_value(s.step(7200), 'permit', False)
    assert_value(s.step(7201), 'permit', True)
    passed('Timed Off override suppresses demand, then returns to automatic demand')
    s = ready(t=43)
    s.step(3601, off=True); s.step(3601.1, off=False)
    assert_value(s.step(3602, on=True), 'permit', True)
    passed('On request cancels an earlier timed Off override')
    s = ready(t=43)
    assert_value(s.step(3601, on=True, off=True), 'permit', False)
    o = s.step(3601.1, on=False, off=False)
    assert_value(o, 'off', True); assert_value(o, 'on', False)
    assert_value(s.step(3602, cancel=True), 'permit', True)
    passed('Simultaneous On/Off gives Off priority; Cancel returns to automatic')
    for mode in ['warmup', 'cooldown', 'setup']:
        s = ready(occ=1)
        o = s.step(3601, **{mode: True})
        assert_value(o, 'permit', True); assert_value(o, mode, True)
    passed('Selected Warmup, Cooldown and Setup force fan operation with common supplied thermal settings')
    s = ready(t=43)
    o = s.step(3601, lowtemp=1)
    assert_value(o, 'permit', False); assert_value(o, 'safety', True); assert_value(o, 'enable', 1)
    assert_value(s.step(3602, lowtemp=0, master=0, on=True), 'permit', False)
    passed('Safety and master shutdown defeat run overrides; native safety control remains enabled for valve protection')
    for key in ['t', 'rh', 'co2', 'dat', 'pcct', 'master', 'sfproof']:
        s = ready(t=43)
        o = s.step(3601, **{key: Value(s.env[key], False)})
        assert_value(o, 'sensorfault', True); assert_value(o, 'permit', False)
    passed('Measurement/master/fan-proof reliability faults produce a reliable closed run permission')
    s = ready(t=43)
    o = s.step(3601, cip=Value(False, False))
    assert_value(o, 'permit', False); assert_value(o, 'cip', True); assert_value(o, 'efpercent', 100)
    s.step(3602, cip=False)
    assert_value(s.step(7201), 'permit', False)
    assert_value(s.step(7202), 'permit', True)
    passed('Unreliable CIP fails active and recovery starts a new full hour')
    for updates in [{'tdiff': 0}, {'hsp': 39}, {'sfpercent': 101}, {'rhband': 0}, {'co2diff': 0}]:
        s = ready(t=43)
        o = s.step(3601, **updates)
        assert_value(o, 'paramfault', True); assert_value(o, 'permit', False)
    passed('Invalid separation, differentials and fan speed stop normal operation')
    s = ready(rh=91)
    assert_value(s.step(3601), 'desiccant', True)
    o = s.step(3602, rotation=1)
    assert_value(o, 'rotationfault', True); assert_value(o, 'desiccant', False)
    passed('Rotation fault inhibits the exposed OEM desiccant request')

    # Run the final-output graph against simulated native controller outputs.
    def gates(coordinator, **updates):
        data = {'permit': coordinator['permit'], 'safety': coordinator['safety'],
                'cool': coordinator['cool'], 'heat': coordinator['heat'], 'rh': coordinator['rh'],
                'fanproof': 1, 'fancmd': 1, 'speed': 50, 'clgraw': 70,
                'htgraw': 60, 'pclgraw': 80, 'oadraw': 100}
        data.update(updates)
        inputs = {v['port']: data[k] for k, v in manifest['gate_inputs'].items()}
        values = Runtime(by, g_ref).step(0, inputs)
        return {key: values[port] for key, port in manifest['gate_outputs'].items()}
    s = ready(t=43)
    run = s.step(3601)
    o = gates(run)
    for key, val in [('fancmd', 1), ('speed', 50), ('oad', 100), ('clg', 70), ('pclg', 80), ('htg', 0)]: assert_value(o, key, val)
    for options in [{'fanproof': 0}, {'fanproof': Value(1, False)}, {'fancmd': Value(1, False)}]:
        o = gates(run, **options)
        for key in ['clg', 'pclg', 'htg']: assert_value(o, key, 0)
    passed('Normal cooling outputs pass; absent/unreliable fan proof or command blocks all normal coils')
    s = ready(t=43)
    blocked = s.step(3601, cip=True)
    o = gates(blocked, clgraw=Value(70, False), fancmd=Value(1, False))
    for key in ['fancmd', 'speed', 'oad', 'clg', 'pclg', 'htg']: assert_value(o, key, 0)
    passed('CIP output shutdown remains reliable even when native fan/valve signals are unreliable')
    s = ready(t=43)
    fault = s.step(3601, lowtemp=1)
    o = gates(fault)
    for key in ['fancmd', 'speed', 'oad']: assert_value(o, key, 0)
    for key, val in [('clg', 70), ('pclg', 80), ('htg', 60)]: assert_value(o, key, val)
    passed('During safety trip the fan/OAD stop while native safety valve commands pass through')

    result = {'status': 'STATIC AND DOCUMENTED-BEHAVIOR MODEL CHECKS PASS; CCT NOT EXECUTED',
              'caf_sha256': manifest['output_sha256'], 'objects': len(objects),
              'diagrams_checked': graph_count, 'connections_checked': connection_count,
              'new_or_redirected_wire_type_checks': type_checks, 'scenario_groups': len(tests),
              'scenarios': tests,
              'limits': ['CCT opening/compiler/device memory not checked',
                         'Existing PID/FSM and actuator behavior not executed',
                         'Native timer setup names and MUX reliability behavior must be verified in CCT',
                         'Provisional coil and fan defaults require design/commissioning review']}
    report_path.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    validate(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
