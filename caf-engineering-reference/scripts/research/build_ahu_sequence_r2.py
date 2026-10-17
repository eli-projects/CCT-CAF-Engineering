#!/usr/bin/env python3
"""Build the AHU-1 sequence R2 candidate with native graphical records."""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from caf_native_builder_r2 import *

def build(src, output, manifest_path, expected_sha):
    assert hashlib.sha256(src.read_bytes()).hexdigest() == expected_sha
    with ZipFile(src) as z:
        assert z.testzip() is None and len(z.infolist()) == 1
        info, comment = z.infolist()[0], z.comment
        original = z.read(info.filename)
    old = parse(original)
    raw = {m.group(1).decode(): m.group(0) for m in re.finditer(rb'<object\s+ref="([^"]+)"[^>]*>.*?</object>', original, re.S)}
    lib = Library(old)
    main = copy.deepcopy(old[MAIN])
    top_blocks = [MAIN + f".{p.get('id')}_{p.text}" for p in prop(main, 3375)]
    main_edges = [[int(v.text) for v in row.iter(N + 'unsignedShort')] for row in prop(main, 3118)]
    main_meta = [copy.deepcopy(v) for v in prop(main, 3384)]
    old_main_edges = copy.deepcopy(main_edges)
    parameter_patches = {}
    changes = []

    def add_top(obj):
        assert obj.get('ref') not in top_blocks
        top_blocks.append(obj.get('ref'))
        prop(main, 3375).append(copy.deepcopy(prop(obj, 75)))
        prop(main, 3117).append(nv('unsignedShort', len(top_blocks)-1))
        is_input = obj.get('classid') in ['526', '528', '530']
        prop(main, 3383).append(lib.layout(obj, -1900 if is_input else 600, (len(top_blocks)-106)*80))

    def main_link(sig, dest, port, replace=False, reason=''):
        s, d = top_blocks.index(sig.obj.get('ref')), top_blocks.index(dest.get('ref'))
        matching = [i for i, e in enumerate(main_edges) if e[2:] == [d, port]]
        assert len(matching) <= 1, (dest.get('ref'), port, matching)
        if matching:
            assert replace, (reason, dest.get('ref'), port)
            i = matching[0]
            previous = main_edges[i]
            main_edges[i] = [s, sig.port, d, port]
            changes.append({'type': 'wire_redirect', 'index': i, 'old': previous,
                            'new': main_edges[i], 'destination_ref': dest.get('ref'),
                            'reason': reason})
        else:
            main_edges.append([s, sig.port, d, port])
            main_meta.append(metadata())
            changes.append({'type': 'wire_add', 'wire': main_edges[-1], 'reason': reason})

    def set_existing(ref, pid, value, reason):
        previous = parameter_patches.get(ref, raw[ref])
        o = copy.deepcopy(old[ref])
        # Replace only the selected property bytes; also remove stale stored
        # simulation overrides for that property so tests start from the new value.
        if prop(o, pid) is None:
            set_prop(o, pid, value)
            m = re.search(rb'</object>$', previous)
            assert m is not None
            p = o.find(f"{N}property[@id='{pid}']")
            previous = previous[:m.start()] + bare_bytes(p) + previous[m.start():]
        else:
            previous = replace_property_bytes(previous, pid, value)
        previous = re.sub(rb'<simulationProperty id="' + str(pid).encode() + rb'">.*?</simulationProperty>', b'', previous, flags=re.S)
        parameter_patches[ref] = previous
        changes.append({'type': 'property', 'ref': ref, 'property': pid,
                        'value': ' '.join(value.itertext()), 'reason': reason})

    params = {}
    definitions = [
        ('cip', 'CIP-REQ', BOOL, False, 'Maintained CIP active. Clearing this request is interpreted as cleaning complete.'),
        ('on', 'UNIT-ON-REQ', BOOL, False, 'Momentary timed unit On request; pulse true then false.'),
        ('off', 'UNIT-OFF-REQ', BOOL, False, 'Momentary timed unit Off request; pulse true then false. Off wins if both requests are asserted.'),
        ('cancel', 'UNIT-OVR-CANCEL', BOOL, False, 'Reset both timed unit overrides and return to automatic operation.'),
        ('warmup', 'WARMUP-REQ', BOOL, False, 'Maintained occupant-selected Warmup request. Forces fan, using the supplied common thermal settings.'),
        ('cooldown', 'COOLDOWN-REQ', BOOL, False, 'Maintained occupant-selected Cooldown request. Forces fan, using the supplied common thermal settings.'),
        ('setup', 'SETUP-REQ', BOOL, False, 'Maintained occupant-selected Setup request. Forces fan, using the supplied common thermal settings.'),
        ('tdiff', 'TEMP-DIFF', Type('float', units=64), 2, 'Temperature start offset; reset span is twice this value. Default 2 F.'),
        ('rhband', 'RH-BAND', Type('float', units=29), 5, 'Humidity start offset above DEHUM-SP; returns below DEHUM-SP.'),
        ('co2sp', 'CO2-SP', Type('float', units=96), 1000, 'CO2 ventilation start threshold.'),
        ('co2diff', 'CO2-DIFF', Type('float', units=96), 100, 'CO2 reset differential; default clears below 900 ppm.'),
        ('ciptime', 'CIP-HOLD-TIME', Type('float', units=73), 3600, 'Post-CIP/restart hold. Logic enforces a minimum of 3600 seconds.'),
        ('ovrtime', 'UNIT-OVRTIME', Type('float', units=73), 3600, 'Duration for separate timed On and Off overrides.'),
        ('sfpercent', 'SF-RUN-%', Type('float', units=98), 50, 'Fixed commissioned VFD speed while running; provisional initial value equals the old fixed-value parameter.'),
        ('pccsp', 'PCC-T-SP', Type('float', units=64), 41, 'Provisional pre-cooling discharge target. Confirm against coil/OEM design.'),
        ('datclg', 'DAT-CLG-SP', Type('float', units=64), 35, 'Provisional cooling discharge reset minimum for the refrigerated space.'),
        ('dathtg', 'DAT-HTG-SP', Type('float', units=64), 60, 'Provisional heating discharge reset maximum.'),
        ('datll', 'DAT-LOW-LIM', Type('float', units=64), 34, 'Provisional analog reheat low-limit target; mechanical LT-A protection is preserved.'),
        ('datllband', 'DAT-LL-BAND', Type('float', units=64), 1, 'Provisional low-limit proportional band for refrigerated-room operation.'),
    ]
    for key, name, typ, default, desc in definitions:
        params[key] = lib.main_input(name, typ, default, desc)
        add_top(params[key].obj)

    c = lib.new_activity('AHU DEMAND AND CIP')
    inputs, sources = {}, {}

    def inp(key, name, source):
        sources[key] = source
        inputs[key] = c.input(name, source.type)
        return inputs[key]

    existing = {
        't': (MAIN + '.536_86471', 8000), 'rh': (MAIN + '.536_86472', 8000),
        'co2': (MAIN + '.536_86473', 8000),
        'hsp': (MAIN + '.523_52062', 3100), 'csp': (MAIN + '.523_52062', 3101),
        'rhsp': (MAIN + '.2_305', 663), 'occ': (MAIN + '.524_51131', 50032),
        'master': (MAIN + '.19_300126', 663),
        'sfproof': (MAIN + '.556_1095', 8000), 'smoke': (MAIN + '.556_1015', 8000),
        'lowtemp': (MAIN + '.556_1053', 8000), 'highstatic': (MAIN + '.556_1044', 8000),
        'rotation': (MAIN + '.556_299966', 8000),
        'dat': (MAIN + '.556_1019', 8000), 'pcct': (MAIN + '.556_299960', 8000),
    }
    for key, (ref, port) in existing.items():
        inp(key, key.upper(), lib.existing_signal(ref, port))
    for key in ['cip', 'on', 'off', 'cancel', 'warmup', 'cooldown', 'setup', 'tdiff', 'rhband',
                'co2sp', 'co2diff', 'ciptime', 'ovrtime', 'sfpercent']:
        inp(key, params[key].obj.find(f"{N}property[@id='2390']/{N}data/{N}string").text, params[key])
    i = dict(inputs)
    i['cip'] = c.safe_bool(i['cip'], True, 'CIP Fail To Active')

    # Per-sequence temperature requests are latched using native hysteretic
    # comparisons. Standard CCT inequality rules apply at the exact reset edge.
    span = c.math('mul', i['tdiff'], 2, 'Temperature Reset Span')
    cool_start = c.math('add', i['csp'], i['tdiff'], 'Cooling Start Threshold')
    heat_start = c.math('sub', i['hsp'], i['tdiff'], 'Heating Start Threshold')
    cool = c.compare('gte', i['t'], cool_start, span, 'Cooling Request')
    heat = c.compare('lte', i['t'], heat_start, span, 'Heating Request')
    rh_start = c.math('add', i['rhsp'], i['rhband'], 'Humidity Start Threshold')
    rh = c.compare('gte', i['rh'], rh_start, i['rhband'], 'Humidity Request')
    co2_raw = c.compare('gte', i['co2'], i['co2sp'], i['co2diff'], 'CO2 Hysteresis')
    occupied = c.enum_bool(i['occ'], {0, 2}, 'Occupied Or Bypass')
    co2 = c.logic('and', co2_raw, occupied, name='Eligible CO2 Demand')
    automatic = c.logic('or', cool, heat, rh, co2, name='Any Automatic Demand')
    master = c.enum_bool(i['master'], {1}, 'Master Enabled')
    sf_proven = c.enum_bool(i['sfproof'], {1}, 'Supply Fan Proven')
    alarm = [c.safe_bool(c.enum_bool(i[k], {1}, k.upper() + ' Alarm'), False,
                         k.upper() + ' Confirmed Alarm') for k in ['smoke', 'lowtemp', 'highstatic']]
    safety = c.logic('or', *alarm, name='Safety Trip')
    rotation_fault = c.enum_bool(i['rotation'], {1}, 'Desiccant Rotation Fault')

    quality = [c.reliability(value, key.upper() + ' Reliable') for key, value in inputs.items()]
    sensor_fault = c.logic('not', c.logic('and', *quality, name='Required Inputs Reliable'), name='Input Reliability Fault')
    gap = c.math('sub', i['csp'], i['hsp'], 'Setpoint Separation')
    required_gap = c.math('add', span, 1, 'Minimum Setpoint Separation')
    bad_gap = c.compare('lt', gap, required_gap, name='Setpoint Overlap Fault')
    bad_tdiff = c.compare('lte', i['tdiff'], 0, name='Bad Temperature Differential')
    bad_rhband = c.compare('lte', i['rhband'], 0, name='Bad RH Differential')
    bad_co2diff = c.compare('lte', i['co2diff'], 0, name='Bad CO2 Differential')
    bad_speed = c.logic('or', c.compare('lte', i['sfpercent'], 0), c.compare('gt', i['sfpercent'], 100), name='Bad Fan Speed')
    parameter_fault = c.logic('or', bad_gap, bad_tdiff, bad_rhband, bad_co2diff, bad_speed, name='Parameter Fault')

    hold_time = c.math('min', c.math('max', i['ciptime'], 3600), 3888000, 'Effective CIP Hold')
    cip_clear = c.logic('not', i['cip'], name='CIP Complete')
    ready, remaining = c.timer(cip_clear, hold_time, i['cip'], 4, 'CIP Clear On Delay With Memory')
    cip_block = c.logic('or', i['cip'], c.logic('not', ready), name='CIP Or Restart Hold')
    # Restart initializes this native timer to false: a full hold is required
    # after any restart, even if the previous cleaning state is unknown.
    override_time = c.math('min', c.math('max', i['ovrtime'], 5), 3888000, 'Effective Override Duration')
    on_reset = c.logic('or', i['cancel'], i['off'], name='On Override Reset')
    off_reset = c.logic('or', i['cancel'], c.logic('and', i['on'], c.logic('not', i['off'])), name='Off Override Reset')
    on_active, _ = c.timer(i['on'], override_time, on_reset, 2, 'Timed Unit On')
    off_active, _ = c.timer(i['off'], override_time, off_reset, 2, 'Timed Unit Off')
    mode_fan = c.logic('or', i['warmup'], i['cooldown'], i['setup'], name='Selected Mode Fan Request')
    demand = c.logic('or', automatic, on_active, mode_fan, name='Resolved Run Request')
    permit = c.logic('and', demand, master, ready, c.logic('not', i['cip']),
                     c.logic('not', off_active), c.logic('not', safety),
                     c.logic('not', sensor_fault), c.logic('not', parameter_fault), name='AHU Run Permission')
    permit = c.safe_bool(permit, False, 'Run Permission Fails Closed')
    # Keep the native safety sequence enabled during a trip so its valve
    # protection can act. Final fan/damper permission remains false.
    native_enable = c.logic('or', permit, safety, name='Native Safety Control Permission')
    enable_state = c.select(native_enable, 0, 1, ENABLE, 'Shutdown Or Enable')
    control_occ = c.select(permit, 1, 0, OCC, 'Control Occupancy While Running')
    neutral = c.math('div', c.math('add', i['hsp'], i['csp']), 2, 'Zone Recovery Control Target')
    rh_control = c.math('sub', i['rhsp'], .5, 'Humidity Recovery Control Target')
    neutral.type = Type('float', units=64)
    rh_control.type = Type('float', units=29)
    refrigerate = c.logic('and', occupied, master, c.logic('not', automatic), c.logic('not', cip_block),
                          c.logic('not', on_active), c.logic('not', off_active), c.logic('not', mode_fan),
                          c.logic('not', safety), c.logic('not', sensor_fault), c.logic('not', parameter_fault),
                          name='Refrigeration Request')
    desiccant = c.logic('and', permit, rh, sf_proven, c.logic('not', rotation_fault), name='OEM Desiccant Request')
    warm_act = c.logic('and', permit, i['warmup'])
    cold_act = c.logic('and', permit, i['cooldown'], c.logic('not', i['warmup']))
    setup_act = c.logic('and', permit, i['setup'], c.logic('not', i['warmup']), c.logic('not', i['cooldown']))
    heating_allowed = c.logic('and', permit, heat)

    out = {}
    output_defs = [
        ('permit', 'AHU-RUN-REQ', permit, 'Resolved run permission after CIP, safety, master, override and input/parameter checks.'),
        ('enable', 'AHU-ENABLE', enable_state, 'Enable native control for valid running or safety-valve protection. AHU-RUN-REQ separately gates fan/damper.'),
        ('control_occ', 'CONTROL-OCC', control_occ, 'Internal control occupancy; actual EFF-OCC and sensor displays remain independent.'),
        ('cool', 'CLG-REQ', cool, 'Hysteretic temperature cooling request.'),
        ('heat', 'HTG-REQ', heat, 'Hysteretic temperature heating request.'),
        ('rh', 'RH-REQ', rh, 'Humidity request; starts at DEHUM-SP plus RH-BAND, resets below DEHUM-SP.'),
        ('co2', 'CO2-REQ', co2, 'Occupied/Bypass-eligible ventilation demand.'),
        ('cip', 'CIP-BLOCK', cip_block, 'Cleaning or full post-cleaning/restart hold active.'),
        ('cipremain', 'CIP-TIME-LEFT', remaining, 'Native timer remaining seconds.'),
        ('on', 'UNIT-ON-ACT', on_active, 'Timed unit On override active.'),
        ('off', 'UNIT-OFF-ACT', off_active, 'Timed unit Off override active.'),
        ('ef', 'EF-PURGE-REQ', cip_block, 'Supervisory request to run the dedicated exhaust fan during CIP/hold; external mapping required.'),
        ('efpercent', 'EF-PURGE-%', c.select(cip_block, 0, 100, Type('float', units=98)), 'Supervisory exhaust speed request, 100% during CIP/hold.'),
        ('refrig', 'REFRIG-REQ', refrigerate, 'Supervisory refrigeration-mode request when occupied conditions are satisfied; external mapping required.'),
        ('desiccant', 'DESICCANT-REQ', desiccant, 'OEM dehumidification request; no physical desiccant output is defined in the drawings.'),
        ('sensorfault', 'INPUT-FAULT', sensor_fault, 'Required input reliability failure.'),
        ('paramfault', 'PARAM-FAULT', parameter_fault, 'Invalid control separation/differential/fan-speed setting.'),
        ('safety', 'SAFETY-TRIP', safety, 'Any smoke, low-temperature or high-static alarm.'),
        ('rotationfault', 'DESICCANT-FAULT', rotation_fault, 'Rotation fault monitoring; inhibits the OEM request.'),
        ('mid', 'ZN-RECOVERY-SP', neutral, 'Common inner-loop target between the heat and cool stop thresholds.'),
        ('rhcontrol', 'RH-RECOVERY-SP', rh_control, 'Inner humidity target 0.5 percentage point below the humidity request reset threshold.'),
        ('warmup', 'WARMUP-ACT', warm_act, 'Warmup request selected and run permitted.'),
        ('cooldown', 'COOLDOWN-ACT', cold_act, 'Cooldown request selected and run permitted.'),
        ('setup', 'SETUP-ACT', setup_act, 'Setup request selected and run permitted.'),
        ('heatrun', 'HTG-RUN-REQ', heating_allowed, 'Permitted heating request to native startup logic.'),
    ]
    for key, label, signal, desc in output_defs:
        out[key] = c.output(label, signal, desc)
    c.finish()
    add_top(c.obj)
    for source_key, port in zip(sources, c.inputs):
        main_link(sources[source_key], c.obj, int(prop(port, 3365).text), reason='New demand/CIP input')

    # Physical-output interlocks preserve native thermal/PID control. Native
    # safety valve commands pass through on a safety trip; the fan and OAD are
    # forced off/closed. Normal thermal commands require fan proof and demand.
    g = lib.new_activity('AHU OUTPUT INTERLOCKS')
    gate_sources = {'permit': out['permit'], 'safety': out['safety'], 'cool': out['cool'], 'heat': out['heat'], 'rh': out['rh'],
                    'fanproof': lib.existing_signal(MAIN + '.556_1095', 8000),
                    'fancmd': lib.existing_signal(MAIN + '.536_86465', 8000),
                    'speed': params['sfpercent'],
                    'clgraw': lib.existing_signal(MAIN + '.536_83798', 8000),
                    'htgraw': lib.existing_signal(MAIN + '.536_83810', 8001),
                    'pclgraw': lib.existing_signal(MAIN + '.536_86466', 8000),
                    'oadraw': lib.existing_signal(MAIN + '.536_86465', 8002)}
    gi = {key: g.input(key.upper(), sig.type) for key, sig in gate_sources.items()}
    raw_fan_on = g.safe_bool(g.enum_bool(gi['fancmd'], {1}, 'Native Fan On'), False, 'Native Fan Command Fails Closed')
    proof = g.enum_bool(gi['fanproof'], {1}, 'Physical Fan Proof')
    proof = g.safe_bool(proof, False, 'Fan Proof Fails Closed')
    final_fan_on = g.logic('and', gi['permit'], raw_fan_on)
    speed = g.math('min', g.math('max', gi['speed'], 0), 100, 'Clamped Fan Run Percent')
    cooling_allow = g.logic('and', final_fan_on, proof, g.logic('or', gi['cool'], gi['rh']))
    heating_allow = g.logic('and', final_fan_on, proof, g.logic('or', gi['heat'], gi['rh']))
    gated = {}
    gated['fancmd'] = g.output('SF-FINAL-C', g.select(final_fan_on, 0, 1, OFFON), 'Final fan command through native damper/start sequence and new permission.')
    gated['speed'] = g.output('SF-FINAL-%', g.select(final_fan_on, 0, speed, Type('float', units=98)), 'Fixed commissioned speed while the final fan command is On.')
    gated['oad'] = g.output('OAD-FINAL-%', g.select(gi['permit'], 0, gi['oadraw'], Type('float', units=98)), 'Native damper positioning while permitted; otherwise closed.')
    for key, rawkey, allow, label in [('clg', 'clgraw', cooling_allow, 'CLG-FINAL-%'),
                                       ('pclg', 'pclgraw', cooling_allow, 'PCLG-FINAL-%'),
                                       ('htg', 'htgraw', heating_allow, 'HTG-FINAL-%')]:
        ordinary = g.select(gi['permit'], 0, g.select(allow, 0, gi[rawkey]), name='Normal Run Permission Gate')
        final = g.select(gi['safety'], ordinary, gi[rawkey], Type('float', units=98), name='Preserve Native Safety Valve Command')
        gated[key] = g.output(label, final, 'Normal operation requires permission, fan proof and demand. Native safety command takes priority.')
    g.finish()
    add_top(g.obj)
    for key, port in zip(gate_sources, g.inputs):
        main_link(gate_sources[key], g.obj, int(prop(port, 3365).text), reason='Final output interlock input')

    # Complete supported physical wiring and replace the legacy enable source.
    main_link(out['enable'], old[MAIN + '.536_86467'], 7000, replace=True, reason='Demand/CIP/override resolution before native unit enable')
    main_link(lib.existing_signal(MAIN + '.556_1015', 8000), old[MAIN + '.536_81027'], 7002, reason='Connect discharge smoke to unused native Safety Switch 2')
    main_link(lib.existing_signal(MAIN + '.556_299960', 8000), old[MAIN + '.536_86466'], 7001, reason='Use actual pre-cooling discharge temperature feedback')
    main_link(params['pccsp'], old[MAIN + '.536_86466'], 7002, reason='Separate precooling target')
    main_link(lib.existing_signal(MAIN + '.556_1019', 8000), old[MAIN + '.536_83810'], 7003, reason='Actual temperature for the native reheat low-limit path')
    main_link(params['datll'], old[MAIN + '.536_83810'], 7004, reason='Refrigerated-space low-limit parameter')
    main_link(params['datllband'], old[MAIN + '.536_83810'], 7015, reason='Refrigerated-space low-limit proportional band')
    for ref, port in [(MAIN + '.536_83798', 7004), (MAIN + '.536_86466', 7004), (MAIN + '.536_82885', 7003)]:
        main_link(out['rhcontrol'], old[ref], port, replace=True, reason='Humidity recovery target permits request to reset')
    for ref, ports in [(MAIN + '.536_83757', [7002, 7003]), (MAIN + '.536_83759', [7001, 7002])]:
        for port in ports:
            main_link(out['mid'], old[ref], port, replace=True, reason='Inner temperature loop drives across the request reset edge')
    main_link(params['datclg'], old[MAIN + '.536_83757'], 7006, reason='Refrigerated-room cooling discharge reset minimum')
    main_link(params['dathtg'], old[MAIN + '.536_83757'], 7004, reason='Refrigerated-room heating discharge reset maximum')
    main_link(out['mid'], old[MAIN + '.536_83757'], 7005, reason='Neutral discharge target follows the effective room setpoints')
    for ref, port in [(MAIN + '.540_10001', 7015), (MAIN + '.536_81052', 7000),
                      (MAIN + '.536_81051', 7000), (MAIN + '.536_85858', 7001)]:
        main_link(out['control_occ'], old[ref], port, replace=True, reason='Cycle on custom demand without an occupied/unused-unoccupied fan lockout')
    main_link(out['permit'], old[MAIN + '.536_62854'], 7002, replace=True, reason='Start native fan sequence for every valid demand including RH and CO2')
    main_link(out['heatrun'], old[MAIN + '.536_62854'], 7003, replace=True, reason='Permitted heat request to native startup logic')
    for key, ref in [('fancmd', '.555_2132'), ('speed', '.555_2133'), ('oad', '.555_299923'),
                     ('clg', '.555_2033'), ('htg', '.555_2114'), ('pclg', '.555_299730')]:
        main_link(gated[key], old[MAIN + ref], 7000, replace=True, reason='Apply final physical-output permission/safety gate')

    # Consistent refrigerated-space settings, including setpoint clamps and
    # stale simulation values. Preserve all hardware point identities/addresses.
    set_existing(MAIN + '.2_12', 3113, nv('float', 37.5), 'Central reference equals midpoint of 35/40 F defaults')
    set_existing(MAIN + '.2_305', 3113, nv('float', 85), 'Use configured RH setpoint and remove stale 50% simulation override')
    set_existing(MAIN + '.2_305', 117, nv('enum', 29, set=507), 'Relative humidity units')
    set_existing(MAIN + '.19_300126', 3113, nv('enum', 1, set=349), 'Match the declared Shutdown/Enable type')
    for oid, value in [(3474, 40), (3475, 35), (3476, 40), (3477, 35), (3478, 40), (3479, 35)]:
        set_existing(MAIN + f'.523_52062.2_{oid}', 3113, nv('float', value), 'Use supplied temperature range for every occupancy mode; no separate unoccupied settings specified')
    set_existing(MAIN + '.523_52062', 3109, nv('float', 32), 'Allow the refrigerated cooling setpoint below the comfort minimum')
    set_existing(MAIN + '.523_52062', 50107, nv('float', 32), 'Allow the refrigerated heating setpoint below the comfort minimum')
    set_existing(MAIN + '.523_52062.2_52077', 3113, nv('float', 37.5), 'Consistent central setpoint fallback')
    set_existing(MAIN + '.523_52062.2_52078', 3113, nv('float', 37.5), 'Consistent local setpoint fallback')
    set_existing(MAIN + '.536_62854.19_160084', 3113, nv('enum', 0, set=978), 'Fixed commissioned VFD speed: constant-capacity startup path, not an unconnected pressure loop')
    for ref, value in [(MAIN + '.536_69909.2_69912', 60), (MAIN + '.536_69909.2_69913', 35)]:
        # Find by port instead of assuming the optional module's point IDs.
        port = 7001 if value == 60 else 7002
        o = lib.get_port(old[MAIN + '.536_69909'], port)
        set_existing(o.get('ref'), 3113, nv('float', value), 'Matching unoccupied discharge fallback')

    set_prop(main, 3118, array('array', [edge(v) for v in main_edges]))
    set_prop(main, 3384, array('listof', main_meta))
    main_raw = raw[MAIN]
    for pid in [3375, 3117, 3383, 3118, 3384]:
        main_raw = replace_property_bytes(main_raw, pid, prop(main, pid))
    parameter_patches[MAIN] = main_raw

    def patch(match):
        return parameter_patches.get(match.group(1).decode(), match.group(0))
    xml = re.sub(rb'<object\s+ref="([^"]+)"[^>]*>.*?</object>', patch, original, flags=re.S)
    where = xml.index(b'<object ref="8-1/575_1.536_400008"')
    xml = xml[:where] + b''.join(bare_bytes(o) for o in lib.new.values()) + xml[where:]
    result = parse(xml)
    assert set(result) == set(old) | set(lib.new)
    for ref, o in old.items():
        if ref not in parameter_patches:
            assert E.tostring(result[ref]) == E.tostring(o), ref
    assert all(not o.get('ref').startswith('8-1/307_2.') for o in lib.new.values())
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'w') as z:
        z.comment = comment
        z.writestr(info, xml)
    with ZipFile(output) as z:
        assert z.testzip() is None and z.read(info.filename) == xml
    manifest = {
        'status': 'R2 SEQUENCE CANDIDATE WITH NATIVE GRAPHICAL RECORDS - CCT ACCEPTANCE PENDING',
        'input': str(src), 'input_sha256': expected_sha,
        'output': str(output), 'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'source_object_count': len(old), 'object_count': len(result),
        'added_object_count': len(lib.new), 'main_blocks': len(top_blocks),
        'main_connections': len(main_edges), 'modified_existing_objects': sorted(parameter_patches),
        'changes': changes, 'interfaces': lib.interfaces,
        'activity_refs': {a.name: a.ref for a in lib.activities},
        'coordinator_inputs': {key: {'source_ref': source.obj.get('ref'), 'source_port': source.port,
                                     'port': int(prop(port, 3365).text)}
                               for (key, source), port in zip(sources.items(), c.inputs)},
        'coordinator_outputs': {key: {'port': sig.port, 'name': output_defs[j][1]}
                                for j, (key, sig) in enumerate(out.items())},
        'gate_inputs': {key: {'source_ref': source.obj.get('ref'), 'source_port': source.port,
                            'port': int(prop(port, 3365).text)}
                        for (key, source), port in zip(gate_sources.items(), g.inputs)},
        'gate_outputs': {key: sig.port for key, sig in gated.items()},
        'native_operations': [op for a in lib.activities for op in a.operations],
        'layout_provenance': lib.layout_provenance,
        'assumptions': [
            'Heating 35 F/cooling 40 F are interpreted from the printed range, despite the room-name conflict.',
            'All occupancy modes keep these refrigerated-space settings because alternative unoccupied settings are absent.',
            'CIP-REQ clearing means cleaning complete.',
            'The minimum one-hour CIP hold is also applied after every controller restart; an exhaust-purge request is exported during that hold.',
            'RH demand begins at 90% and clears below 85%; inner RH target is 84.5% to cross the reset edge.',
            'CO2 starts at 1000 ppm and clears below 900 ppm while Occupied/Bypass.',
            'Warmup/Cooldown/Setup requests force fan with the common supplied thermal settings; distinct mode targets were not provided.',
            'VFD speed is fixed at an adjustable commissioned value, initially 50%; native constant-capacity startup is selected.',
            'PCC 41 F, cooling DAT 35 F, heating DAT 60 F and reheat analog low limit 34 F/band 1 F are provisional design-review values.',
            'CCT timer enum setup 2 is used for retriggerable pulses and 4 for on-delay-with-memory; verify their displayed names in CCT.',
            'Required zone/CO2/setpoint/master/CIP reliability faults stop normal operation; native safety valve commands retain priority.',
        ],
        'external_integration': ['Map EF-PURGE-REQ and EF-PURGE-% to the dedicated exhaust-fan controller.',
                                 'Map REFRIG-REQ to the refrigeration supervisory sequence.',
                                 'Confirm OEM desiccant command interface; DESICCANT-REQ has no invented physical output.',
                                 'Configure DLK HMI controls and Metasys trends/alarms/graphics.'],
        'validation_limit': 'Graph and independent behavior-model checks do not execute Johnson Controls CCT or its existing PID/FSM modules.',
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k: manifest[k] for k in ['status', 'output', 'output_sha256', 'object_count', 'added_object_count', 'main_blocks', 'main_connections']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--expected-source-sha', required=True)
    args = parser.parse_args()
    build(args.source, args.output, args.manifest, args.expected_source_sha)
