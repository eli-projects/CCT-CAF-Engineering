#!/usr/bin/env python3
"""Verify the actual serialized custom Activities with the reviewed model.

This does NOT execute native CCT, sequencers, PIDs, totalizers, memories or
hardware. Usage: python3 verify_ct_chws_candidate.py CAF MANIFEST REPO REPORT
"""
import hashlib
import json
import sys
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E

def verify(caf, manifest_path, repo, report):
    scripts = repo / "caf-engineering-reference/scripts/research"
    model = scripts / "verify_custom_graph.py"
    assert hashlib.sha256(model.read_bytes()).hexdigest() == "f75f721923c89ff29ab6f24ba54ebe4bc7f42aa1a4e07e0f158005b69577f68b"
    sys.path.insert(0, str(scripts))
    from verify_custom_graph import Runtime, p, N
    manifest = json.loads(manifest_path.read_text())
    assert hashlib.sha256(caf.read_bytes()).hexdigest() == manifest["output_sha256"]
    with ZipFile(caf) as z:
        assert z.testzip() is None
        root = E.fromstring(z.read(z.namelist()[0]))
    by = {o.get("ref"): o for o in root.findall(N+"object")}
    assert len(by) == manifest["output_objects"]
    assert len({o.get("ref") for o in root.findall(N+"object")}) == len(by)
    for row in manifest["point_mapping"]:
        if row["status"] == "physical_input_NOT_IMPLEMENTED":
            assert row["interface_name"].startswith("SIM-")
            assert row["interface_ref"] in by
            assert "physical_ref" not in row
        else:
            obj = by[row["physical_ref"]]
            assert p(obj,31).text == row["terminal"]
            assert p(obj,2390).text == row["name"]
            proxy = by[row["proxy_ref"]]
            arr = p(proxy,3399 if row["kind"] in ("AI","DI") else 3672)
            assert [v.text for v in arr.iter(N+"attrref")] == [row["physical_ref"]]
    assert sum("physical_ref" in x for x in manifest["point_mapping"]) == 20
    assert sum(x["status"]=="physical_input_NOT_IMPLEMENTED" for x in manifest["point_mapping"]) == 15
    checks=[]
    def passed(name):
        checks.append({"name":name,"result":"PASS_INDEPENDENT_CUSTOM_ACTIVITY_MODEL_ONLY"})

    class Scenario:
        def __init__(self, name, env):
            self.meta=manifest["activities"][name]
            self.runtime=Runtime(by,self.meta["ref"])
            self.env=dict(env)
        def step(self,t,**updates):
            self.env.update(updates)
            assert set(self.env) == set(self.meta["inputs"]), (set(self.meta["inputs"])-set(self.env),set(self.env)-set(self.meta["inputs"]))
            data={v["port"]:self.env[k] for k,v in self.meta["inputs"].items()}
            raw=self.runtime.step(t,data)
            return {k:raw[v["port"]] for k,v in self.meta["outputs"].items()}
    def check(out,key,expected):
        assert out[key].reliable,(key,"unreliable",out[key])
        assert out[key].value==expected,(key,out[key].value,expected)

    pump=dict(SYSTEM_ENABLE=True,CONFIG_READY=True,FAULT_RESET=False,PROOF_DELAY=30,MIN_SPEED=20,
              DP_PI_OUTPUT=48,MAINT_A=False,FAULT_A=False,PROOF_A=1,SELECTED_A=True,
              MAINT_B=False,FAULT_B=False,PROOF_B=0,SELECTED_B=False)
    s=Scenario("CT PUMP CONTROL",pump)
    o=s.step(0,CONFIG_READY=False)
    for k,v in [("A_COMMAND",0),("B_COMMAND",0),("A_SPEED",0),("B_SPEED",0),("DP_MODE",0),("ONE_PUMP_DEMAND",0)]: check(o,k,v)
    passed("Unconfirmed configuration keeps custom pump commands, speeds and PID mode off")
    s=Scenario("CT PUMP CONTROL",pump);o=s.step(0)
    for k,v in [("A_COMMAND",1),("B_COMMAND",0),("A_SPEED",48),("B_SPEED",0),("DP_MODE",2),("A_AVAILABLE",True),("B_AVAILABLE",True)]:check(o,k,v)
    passed("Selected proven pump gets native PI demand; standby speed is zero")
    s=Scenario("CT PUMP CONTROL",pump)
    check(s.step(0,DP_PI_OUTPUT=5),"A_SPEED",20)
    check(s.step(1,DP_PI_OUTPUT=150),"A_SPEED",100)
    check(s.step(2,SELECTED_A=False),"A_SPEED",0)
    passed("Running pump respects native provisional 20 percent minimum and 100 percent ceiling; stopped output stays zero")
    s=Scenario("CT PUMP CONTROL",{**pump,"PROOF_A":0})
    check(s.step(0),"A_FAIL_ALARM",False);check(s.step(29),"A_FAIL_ALARM",False)
    o=s.step(30);check(o,"A_FAIL_ALARM",True);check(o,"A_AVAILABLE",False);check(o,"B_AVAILABLE",True)
    check(o,"A_COMMAND",0);check(o,"A_SPEED",0);check(o,"DP_MODE",0)
    o=s.step(31,SELECTED_A=False,SELECTED_B=True,PROOF_B=1)
    check(o,"A_COMMAND",0);check(o,"B_COMMAND",1)
    passed("Proof failure removes A eligibility after provisional delay; substituted native selection input routes B")
    s=Scenario("CT PUMP CONTROL",pump);o=s.step(0,FAULT_A=True)
    check(o,"A_AVAILABLE",False);check(o,"A_FAIL_ALARM",True)
    check(o,"A_COMMAND",0);check(o,"A_SPEED",0);check(o,"DP_MODE",0)
    passed("VFD fault immediately removes eligibility and output even before native selector changes")
    s=Scenario("CT PUMP CONTROL",pump);o=s.step(0,MAINT_A=True)
    check(o,"A_AVAILABLE",False);check(o,"A_FAIL_ALARM",False)
    check(o,"A_COMMAND",0);check(o,"A_SPEED",0)
    passed("Maintenance excludes and turns off a pump without inventing a failure alarm")
    s=Scenario("CT PUMP CONTROL",pump)
    o=s.step(0,FAULT_A=True,FAULT_B=True,SELECTED_B=True)
    for k,v in [("A_COMMAND",0),("B_COMMAND",0),("A_SPEED",0),("B_SPEED",0),("DP_MODE",0)]:check(o,k,v)
    passed("Both pumps unavailable keeps outputs and native DP loop mode off")
    s=Scenario("CT PUMP CONTROL",{**pump,"SELECTED_A":False})
    check(s.step(0),"A_HAND_ALARM",False);check(s.step(30),"A_HAND_ALARM",True)
    check(s.step(31,PROOF_A=0),"A_HAND_ALARM",False)
    passed("Hand alarm uses command/status mismatch and clears after proof normalizes")
    s=Scenario("CT PUMP CONTROL",{**pump,"PROOF_A":0})
    s.step(0);check(s.step(30),"A_AVAILABLE",False)
    check(s.step(31,SELECTED_A=False,FAULT_RESET=True),"A_AVAILABLE",True)
    passed("Explicit provisional manual reset clears the custom pump latch")

    hx=dict(SYSTEM_ENABLE=True,CONFIG_READY=True,FAULT_RESET=False,OVERLAP=300,
            ISO_DELAY=30,VALVE_DELAY=120,VALVE_DEVIATION=10,
            ISOLATE_A=False,PREVIOUS_AVAILABLE_A=True,DUTY_A=True,
            OPEN_A=True,CLOSED_A=False,POSITION_A=40,VALVE_COMMAND_A=40,
            ISOLATE_B=False,PREVIOUS_AVAILABLE_B=True,DUTY_B=False,
            OPEN_B=False,CLOSED_B=True,POSITION_B=0,VALVE_COMMAND_B=0)
    s=Scenario("CT HX TRANSFER AND FAULTS",hx);o=s.step(0)
    for k,v in [("A_ISO_COMMAND",1),("B_ISO_COMMAND",0),("A_VALVE_PERMISSION",True),("B_VALVE_PERMISSION",False),("LWT_MODE",2)]:check(o,k,v)
    passed("Duty HX with open proof permits cooling; standby is isolated")
    s=Scenario("CT HX TRANSFER AND FAULTS",hx);o=s.step(0,CONFIG_READY=False)
    for k,v in [("A_ISO_COMMAND",0),("B_ISO_COMMAND",0),("LWT_MODE",0)]:check(o,k,v)
    passed("Configuration guard disables HX commands and LWT mode")
    s=Scenario("CT HX TRANSFER AND FAULTS",{**hx,"OPEN_A":False,"CLOSED_A":True})
    o=s.step(0);check(o,"LWT_MODE",0);check(o,"A_ISO_FAIL",False)
    check(s.step(29),"A_ISO_FAIL",False)
    o=s.step(30);check(o,"A_ISO_FAIL",True);check(o,"A_AVAILABLE",False)
    check(s.step(31,PREVIOUS_AVAILABLE_A=False),"A_ISO_COMMAND",0)
    passed("Missing open proof blocks LWT loop; specified mismatch times out and previous-scan exclusion closes command")
    s=Scenario("CT HX TRANSFER AND FAULTS",{**hx,"POSITION_A":30})
    check(s.step(0),"A_VALVE_FAIL",False);check(s.step(119),"A_VALVE_FAIL",False)
    check(s.step(120),"A_VALVE_FAIL",True)
    check(s.step(121,FAULT_RESET=True,POSITION_A=40),"A_VALVE_FAIL",False)
    passed("Provisional inclusive 10 percent deviation edge latches at 120 s; reset clears")
    s=Scenario("CT HX TRANSFER AND FAULTS",{**hx,"POSITION_A":30.1})
    s.step(0);check(s.step(121),"A_VALVE_FAIL",False)
    passed("Position error below 10 percent does not trip deviation latch")
    s=Scenario("CT HX TRANSFER AND FAULTS",hx)
    s.step(0);o=s.step(1,DUTY_A=False,DUTY_B=True,OPEN_B=True,CLOSED_B=False)
    check(o,"A_ISO_COMMAND",1);check(o,"B_ISO_COMMAND",1)
    o=s.step(300);check(o,"A_ISO_COMMAND",1);check(o,"A_ISO_FAIL",False)
    o=s.step(301);check(o,"A_ISO_COMMAND",0);check(o,"A_ISO_FAIL",False)
    check(s.step(330),"A_ISO_FAIL",False);check(s.step(331),"A_ISO_FAIL",True)
    passed("300 s overlap is separate from 30 s close-failure timing, measured from actual close command")
    s=Scenario("CT HX TRANSFER AND FAULTS",hx);s.step(0)
    o=s.step(1,ISOLATE_A=True)
    check(o,"A_ISO_COMMAND",0);check(o,"A_VALVE_PERMISSION",False);check(o,"A_AVAILABLE",False)
    passed("Manual isolation bypasses normal overlap and removes building-valve permission")
    s=Scenario("CT BUILDING VALVE OUTPUTS",dict(LWT_PI_OUTPUT=47,ALLOW_A=True,ALLOW_B=False))
    o=s.step(0);check(o,"A_VALVE_COMMAND",47);check(o,"B_VALVE_COMMAND",0)
    passed("LWT demand reaches permitted building valve only")

    alarms=dict(SYSTEM_ENABLE=True,CONFIG_READY=True,PROCESS_SUPPLY_T=65,LWT_SP=65,
                DP=10,DP_SP=10,FLOW=5,LOWFLOW_SP=0,LOWFLOW_DELAY=30,
                TEMPERATURE_DELAY=300,DP_DELAY=120,BTU_HIGH_PERCENT=10,
                BTU_MEAS=100,BTU_AVERAGE=100,BTU_VALID=False)
    for name,pv,key,bound,trip,delay in [
        ("High supply","PROCESS_SUPPLY_T","HIGH_SUPPLY_T",70,70.1,300),
        ("Low supply","PROCESS_SUPPLY_T","LOW_SUPPLY_T",60,59.9,300),
        ("High DP","DP","HIGH_DP",12.5,12.51,120),
        ("Low DP","DP","LOW_DP",7.5,7.49,120)]:
        s=Scenario("CT PROCESS ALARMS",{**alarms,pv:bound})
        s.step(0);check(s.step(delay+1),key,False)
        s=Scenario("CT PROCESS ALARMS",{**alarms,pv:trip})
        s.step(0);check(s.step(delay-1),key,False);check(s.step(delay),key,True)
        check(s.step(delay+1,**{pv:alarms[pv]}),key,False)
        passed(name+" strict threshold, specified delay and reset")
    s=Scenario("CT PROCESS ALARMS",{**alarms,"FLOW":0})
    o=s.step(0);check(o,"LOWFLOW_SETTINGS_MISSING",True);check(o,"LOW_FLOW",False)
    check(s.step(100),"LOW_FLOW",False)
    s=Scenario("CT PROCESS ALARMS",{**alarms,"FLOW":0,"LOWFLOW_SP":1.5})
    s.step(0);check(s.step(29),"LOW_FLOW",False);check(s.step(30),"LOW_FLOW",True)
    check(s.step(31,FLOW=2),"LOW_FLOW",False)
    passed("Unset flow threshold is visible and disabled; explicit threshold/delay works")
    s=Scenario("CT PROCESS ALARMS",{**alarms,"BTU_MEAS":111})
    o=s.step(0);check(o,"HIGH_BTU",False);check(o,"BTU_DATA_MISSING",True)
    check(s.step(1,BTU_VALID=True,BTU_MEAS=110),"HIGH_BTU",False)
    check(s.step(2,BTU_MEAS=111),"HIGH_BTU",True)
    check(s.step(3,BTU_AVERAGE=0),"BTU_DATA_MISSING",True)
    check(s.step(4,BTU_AVERAGE=100,BTU_HIGH_PERCENT=20),"HIGH_BTU",False)
    passed("External BTU comparator respects valid data and strict 110 percent boundary")
    s=Scenario("CT PROCESS ALARMS",{**alarms,"DP":20,"DP_DELAY":15})
    s.step(0);check(s.step(14),"HIGH_DP",False);check(s.step(15),"HIGH_DP",True)
    passed("Adjustable DP alarm delay uses the serialized external setting")
    s=Scenario("CT PROCESS ALARMS",{**alarms,"CONFIG_READY":False,"PROCESS_SUPPLY_T":90,"DP":20})
    s.step(0);o=s.step(400)
    check(o,"HIGH_SUPPLY_T",False);check(o,"HIGH_DP",False)
    passed("Configuration guard masks uncommissioned custom process alarms")
    result={"caf_sha256":manifest["output_sha256"],
            "status":"CUSTOM_ACTIVITY_MODEL_CHECKS_PASS_NATIVE_CCT_NOT_EXECUTED",
            "scenario_groups":len(checks),"checks":checks,
            "native_CCT_executed":False,"whole_control_system_simulated":False,
            "scope":"Actual serialized custom Activities only, with explicit external inputs.",
            "limitations":manifest["native_functions_not_executed"],
            "bindings":{"existing_physical_candidate_mappings_checked":20,"unimplemented_physical_inputs_explicit":15}}
    report.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ("status","caf_sha256","scenario_groups")},indent=2))

if __name__=="__main__":
    if len(sys.argv)!=5:raise SystemExit(__doc__)
    verify(*map(Path,sys.argv[1:]))
