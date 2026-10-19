#!/usr/bin/env python3
"""Build a PARTIAL, offline CT CHWS candidate from the exact user CGE native.

Usage: python3 build_ct_chws_candidate.py SOURCE.caf REPO_ROOT OUTPUT_DIRECTORY
Requires lxml and the pinned CCT-CAF-Engineering repository references.
Missing physical inputs remain explicitly named SIM interfaces. No GUIDs or
unobserved Platinum signal encodings are manufactured. No native CCT is run.
"""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E

SOURCE_SHA = "e896bab23c944d08b3eb3e309cd813cd66b4b7ab0b22d3c2a4476c754eef76d2"
AHU_SHA = "078e1aa20f084e82212f205480f858bb17fad45a81081a74f74e4d429530bd26"
PINNED = {
    "caf_native_builder_r2.py": "43db5a0a22a757cd51545f7daa92acae94fc6b9375ee320e590348a564beb0d5",
    "make_ahu_three_tocc_candidate_r2.py": "b85833a2df8651dd8bbe9299c712a8420318aabb43d2da756f91b65cf49b3081",
}
COMMIT = "c715dbfe9f3f9bb2a38dbd631b797d8afbfbd598"

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def build(source, repo, out):
    assert digest(source) == SOURCE_SHA, "Wrong source; use the supplied CT CHWS.caf unchanged"
    scripts = repo / "caf-engineering-reference/scripts/research"
    for name, sha in PINNED.items():
        assert digest(scripts / name) == sha, "Reference helper differs: " + name
    ahu = repo / "caf-engineering-reference/examples/ahu-1/AHU-1_latest_AvgControlRedirect_VERIFIED-OPEN.caf"
    assert digest(ahu) == AHU_SHA
    sys.path.insert(0, str(scripts))
    import caf_native_builder_r2 as b
    import make_ahu_three_tocc_candidate_r2 as base
    N, MAIN, p, nv, setp = b.N, b.MAIN, b.prop, b.nv, b.set_prop
    with ZipFile(source) as z:
        assert z.testzip() is None and len(z.infolist()) == 1
        info, comment = z.infolist()[0], z.comment
        original = z.read(info.filename)
    old = b.parse(original)
    assert p(old["8-1"], 70).text == "M4-CGE09090-0"
    with ZipFile(ahu) as z:
        templates = b.parse(z.read(z.namelist()[0]))
    lib = b.Library(templates)
    lib.main_port = 7300
    lib.used_numbers.update(int(o.get("objectid")) for o in old.values())
    native = base.NativeClones(old)
    native.next_id = 900000
    native.used_numbers.update(lib.used_numbers)
    raw = {m.group(1).decode(): m.group(0) for m in re.finditer(
        rb'<object\s+ref="([^"]+)"[^>]*>.*?</object>', original, re.S)}
    patches, relocations, changes, mappings = {}, {}, [], []
    main = copy.deepcopy(old[MAIN])
    blocks = [MAIN + f".{x.get('id')}_{x.text}" for x in p(main, 3375)]
    edges = [[int(v.text) for v in row.iter(N + "unsignedShort")] for row in p(main, 3118)]
    metadata = [copy.deepcopy(x) for x in p(main, 3384)]
    original_edges = copy.deepcopy(edges)
    original_registry = [b.bare_bytes(p(main, n)) for n in (3926, 3927)]
    locations = {r: copy.deepcopy(x) for r, x in zip(blocks, p(main, 3383))}
    queued = []
    activity_bindings, activity_outputs = {}, {}

    def patch(ref, pid, value, reason):
        previous = patches.get(ref, raw[ref])
        if p(old[ref], pid) is None:
            o = copy.deepcopy(old[ref]); setp(o, pid, value)
            prop = o.find(f"{N}property[@id='{pid}']")
            previous = previous.replace(b"</object>", b.bare_bytes(prop) + b"</object>")
        else:
            previous = b.replace_property_bytes(previous, pid, value)
        previous = re.sub(rb'<simulationProperty id="' + str(pid).encode() +
                          rb'">.*?</simulationProperty>', b"", previous, flags=re.S)
        patches[ref] = previous
        changes.append({"kind": "property", "ref": ref, "property": pid,
                        "value": " ".join(value.itertext()), "reason": reason})

    def port(obj, number):
        search = {**old, **native.new}
        found = [o for ref, o in search.items()
                 if ref.rsplit(".", 1)[0] == obj.get("ref") and p(o, 3365) is not None
                 and int(p(o, 3365).text) == number]
        assert len(found) == 1, (obj.get("ref"), number)
        return found[0]

    def signal(ref, number):
        obj = ({**old, **native.new})[ref]
        typ = b.typed(obj) if obj.get("classid") in ("526", "527", "528", "529", "530", "531") else b.typed(port(obj, number))
        return b.Signal(obj, number, typ)

    def add_top(obj, source_layout=None):
        ref = obj.get("ref")
        assert ref not in blocks
        blocks.append(ref)
        p(main, 3375).append(copy.deepcopy(p(obj, 75)))
        p(main, 3117).append(nv("unsignedShort", len(blocks)-1))
        template = copy.deepcopy(source_layout if source_layout is not None else locations[MAIN + ".536_83041"])
        xy = list(template.iter(N + "float"))
        assert len(xy) == 2
        is_input = obj.get("classid") in ("526", "528", "530")
        xy[0].text = str(-2400 if is_input else 1600)
        xy[1].text = str(1800 + (len(blocks)-83)*85)
        p(main, 3383).append(template)

    def link(sig, obj, number, reason):
        si, di = blocks.index(sig.obj.get("ref")), blocks.index(obj.get("ref"))
        idx = [i for i, row in enumerate(edges) if row[2:] == [di, number]]
        assert len(idx) <= 1, (obj.get("ref"), number)
        row = [si, sig.port, di, number]
        if idx:
            old_row = edges[idx[0]]
            edges[idx[0]] = row
            changes.append({"kind": "wire_redirect", "old": old_row, "new": row, "reason": reason})
        else:
            edges.append(row); metadata.append(b.metadata())
            changes.append({"kind": "wire_add", "new": row, "reason": reason})

    def bind_native(ref, number, value, reason):
        obj = ({**old, **native.new})[ref]
        desc = port(obj, number)
        typ = b.typed(desc)
        if isinstance(value, b.Signal):
            assert typ.kind == value.type.kind, (ref, number, typ, value.type)
            if typ.kind == "enum":
                assert typ.enum == value.type.enum, (ref, number, typ, value.type)
            link(value, obj, number, reason)
        else:
            di = blocks.index(ref)
            for idx in reversed([i for i, row in enumerate(edges) if row[2:] == [di, number]]):
                changes.append({"kind": "wire_remove_for_default", "old": edges[idx], "reason": reason})
                del edges[idx]; del metadata[idx]
            if typ.kind == "boolean":
                val = nv("boolean", "true" if value else "false")
            elif typ.kind == "enum":
                val = nv("enum", value, **({"set": typ.enum} if typ.enum is not None else {}))
            else:
                val = nv("float", value)
            if desc.get("ref") in old:
                patch(desc.get("ref"), 3113, val, reason)
            else:
                setp(desc, 3113, val)

    def param(name, typ, default, description):
        sig = lib.main_input(name, typ, default, description)
        add_top(sig.obj, lib.layout(sig.obj, 0, 0))
        return sig

    def activity(name):
        c = lib.new_activity(name)
        setp(c.obj, 3670, nv("enum", 0, set=432))
        activity_bindings[name] = {}
        activity_outputs[name] = {}
        # Correct the old helper's inherited Mux tables for every new selector.
        old_select = c.select
        def select(*args, **kwargs):
            sig = old_select(*args, **kwargs)
            setp(sig.obj, 2381, b.array("array", [nv("unsignedShort", 1), nv("unsignedShort", 2)]))
            setp(sig.obj, 3122, nv("unsignedShort", 0))
            return sig
        c.select = select
        return c

    def inp(c, key, sig, default=0):
        local = c.input(key, sig.type, default)
        activity_bindings[c.name][key] = {
            "port": int(p(local.obj, 3365).text),
            "source_ref": sig.obj.get("ref"), "source_port": sig.port,
            "kind": sig.type.kind, "enum": sig.type.enum}
        queued.append((sig, c.obj, int(p(local.obj, 3365).text), c.name + " / " + key))
        return local

    def output(c, name, sig):
        exported = c.output(name, sig)
        activity_outputs[c.name][name] = {"port": exported.port, "kind": sig.type.kind, "enum": sig.type.enum}
        return exported

    def finish(c):
        c.finish()
        add_top(c.obj, locations[MAIN + ".536_83041"])
        return c

    def cloned_native(ref, name):
        obj = native.clone(ref, MAIN)
        setp(obj, 2390, nv("string", name))
        add_top(obj, locations[ref])
        return obj

    def memory(sig, boolean, name):
        template = MAIN + (".538_80491" if boolean else ".538_80484")
        obj = cloned_native(template, name)
        # The native memory block defaults to using the previous scan.
        setp(obj, 3382, nv("boolean", "true"))
        link(sig, obj, 513, name)
        return b.Signal(obj, 85, b.BOOL if boolean else b.FLOAT)

    # Reuse all 20 native physical objects. New terminals are not fabricated.
    # Physical input/output indices come from this exact CGE native.
    X4, X5, X6 = ["8-1/307_2.598_" + str(i) for i in (10001, 10004, 10007)]
    rows = [
        ("1356", "CT-CHWS-T", "8-1", "UI IN1", 1, "AI"),
        ("1355", "CT-CHWR-T", "8-1", "UI IN2", 2, "AI"),
        ("30014", "CT-CABINET-S-T", "8-1", "UI IN3", 3, "AI"),
        ("30034", "CT-CABINET-R-T", "8-1", "UI IN4", 4, "AI"),
        ("1369", "CT-PCHWS-T", "8-1", "UI IN5", 5, "AI"),
        ("1368", "CT-PCHWR-T", "8-1", "UI IN6", 6, "AI"),
        ("30013", "11-2-CTHX-1A-BLDG-R-T", X6, "UI IN1", 1, "AI"),
        ("30035", "11-2-CTHX-1B-BLDG-R-T", X6, "UI IN2", 2, "AI"),
        ("1293", "CT-PCHW-DP", X4, "UI IN1", 1, "AI"),
        ("1354", "CT-PCHWR-F", X5, "UI IN1", 1, "AI"),
        ("1436", "11-2-CTP-1A-S", "8-1", "BI IN1", 8, "DI"),
        ("1437", "11-2-CTP-1B-S", "8-1", "BI IN2", 9, "DI"),
        ("2246", "11-2-CTP-1A-C", "8-1", "BO OUT1", 1, "DO"),
        ("2247", "11-2-CTP-1B-C", "8-1", "BO OUT2", 2, "DO"),
        ("2206", "11-2-CTHX-1A-PROCESS-V-C", "8-1", "CO OUT1", 4, "DO"),
        ("2209", "11-2-CTHX-1B-PROCESS-V-C", "8-1", "CO OUT2", 5, "DO"),
        ("2614", "11-2-CTHX-1A-BLDG-V-O", "8-1", "CO OUT3", 6, "AO"),
        ("2620", "11-2-CTHX-1B-BLDG-V-O", "8-1", "CO OUT4", 7, "AO"),
        ("2327", "11-2-CTP-1A-O", "8-1", "AO OUT1", 8, "AO"),
        ("2328", "11-2-CTP-1B-O", "8-1", "AO OUT2", 9, "AO"),
    ]
    for instance, name, device, terminal, ordinal, kind in rows:
        physical = [o for ref, o in old.items() if o.get("classid") in ("239", "240", "241", "242")
                    and p(o, 75).text == instance]
        assert len(physical) == 1
        obj = physical[0]
        old_ref = obj.get("ref")
        segment = old_ref.rsplit(".", 1)[-1].rsplit("/", 1)[-1]
        new_ref = (device + "/" if device == "8-1" else device + ".") + segment
        if new_ref != old_ref:
            relocations[old_ref] = new_ref
        for pid, val in [(2390, nv("string", name)), (28, nv("string", name)),
                         (31, nv("string", terminal)),
                         (519 if kind in ("AI", "DI") else 990, nv("unsignedByte", ordinal))]:
            patch(old_ref, pid, val, "Submittal PDF 7 physical point assignment")
        proxy = MAIN + (".556_" if kind in ("AI", "DI") else ".555_") + instance
        patch(proxy, 2390, nv("string", name), "Submittal point name")
        patch(proxy, 28, nv("string", name), "Submittal point description")
        mappings.append({"name": name, "physical_ref": new_ref, "proxy_ref": proxy,
                         "device": device, "terminal": terminal, "kind": kind,
                         "status": "candidate_mapping_CCT_verification_required"})

    # The matched AHU native supplies observed Current=2 / 4..20 mA metadata.
    # The DP span remains the CGE source's provisional 0..25 psi.
    current_sample = templates["8-1/0_299963"]
    assert p(current_sample,518).text == "2"
    assert [p(current_sample,n).text for n in (1293,1294)] == ["4","20"]
    for pid in (518,1293,1294,2180):
        patch("8-1/0_1293", pid, copy.deepcopy(p(current_sample,pid)),
              "4-20 mA DP electrical format observed in native AHU; full scale still unapproved")

    # Missing physical inputs are visible, published SIM inputs for CCT tests.
    # They are NOT proxies or field bindings.
    sim = {}
    missing = [
        ("HX-A-PROC-ST", "11-2-CTHX-1A-PROCESS-S-T", X6, "UI IN3", b.Type("float", units=64), 65),
        ("HX-B-PROC-ST", "11-2-CTHX-1B-PROCESS-S-T", X6, "UI IN4", b.Type("float", units=64), 65),
        ("HX-A-VPOS", "11-2-CTHX-1A-BLDG-V-POS", X4, "UI IN2", b.Type("float", units=98), 0),
        ("HX-B-VPOS", "11-2-CTHX-1B-BLDG-V-POS", X4, "UI IN3", b.Type("float", units=98), 0),
        ("PUMP-A-FAULT", "11-2-CTP-1A-A", X4, "UI IN4", b.BOOL, False),
        ("PUMP-B-FAULT", "11-2-CTP-1B-A", X4, "UI IN5", b.BOOL, False),
        ("HX-A-OPEN", "11-2-CTHX-1A-PROCESS-V-OPN-S", X4, "UI IN6", b.BOOL, False),
        ("HX-A-CLOSED", "11-2-CTHX-1A-PROCESS-V-CLS-S", X4, "UI IN7", b.BOOL, True),
        ("HX-B-OPEN", "11-2-CTHX-1B-PROCESS-V-OPN-S", X4, "BI IN1", b.BOOL, False),
        ("HX-B-CLOSED", "11-2-CTHX-1B-PROCESS-V-CLS-S", X4, "BI IN2", b.BOOL, True),
        ("RETURN-P", "CT-PCHWR-P", X5, "UI IN2", b.Type("float", units=56), 0),
        ("UPSTREAM-P", "CT-PCHWS-UP-P", X5, "UI IN3", b.Type("float", units=56), 0),
        ("DOWNSTREAM-P", "CT-PCHWS-DOWN-P", X6, "UI IN5", b.Type("float", units=56), 0),
        ("PUMP-A-FB", "11-2-CTP-1A-FB", X6, "UI IN6", b.Type("float", units=98), 0),
        ("PUMP-B-FB", "11-2-CTP-1B-FB", X6, "UI IN7", b.Type("float", units=98), 0),
    ]
    for key, name, dev, terminal, typ, default in missing:
        sim[key] = param("SIM-" + key, typ, default, "SIMULATION ONLY; missing physical input " + name)
        mappings.append({"name": name, "device": dev, "terminal": terminal,
                         "interface_ref": sim[key].obj.get("ref"),
                         "interface_name": "SIM-" + key, "status": "physical_input_NOT_IMPLEMENTED"})

    ready = param("CONFIGURATION-READY", b.BOOL, False,
                  "Keep False until physical inputs, Platinum signals, settings and priorities are completed. True is for offline CCT testing only at this stage.")
    reset = param("CT-FAULT-RESET", b.BOOL, False, "Provisional momentary reset for latched pump/HX faults; confirm reset policy")
    pump_maint = [param("PUMP-" + x + "-MAINT", b.BOOL, False, "Pump maintenance request") for x in ("A", "B")]
    hx_maint = [param("HX-" + x + "-ISOLATE", b.BOOL, False, "BMS manual HX isolation") for x in ("A", "B")]
    proof_delay = param("PUMP-PROOF-DELAY", b.Type("float", units=73), 30,
                        "PROVISIONAL 30 s, borrowed from native status-alarm default; sequence did not specify")
    minimum_speed_ref = MAIN+".536_81398.2_207362"
    native_minimum_speed = float(p(old[minimum_speed_ref],3113).text)
    assert native_minimum_speed == 20
    minimum_speed = param("PUMP-MIN-SPEED", b.Type("float", units=98), native_minimum_speed,
                          "PROVISIONAL minimum retained from native CGE pump control; confirm against VFD/equipment requirements")
    overlap = param("HX-TRANSFER-DELAY", b.Type("float", units=73), 300, "Specified adjustable delay; timer anchor is provisional duty deselection")
    iso_delay = param("ISO-FAIL-DELAY", b.Type("float", units=73), 30, "Specified isolation mismatch delay")
    valve_delay = param("VALVE-FAIL-DELAY", b.Type("float", units=73), 120, "Specified valve deviation delay")
    valve_diff = param("VALVE-DEVIATION", b.Type("float", units=98), 10, "Specified deviation; candidate uses >= threshold; confirm boundary")
    lowflow = param("LOWFLOW-SP", b.Type("float", units=89), 0, "UNSET; zero disables low-flow alarm until approved threshold entered")
    lowflow_delay = param("LOWFLOW-DELAY", b.Type("float", units=73), 30, "PROVISIONAL; confirm low-flow delay")
    temperature_alarm_delay = param("CT-TEMP-ALM-DELAY", b.Type("float", units=73), 300, "Supply temperature alarm delay, source default 300 s")
    dp_alarm_delay = param("CT-DP-ALM-DELAY", b.Type("float", units=73), 120, "Adjustable DP alarm delay, source default 120 s")
    btu_high_percent = param("BTU-HIGH-PERCENT", b.Type("float", units=98), 10, "Adjustable high-BTU margin above external average, source default 10 percent")
    btu = param("BTU-MEAS", b.FLOAT, 0, "External/calc measurement not implemented; units and calculation TBD")
    average = param("BTU-AVERAGE", b.FLOAT, 0, "External trended average; averaging/retention not implemented")
    btu_valid = param("BTU-DATA-VALID", b.BOOL, False, "BMS freshness/validity contract not implemented")
    for ref, name in [(MAIN+".2_112", "CT-DP-SP"), (MAIN+".2_259", "CT-LWT-SP"),
                      (MAIN+".5_135", "PUMP-WEEKLY-ROT"), (MAIN+".5_110", "HX-MONTHLY-ROT")]:
        patch(ref, 2390, nv("string", name), "CT interface name; source defaults retained")

    BOOL, FLOAT = b.BOOL, b.FLOAT
    OFFON = b.Type("enum", 647, 2)
    MODE = b.Type("enum", 1346, 4)
    pump_seq, hx_seq = MAIN+".571_80431", MAIN+".571_80099"
    dp_pi = MAIN+".536_83041"
    temp_obj = cloned_native(dp_pi, "CT LWT PI - PROVISIONAL")
    temp_ref = temp_obj.get("ref")
    for number, default in [(7001, 65), (7002, 65), (7003, True), (7005, 11), (7006, 64)]:
        bind_native(temp_ref, number, default, "Native temperature-control process settings copied from CGE water-zone context; provisional")
    for number in (7001, 7002):
        setp(port(temp_obj, number), 117, nv("enum", 64, set=507))
    patch(dp_pi, 2390, nv("string", "CT DP PI"), "Name preserved native pressure PID for CT use")

    # Pump availability uses the native sequencer and actual pump-proof inputs.
    c = activity("CT PUMP CONTROL")
    en = inp(c, "SYSTEM_ENABLE", signal(MAIN+".5_85", 663))
    rd = inp(c, "CONFIG_READY", ready)
    rs = inp(c, "FAULT_RESET", reset)
    delay = inp(c, "PROOF_DELAY", proof_delay)
    raw_speed = inp(c, "DP_PI_OUTPUT", signal(dp_pi, 8000))
    min_speed = inp(c, "MIN_SPEED", minimum_speed)
    limited_speed = c.math("min", c.math("max", raw_speed, min_speed, "Pump Minimum Speed"), 100, "Pump Maximum Speed")
    permit = c.logic("and", en, rd, name="Offline Configuration Permission")
    pump_avail, pump_commands, pump_speeds, pump_on = [], [], [], []
    for idx, letter in enumerate(("A", "B")):
        maintenance = inp(c, "MAINT_"+letter, pump_maint[idx])
        fault = inp(c, "FAULT_"+letter, sim["PUMP-"+letter+"-FAULT"])
        proof = inp(c, "PROOF_"+letter, signal(MAIN+(".556_1436" if idx==0 else ".556_1437"), 8000))
        cmd = inp(c, "SELECTED_"+letter, signal(pump_seq, 8000+idx))
        proven = c.enum_bool(proof, {1}, "Pump "+letter+" Proven")
        mismatch = c.logic("and", permit, cmd, c.logic("not", proven), name="Pump "+letter+" Missing Proof")
        timed, _ = c.timer(mismatch, delay, rs, 4, "Pump "+letter+" Latched Failure")
        failed = c.logic("or", fault, timed, name="Pump "+letter+" Failure")
        available = c.logic("not", c.logic("or", maintenance, failed), name="Pump "+letter+" Available")
        on = c.logic("and", permit, cmd, available, name="Pump "+letter+" Command")
        pump_on.append(on)
        command = c.select(on, 0, 1, OFFON, "Pump "+letter+" Off On")
        speed = c.select(on, 0, limited_speed, b.Type("float", units=98), "Pump "+letter+" Speed Gate")
        hand = c.logic("and", permit, c.logic("not", on), proven, name="Pump "+letter+" Hand Condition")
        hand_alarm, _ = c.timer(hand, delay, c.logic("not", hand), 4, "Pump "+letter+" Hand Alarm Delay")
        pump_avail.append(output(c, letter+"_AVAILABLE", available))
        pump_commands.append(output(c, letter+"_COMMAND", command))
        pump_speeds.append(output(c, letter+"_SPEED", speed))
        output(c, letter+"_FAIL_ALARM", failed)
        output(c, letter+"_HAND_ALARM", hand_alarm)
    demand = output(c, "ONE_PUMP_DEMAND", c.select(permit, 0, 1, FLOAT, "One Pump Demand"))
    shutdown = output(c, "PUMP_SHUTDOWN", c.logic("not", permit))
    dp_mode = output(c, "DP_MODE", c.select(c.logic("or", *pump_on), 0, 2, MODE, "DP PI Mode With Enabled Pump"))
    finish(c)
    for idx, avail in enumerate(pump_avail):
        mem = memory(avail, True, "CT PUMP "+("A" if idx==0 else "B")+" AVAIL MEMORY")
        bind_native(pump_seq, 7000+idx, mem, "Native previous-scan availability path")
    bind_native(pump_seq, 513, demand, "One operating pump rather than source load staging")
    bind_native(pump_seq, 30094, shutdown, "System disable bypasses native min-on")
    bind_native(pump_seq, 2420, signal(MAIN+".5_135", 663), "External weekly calendar trigger; binding remains pending")
    bind_native(dp_pi, 7000, dp_mode, "CT pressure loop control mode")
    for idx, total in enumerate((MAIN+".591_80421", MAIN+".591_80424")):
        bind_native(total, 513, signal(MAIN+(".556_1436" if idx==0 else ".556_1437"), 8000), "Proven pump runtime, native 3600 second/hour totalizer")
        bind_native(pump_seq, 7500+idx, signal(total, 85), "Least proven runtime rank")
    for idx in range(2,8):
        bind_native(pump_seq, 7000+idx, False, "Only two pumps are installed")

    # HX coordinator. Previous-scan availability memories break the fault/command loop.
    hx_mem = [cloned_native(MAIN+".538_80491", "CT HX "+x+" AVAIL MEMORY") for x in ("A", "B")]
    for obj in hx_mem:
        setp(obj, 3382, nv("boolean", "true"))
    h = activity("CT HX TRANSFER AND FAULTS")
    en = inp(h, "SYSTEM_ENABLE", signal(MAIN+".5_85", 663))
    rd = inp(h, "CONFIG_READY", ready)
    rs = inp(h, "FAULT_RESET", reset)
    ov = inp(h, "OVERLAP", overlap)
    it = inp(h, "ISO_DELAY", iso_delay)
    vt = inp(h, "VALVE_DELAY", valve_delay)
    diff = inp(h, "VALVE_DEVIATION", valve_diff)
    run = h.logic("and", en, rd, name="HX Configuration Permission")
    hx_avail, iso_cmd, valve_permission, duty_enum, permitted_paths = [], [], [], [], []
    for idx, letter in enumerate(("A","B")):
        maintenance = inp(h, "ISOLATE_"+letter, hx_maint[idx])
        previous = inp(h, "PREVIOUS_AVAILABLE_"+letter, signal(hx_mem[idx].get("ref"),85))
        duty = inp(h, "DUTY_"+letter, signal(hx_seq,8000+idx))
        opened = inp(h, "OPEN_"+letter, sim["HX-"+letter+"-OPEN"])
        closed = inp(h, "CLOSED_"+letter, sim["HX-"+letter+"-CLOSED"])
        position = inp(h, "POSITION_"+letter, sim["HX-"+letter+"-VPOS"])
        effective = signal(MAIN+(".556_30016" if idx==0 else ".556_30037"),8000)
        command = inp(h, "VALVE_COMMAND_"+letter, memory(effective, False, "CT VALVE "+letter+" COMMAND MEMORY"))
        held, _ = h.timer(duty, ov, h.logic("not", run), 5, "HX "+letter+" Process Path Off Delay")
        iso_on = h.logic("and", run, held, previous, h.logic("not", maintenance), name="HX "+letter+" Isolation Command")
        open_mismatch = h.logic("and", iso_on, closed)
        close_mismatch = h.logic("and", h.logic("not", iso_on), opened)
        mismatch = h.logic("and", run, h.logic("or",open_mismatch,close_mismatch), name="HX "+letter+" End Switch Mismatch")
        isolation_fault, _ = h.timer(mismatch, it, rs, 4, "HX "+letter+" Latched Isolation Fault")
        delta = h.math("sub", command, position, "HX "+letter+" Position Error")
        abs_delta = h.math("max", delta, h.math("mul", delta, -1), "HX "+letter+" Absolute Position Error")
        deviated = h.logic("and", run, h.compare("gte",abs_delta,diff), name="HX "+letter+" Position Deviated")
        control_fault, _ = h.timer(deviated, vt, rs, 4, "HX "+letter+" Latched Control Valve Fault")
        available = h.logic("not", h.logic("or", maintenance, isolation_fault, control_fault), name="HX "+letter+" Available")
        allowed = h.logic("and", iso_on, opened, h.logic("not", closed), name="HX "+letter+" Building Valve Permission")
        permitted_paths.append(allowed)
        hx_avail.append(output(h,letter+"_AVAILABLE",available))
        iso_cmd.append(output(h,letter+"_ISO_COMMAND",h.select(iso_on,0,1,OFFON,"HX "+letter+" Isolation Off On")))
        valve_permission.append(output(h,letter+"_VALVE_PERMISSION",allowed))
        duty_enum.append(output(h,letter+"_DUTY_ENUM",h.select(duty,0,1,OFFON,"HX "+letter+" Runtime State")))
        output(h,letter+"_ISO_FAIL",isolation_fault)
        output(h,letter+"_VALVE_FAIL",control_fault)
    hx_demand = output(h,"ONE_HX_DEMAND",h.select(run,0,1,FLOAT,"One Duty HX Demand"))
    hx_shutdown = output(h,"HX_SHUTDOWN",h.logic("not",run))
    temp_mode = output(h,"LWT_MODE",h.select(h.logic("and",run,h.logic("or",*permitted_paths)),0,2,MODE,"LWT PI Mode With Proven Path"))
    finish(h)
    for idx in range(2):
        link(hx_avail[idx],hx_mem[idx],513,"Previous-scan HX availability")
        bind_native(hx_seq,7000+idx,signal(hx_mem[idx].get("ref"),85),"HX availability feedback")
        total = MAIN+(".591_80466" if idx==0 else ".591_80467")
        bind_native(total,513,duty_enum[idx],"Native HX duty-hours totalization")
        bind_native(hx_seq,7500+idx,signal(total,85),"Provisional monthly lower-duty-hours preference; confirm rotation policy")
    for idx in range(2,8):
        bind_native(hx_seq,7000+idx,False,"Only two HX are installed")
    bind_native(hx_seq,513,hx_demand,"One duty heat exchanger")
    bind_native(hx_seq,30094,hx_shutdown,"System disable")
    bind_native(hx_seq,2420,signal(MAIN+".5_110",663),"External monthly calendar pulse; binding remains pending")
    bind_native(temp_ref,7000,temp_mode,"Temperature control mode")
    bind_native(temp_ref,7001,signal(MAIN+".556_1369",8000),"Common-header process supply sensor, not individual HX sensors")
    bind_native(temp_ref,7002,signal(MAIN+".2_259",663),"Source 65 F retained as explicitly provisional LWT SP")

    g = activity("CT BUILDING VALVE OUTPUTS")
    value = inp(g,"LWT_PI_OUTPUT",signal(temp_ref,8000))
    valve_cmd = []
    for idx,letter in enumerate(("A","B")):
        allow = inp(g,"ALLOW_"+letter,valve_permission[idx])
        valve_cmd.append(output(g,letter+"_VALVE_COMMAND",
                         g.select(allow,0,value,b.Type("float",units=98),"HX "+letter+" Valve Gate")))
    finish(g)
    for idx in range(2):
        for sig,ref in [
            (pump_commands[idx], MAIN+(".555_2246" if idx==0 else ".555_2247")),
            (pump_speeds[idx], MAIN+(".555_2327" if idx==0 else ".555_2328")),
            (iso_cmd[idx], MAIN+(".555_2206" if idx==0 else ".555_2209")),
            (valve_cmd[idx], MAIN+(".555_2614" if idx==0 else ".555_2620"))]:
            link(sig,old[ref],7000,"CT outputs replace legacy source program drivers")

    a = activity("CT PROCESS ALARMS")
    en = inp(a,"SYSTEM_ENABLE",signal(MAIN+".5_85",663))
    rd = inp(a,"CONFIG_READY",ready)
    temp = inp(a,"PROCESS_SUPPLY_T",signal(MAIN+".556_1369",8000))
    t_sp = inp(a,"LWT_SP",signal(MAIN+".2_259",663))
    dp = inp(a,"DP",signal(MAIN+".556_1293",8000))
    dp_sp = inp(a,"DP_SP",signal(MAIN+".2_112",663))
    flow = inp(a,"FLOW",signal(MAIN+".556_1354",8000))
    flow_sp = inp(a,"LOWFLOW_SP",lowflow)
    flow_time = inp(a,"LOWFLOW_DELAY",lowflow_delay)
    temperature_time = inp(a,"TEMPERATURE_DELAY",temperature_alarm_delay)
    dp_time = inp(a,"DP_DELAY",dp_alarm_delay)
    btu_margin = inp(a,"BTU_HIGH_PERCENT",btu_high_percent)
    bt = inp(a,"BTU_MEAS",btu)
    avg = inp(a,"BTU_AVERAGE",average)
    bv = inp(a,"BTU_VALID",btu_valid)
    run = a.logic("and",en,rd)
    conditions = [
        ("HIGH_SUPPLY_T",a.compare("gt",temp,a.math("add",t_sp,5)),temperature_time),
        ("LOW_SUPPLY_T",a.compare("lt",temp,a.math("sub",t_sp,5)),temperature_time),
        ("HIGH_DP",a.compare("gt",dp,a.math("mul",dp_sp,1.25)),dp_time),
        ("LOW_DP",a.compare("lt",dp,a.math("mul",dp_sp,.75)),dp_time)
    ]
    for name,condition,duration in conditions:
        condition = a.logic("and",run,condition,name=name+" Qualifier")
        alarm,_ = a.timer(condition,duration,a.logic("not",condition),4,name+" Delay")
        output(a,name,alarm)
    valid_flow = a.compare("gt",flow_sp,0)
    condition = a.logic("and",run,valid_flow,a.compare("lt",flow,flow_sp))
    alarm,_ = a.timer(condition,flow_time,a.logic("not",condition),4,"Low Flow Delay")
    output(a,"LOW_FLOW",alarm)
    output(a,"LOWFLOW_SETTINGS_MISSING",a.logic("not",valid_flow))
    btu_average_valid = a.logic("and",bv,a.compare("gt",avg,0))
    btu_multiplier = a.math("add",1,a.math("mul",btu_margin,.01))
    high_btu = a.logic("and",run,btu_average_valid,a.compare("gt",bt,a.math("mul",avg,btu_multiplier)))
    output(a,"HIGH_BTU",high_btu)
    output(a,"BTU_DATA_MISSING",a.logic("not",btu_average_valid))
    finish(a)

    for sig,obj,number,reason in queued:
        link(sig,obj,number,reason)
    for ref,name in [
        (pump_seq,"CT PUMP LEAD STANDBY"),(hx_seq,"CT HX DUTY STANDBY"),
        (MAIN+".591_80421","CT PUMP A PROVEN HOURS"),(MAIN+".591_80424","CT PUMP B PROVEN HOURS"),
        (MAIN+".591_80466","CT HX A DUTY HOURS"),(MAIN+".591_80467","CT HX B DUTY HOURS")]:
        patch(ref,2390,nv("string",name),"Identify retained native CT function")
    # Retain source SYSTEM-EN=False. CONFIGURATION-READY=False is additional.
    assert p(old[MAIN+".5_85"],3113).text == "false"
    setp(main,3118,b.array("array",[b.edge(row) for row in edges]))
    setp(main,3384,b.array("listof",metadata))
    main_raw = patches.get(MAIN,raw[MAIN])
    for pid in (3375,3117,3383,3118,3384):
        main_raw = b.replace_property_bytes(main_raw,pid,p(main,pid))
    patches[MAIN] = main_raw
    candidate = original
    for ref,replacement in patches.items():
        assert candidate.count(raw[ref]) == 1, ref
        candidate = candidate.replace(raw[ref],replacement,1)
    for old_ref,new_ref in relocations.items():
        assert new_ref not in old
        # Exact full-reference occurrences only; no substring ID rewriting.
        candidate = candidate.replace(old_ref.encode()+b'"',new_ref.encode()+b'"')
        candidate = candidate.replace(old_ref.encode()+b"<",new_ref.encode()+b"<")
    new_objects = {**lib.new,**native.new}
    assert not set(lib.new)&set(native.new)
    insertion = b"".join(b.bare_bytes(o) for o in new_objects.values())
    assert candidate.count(b"</objects>")==1
    candidate = candidate.replace(b"</objects>",insertion+b"</objects>")
    by=b.parse(candidate)
    assert len(by)==len(old)+len(new_objects)
    assert [b.bare_bytes(p(by[MAIN],n)) for n in (3926,3927)]==original_registry
    # Neither source/root hardware IDs nor the expansion model/address records change.
    for ref in ["8-1",X4,X5,X6,"8-1/307_2.640_1"]:
        assert b.bare_bytes(by[ref])==b.bare_bytes(old[ref])
    for o in lib.new.values():
        if o.get("classid")=="562":
            assert [x.text for x in p(o,2381)]==["1","2"] and p(o,3122).text=="0"
    out.mkdir(parents=True,exist_ok=True)
    final=out/"CT_CHWS_R1_PARTIAL_CCT_TEST.caf"
    assert final.resolve()!=source.resolve()
    if final.exists():
        raise FileExistsError("Refuse to overwrite an existing candidate: "+str(final))
    with ZipFile(final,"w") as z:
        z.comment=comment;z.writestr(info,candidate)
    record={
        "status":"PARTIAL_CANDIDATE_CCT_NOT_EXECUTED",
        "source_sha256":SOURCE_SHA,"output_sha256":digest(final),
        "repository_commit":COMMIT,"CCT_saved_version":"10.8.0.60",
        "controller":"M4-CGE09090-0","source_objects":len(old),"output_objects":len(by),
        "source_main_connections":len(original_edges),"output_main_connections":len(edges),
        "native_registry_preserved":True,"source_hardware_records_preserved":True,
        "hardwired_points_mapped":20,"physical_inputs_missing":15,
        "point_mapping":mappings,"changes":changes,"relocations":relocations,
        "activities":{c.name:{"ref":c.ref,"inputs":activity_bindings[c.name],
                            "outputs":activity_outputs[c.name]} for c in lib.activities},
        "interfaces":lib.interfaces,
        "native_CCT_executed":False,"control_behavior_verified":False,
        "native_functions_not_executed":["Sequencer class 571","PID/Preprocessor class 252/582",
                                         "Totalization class 591","Previous-scan memory class 538",
                                         "Physical input scaling/output bindings"],
        "construction_sources":[{"path":str(ahu.relative_to(repo)),"sha256":AHU_SHA},
                                {"path":source.name,"sha256":SOURCE_SHA}],
        "open_items":[
            "15 required physical inputs are NOT created/bound; SIM-* inputs are workbench interfaces only.",
            "Eight retained physical RTD inputs still use source Nickel setup 3. Submittal requires Platinum 1k RTD. Native Platinum serialization/probe needed.",
            "DP setpoint 10 psi and LWT setpoint 65 F are inherited source values, NOT approved submittal settings. DP full scale 25 psi retained provisionally.",
            "Running pump speed is limited to 20..100 percent. The 20 percent minimum is retained from native CGE pump control and remains provisional; confirm equipment limits.",
            "Flow remains inherited 0-10 V / 0..100 scale; electrical selection, full scale and units remain unconfirmed.",
            "Source local display is MS-DIS1710-0 at SA 3; submittal calls M4-DLK0350-0. No blind display-model rewrite performed.",
            "Weekly/monthly trigger inputs exist; calendar schedules, host bindings and restart freshness are NOT implemented.",
            "Monthly HX preference uses lower native duty hours, with native device-number tie ordering; confirm intended rotation criterion.",
            "300 s HX delay starts on duty deselection. Manual isolation/fault bypasses overlap; transfer proof/rollback policy requires approval.",
            "Pump proof/hand delay is PROVISIONAL 30 s. Failure latches use momentary manual reset. Confirm actual failure/reset/startup policies.",
            "Valve deviation uses >=10 percent for 120 s; isolation uses specified open/closed mismatch for 30 s. Both/neither proof policy is not fully specified.",
            "Pump startup is not interlocked to a proven HX path in this version; approved start order and all-unavailable/failure policy remain incomplete.",
            "BTU measurement/average/valid inputs are external contracts only; heat-rate/energy calculation, fluid coefficient, trending, baselines and kW integration are NOT implemented.",
            "Low-flow alarm is disabled while LOWFLOW-SP is 0. Approved low-flow threshold/delay needed.",
            "LWT PI retains provisional native tuning/process range and uses water process ID 11 observed in the source water-zone control. Native tuning, action and output-override tracking require review.",
            "Legacy source control modules remain for comparison. Their eight physical-output wires have been redirected to CT logic. Legacy diagnostic points are not acceptance evidence.",
            "CONFIGURATION-READY and SYSTEM-EN remain False. Candidate is for CCT opening/Simulation, not controller transfer.",
        ]
    }
    (out/"CT_CHWS_R1_Manifest.json").write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps({"caf":str(final),"sha256":record["output_sha256"],
                      "objects":len(by),"mapped_hardwired":20,"unbound_physical_inputs":15,
                      "status":record["status"]},indent=2))
    return final

if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit(__doc__)
    build(*map(Path,sys.argv[1:]))
