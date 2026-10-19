#!/usr/bin/env python3
"""Build bounded CAF candidates from a submittal-derived JSON spec, using retained natives.
No source CAF argument, repository checkout or network is required by these recipes.
Native CCT is not executed. See references/submittal-only-workflow.md.
"""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E

ROOT=Path(__file__).resolve().parents[1]
N='{http://johnsoncontrols.com/MetasysIII/2002/3/Core}'
MAIN='8-1/575_1'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def library():return json.loads((ROOT/'assets/native-library.json').read_text())
def load_module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s)
    sys.modules[name]=m;s.loader.exec_module(m);return m

def prop(o,pid):
    d=o.find(f'{N}property[@id="{pid}"]/{N}data');return d[0] if d is not None and len(d) else None

def norm_model(model):
    if model.startswith('M4-') and model.endswith('-0'):return model[3:-2]
    return model

def plan(spec,cat=None):
    cat=cat or library()
    if spec.get('schema')!='cct-caf-spec-v1':raise ValueError('Expected schema cct-caf-spec-v1')
    controller=spec.get('controller',{});model=controller.get('model','')
    release=controller.get('release')
    matches=[p for p in cat['profiles'] if norm_model(p['controller_model'])==norm_model(model) and (release is None or p['release']==str(release))]
    result={'status':'NEEDS_CAPABILITY_WORK','new_CAF_upload_required':False,'native_CCT_executed':False,'missing_capabilities':[],'assumptions':list(spec.get('assumptions',[]))}
    if len(matches)!=1:
        result['missing_capabilities'].append({'kind':'controller_profile','detail':f'No unique retained native for model {model!r} release {release!r}; inspect retained library/repo/definitions before asking for a focused new native probe.'})
        return result
    profile=matches[0];result['profile_id']=profile['id'];result['source_sha256']=profile['sha256']
    if release is None:result['assumptions'].append('Authoring release selected from the unique retained profile: '+profile['release']+'; installed tool/firmware compatibility remains untested.')
    if model!=profile['controller_model']:result['assumptions'].append('Native profile order code selected: '+profile['controller_model']+'; verify actual order-code suffix.')
    recipes=[v for v in cat['recipes'] if v['id']==spec.get('recipe') and v['profile']==profile['id']]
    if len(recipes)!=1:
        result['missing_capabilities'].append({'kind':'recipe','detail':'No bounded recipe matches this profile. Compose native modules/new supported logic and retain the implementation; do not clone an unrelated finished application as a claimed program.'})
        return result
    recipe=recipes[0];result['recipe']=recipe['id'];result['known_gaps']=list(recipe['known_gaps'])
    result['known_gaps'].append('Native application/device/network identity is retained from the profile; project identity configuration and uniqueness are not implemented or accepted.')
    for key in controller:
        if key not in {'model','release','expansions'}:
            result['known_gaps'].append('Controller setting not applied by this bounded recipe: '+key+'='+str(controller[key]))
    if not spec.get('requested_features'):raise ValueError('Extract requested_features from the sequence; do not assume the recipe covers an unspecified program')
    deferred=spec.get('deferred_features',[])
    if any(not d.get('feature') or not d.get('reason') or d['feature'] not in spec['requested_features'] for d in deferred):raise ValueError('Deferred features need a requested feature and explicit reason')
    result['deferred_features']=deferred
    unknown=set(spec['requested_features'])-set(recipe['features'])-{d['feature'] for d in deferred}
    if unknown:result['missing_capabilities'].append({'kind':'logic','detail':'Requested features outside this recipe: '+', '.join(sorted(unknown))})
    points=spec.get('points',[])
    if len({p.get('role') for p in points})!=len(points):raise ValueError('Duplicate point roles')
    if len({p.get('name') for p in points})!=len(points):raise ValueError('Duplicate point names')
    got={p['role']:p for p in points};expected=recipe['point_roles']
    for role in sorted(set(expected)-set(got)):result['missing_capabilities'].append({'kind':'point_role','detail':'Missing specified role '+role})
    for role in sorted(set(got)-set(expected)):result['missing_capabilities'].append({'kind':'point_role','detail':'Additional role needs construction work: '+role})
    for role in sorted(set(got)&set(expected)):
        point=got[role];bind=expected[role]
        for key,bk in [('device','source_device'),('terminal','source_terminal'),('kind','kind')]:
            if point.get(key)!=bind[bk]:result['missing_capabilities'].append({'kind':'hardware_variant','detail':f'{role}: {key} {point.get(key)!r} differs from observed recipe {bind[bk]!r}'})
        name=point.get('name','')
        if 'readback_ref' in bind and len(name)>29:raise ValueError('Output name plus -EC exceeds 32 characters')
        if recipe['id']=='single-exhaust-fan-v1' and role=='room_dp' and point.get('signal')!='voltage_0_10':
            result['missing_capabilities'].append({'kind':'signal_variant','detail':'Fan recipe pressure input supports observed voltage_0_10 only; add current/RTD variants from native evidence.'})
        if not name or len(name)>32 or any(ord(c)<32 for c in name):raise ValueError('Point name must be 1..32 printable characters: '+role)
    expected_exp=profile.get('expansions',[])
    actual_exp=controller.get('expansions',[])
    if actual_exp!=expected_exp:result['missing_capabilities'].append({'kind':'topology','detail':'Expansion model/address list differs from retained profile; inspect/construct native topology before using this recipe.'})
    settings=spec.get('settings',{})
    if recipe['id']=='single-exhaust-fan-v1' and settings.get('pressure_minimum',0)>=settings.get('pressure_maximum',1):raise ValueError('Pressure minimum must be below maximum')
    allowed=ct_settings() if recipe['id'].startswith('ct-chws') else ef_settings()
    for key,value in settings.items():
        if key not in allowed:raise ValueError('Unsupported setting: '+key)
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError('Finite numeric setting required: '+key)
        low,high=allowed[key][2:]
        if not low<=value<=high:raise ValueError('Setting outside supported range: '+key)
    if not spec.get('sources') or any(not s.get('filename') or not re.fullmatch('[0-9a-f]{64}',s.get('sha256','')) for s in spec['sources']):raise ValueError('Retain filename and SHA-256 for each source submittal/sequence')
    name=spec.get('project',{}).get('name','')
    if not name or len(name)>32 or any(ord(c)<32 for c in name):raise ValueError('Project name must be 1..32 printable characters')
    if not result['missing_capabilities']:result['status']='PARTIAL_RECIPE_READY_CCT_NOT_EXECUTED'
    return result

def ct_settings():
    # role -> (selector, units/type supplied by retained native, lower, upper)
    return {'dp_setpoint':(MAIN+'.2_112','float',0.01,25),'lwt_setpoint':(MAIN+'.2_259','float',32,100),
            'pump_minimum_speed':('PUMP-MIN-SPEED','float',0,100),'pump_proof_delay':('PUMP-PROOF-DELAY','float',1,3600),
            'hx_transfer_delay':('HX-TRANSFER-DELAY','float',0,3600),'isolation_failure_delay':('ISO-FAIL-DELAY','float',1,3600),
            'valve_failure_delay':('VALVE-FAIL-DELAY','float',1,3600),'valve_deviation':('VALVE-DEVIATION','float',0.1,100),
            'lowflow_setpoint':('LOWFLOW-SP','float',0,100),'lowflow_delay':('LOWFLOW-DELAY','float',1,3600),
            'temperature_alarm_delay':('CT-TEMP-ALM-DELAY','float',1,3600),'dp_alarm_delay':('CT-DP-ALM-DELAY','float',1,3600),
            'btu_high_percent':('BTU-HIGH-PERCENT','float',0.1,100)}
def ef_settings():
    return {'proof_delay':(MAIN+'.536_10001.2_10012','float',1,3600),
            'runtime_limit_hours':(MAIN+'.2_10069','float',1,1e7),
            'pressure_minimum':('8-1/0_10008:1295','float',-100,100),
            'pressure_maximum':('8-1/0_10008:1296','float',-100,100)}

def verify_assets(cat):
    for name,want in cat['asset_sha256'].items():
        path=(ROOT/name).resolve()
        if ROOT not in path.parents or not path.is_file() or sha(path)!=want:raise ValueError('Retained asset integrity failed: '+name)

def stage_repo(dest):
    scripts=dest/'caf-engineering-reference/scripts/research';scripts.mkdir(parents=True)
    for file in (ROOT/'assets/runtime').glob('*.py'):shutil.copy2(file,scripts/file.name)
    target=dest/'caf-engineering-reference/examples/ahu-1/AHU-1_latest_AvgControlRedirect_VERIFIED-OPEN.caf'
    target.parent.mkdir(parents=True);shutil.copy2(ROOT/'assets/native/CGM09090_AHU_10.8.caf',target)
    return dest

def patch_candidate(source,dest,edits,archive_template=None):
    """Replace only known object properties; preserve other object bytes and ZIP metadata."""
    with ZipFile(source) as z:info=z.infolist()[0];comment=z.comment;xml=z.read(info.filename)
    if archive_template is not None:
        with ZipFile(archive_template) as z:info=z.infolist()[0];comment=z.comment
    external_attr=info.external_attr
    root=E.fromstring(xml);by={o.get('ref'):o for o in root.findall(N+'object')}
    records={m.group(1).decode():m.group(0) for m in re.finditer(rb'<object\s+ref="([^"]+)"[^>]*>.*?</object>',xml,re.S)}
    for ref,pid,kind,value,attrs in edits:
        if ref not in by:raise ValueError('Missing known object '+ref)
        original=records[ref];replacement=original
        node=E.Element(N+kind,nsmap={None:N[1:-1]},**attrs);node.text=str(value)
        existing=by[ref].find(N+f'property[@id="{pid}"]')
        new=E.Element(N+'property',nsmap={None:N[1:-1]},id=str(pid));data=E.SubElement(new,N+'data');data.append(node)
        b=E.tostring(new,with_tail=False)
        if existing is None:replacement=replacement.replace(b'</object>',b+b'</object>')
        else:
            pattern=rb'<property\b[^>]*\bid="'+str(pid).encode()+rb'"[^>]*>.*?</property>'
            replacement,count=re.subn(pattern,lambda _:b,replacement,count=1,flags=re.S)
            if count!=1:raise ValueError('Missing exact property bytes '+ref+':'+str(pid))
        replacement=re.sub(rb'<simulationProperty id="'+str(pid).encode()+rb'">.*?</simulationProperty>',b'',replacement,flags=re.S)
        if xml.count(original)!=1:raise ValueError('Ambiguous object byte scope')
        xml=xml.replace(original,replacement,1);records[ref]=replacement
        # Keep existence map current for multiple edits to the same property/object.
        by[ref]=E.fromstring(b'<objects xmlns="'+N[1:-1].encode()+b'">'+replacement+b'</objects>')[0]
    root=E.fromstring(xml);by={o.get('ref'):o for o in root.findall(N+'object')}
    for ref,o in by.items():
        ids=[p.get('id') for p in o.findall(N+'property')]
        if len(ids)!=len(set(ids)):raise ValueError('Duplicate properties in '+ref)
    with ZipFile(dest,'w') as z:
        z.comment=comment;z.writestr(info,xml)
        # CPython substitutes 0600 for zero external_attr; restore before central directory writing.
        info.external_attr=external_attr
    return by

def build(spec_path,out):
    spec=json.loads(spec_path.read_text());cat=library();decision=plan(spec,cat)
    if decision['missing_capabilities']:raise ValueError(json.dumps(decision,indent=2))
    verify_assets(cat)
    if out.exists() and any(out.iterdir()):raise ValueError('Use a fresh/empty output directory')
    out.mkdir(parents=True,exist_ok=True)
    profile=next(p for p in cat['profiles'] if p['id']==decision['profile_id'])
    recipe=next(p for p in cat['recipes'] if p['id']==decision['recipe'])
    inputs={p['role']:p for p in spec['points']};edits=[]
    final=out/(re.sub('[^A-Za-z0-9_-]+','_',spec['project']['name']).strip('_')+'_CCT_TEST.caf')
    with tempfile.TemporaryDirectory(prefix='caf-retained-build-') as work:
        tmp=Path(work);repo=stage_repo(tmp/'reference')
        sys.path.insert(0,str(repo/'caf-engineering-reference/scripts/research'))
        if recipe['id'].startswith('ct-chws'):
            impl=load_module('retained_ct_builder',ROOT/'assets/runtime/build_ct_chws_candidate.py')
            with contextlib.redirect_stdout(io.StringIO()):baseline=impl.build(ROOT/profile['asset'],repo,tmp/'generated')
            native_manifest=json.loads((baseline.parent/'CT_CHWS_R1_Manifest.json').read_text())
            original_mappings={p['name']:p for p in native_manifest['point_mapping']}
            for role,binding in recipe['point_roles'].items():
                name=inputs[role]['name']
                if 'physical_ref' in binding:
                    for ref in [binding['physical_ref'],binding['proxy_ref']]:
                        edits += [(ref,2390,'string',name,{}),(ref,28,'string',name,{})]
                else:edits.append((binding['interface_ref'],28,'string','SIMULATION ONLY; missing physical input '+name,{}))
                original_mappings[binding['original_name']]['name']=name
            allowed=ct_settings()
            with ZipFile(baseline) as z:tree=E.fromstring(z.read(z.namelist()[0]))
            by={o.get('ref'):o for o in tree.findall(N+'object')}
            for key,value in spec.get('settings',{}).items():
                selector,kind,*_=allowed[key]
                refs=[selector] if selector in by else [ref for ref,o in by.items() if prop(o,2390) is not None and prop(o,2390).text==selector]
                if len(refs)!=1:raise ValueError('Ambiguous setting interface '+selector)
                edits.append((refs[0],3113,kind,value,{}))
        else:
            baseline=ROOT/profile['asset'];native_manifest={'point_mapping':[],'open_items':list(recipe['known_gaps']),'status':'PARTIAL_CANDIDATE_CCT_NOT_EXECUTED'}
            for role,binding in recipe['point_roles'].items():
                name=inputs[role]['name']
                for ref in [binding['physical_ref'],binding['proxy_ref']]:edits += [(ref,2390,'string',name,{}),(ref,28,'string',name,{})]
                if 'readback_ref' in binding:edits.append((binding['readback_ref'],2390,'string',name+'-EC',{}))
                native_manifest['point_mapping'].append({**binding,'name':name,'status':'candidate_mapping_CCT_verification_required'})
            edits += [(MAIN+'.19_10055',3113,'enum',0,{'set':'647'}),(MAIN+'.5_10093',3113,'boolean','false',{})]
            for key,value in spec.get('settings',{}).items():
                selector,kind,*_=ef_settings()[key];ref,_,pid=selector.partition(':');edits.append((ref,int(pid) if pid else 3113,kind,value,{}))
            native_manifest['guard']='EF-SCHED stored Off (enum 647=0), RUNTIME-RESET False. Native command schedule remains external.'
            native_manifest['native_functions_not_executed']=['SideLoop Command class 540','Status Alarm native FSM','Runtime Alarm native graph','Totalization class 591','Hardware scaling and outputs']
            native_manifest['physical_inputs_missing']=0;native_manifest['hardwired_points_mapped']=3
        edits += [('8-1',2390,'string',spec['project']['name'],{}),(MAIN,2390,'string',spec['project']['name'],{})]
        by=patch_candidate(baseline,final,edits,ROOT/profile['asset'])
        constructor_commit=native_manifest.pop('repository_commit',None)
        native_manifest.update(constructor_reference_commit=constructor_commit,retained_library_reference_commit=cat['reference_commit'],factory_sha256=sha(Path(__file__)),output_sha256=sha(final),output_objects=len(by),source_sha256=profile['sha256'],profile_id=profile['id'],recipe=recipe['id'],project_spec=spec,new_CAF_upload_required=False,native_CCT_executed=False,control_behavior_verified=False,native_identity_retained=True,status='PARTIAL_CANDIDATE_CCT_NOT_EXECUTED',spec_property_edits=[{'ref':r,'property':p,'kind':k,'value':v} for r,p,k,v,a in edits],planning=decision)
        manifest=out/'CAF_Manifest.json';manifest.write_text(json.dumps(native_manifest,indent=2)+'\n')
        subprocess.run([sys.executable,str(ROOT/'scripts/caf_preflight.py'),str(final),'--class-cache',str(ROOT/'assets/native/classCache-10.8.xml'),'--report',str(out/'preflight.json')],check=True,capture_output=True,text=True)
        if recipe['id'].startswith('ct-chws'):
            subprocess.run([sys.executable,str(ROOT/'assets/runtime/verify_ct_chws_candidate.py'),str(final),str(manifest),str(repo),str(out/'model-checks.json')],check=True,capture_output=True,text=True)
    provenance={'status':native_manifest['status'],'caf':str(final.resolve()),'caf_sha256':sha(final),'source_profile':profile['id'],'source_sha256':profile['sha256'],'spec_sha256':sha(spec_path),'new_CAF_upload_required':False,'native_CCT_executed':False,'complete_submittal_implemented':False,'preflight':json.loads((out/'preflight.json').read_text())['status'],'model_scope':'25 custom CT model groups only' if recipe['id'].startswith('ct-chws') else 'Native fan functions not independently modeled; static-only candidate'}
    (out/'build-result.json').write_text(json.dumps(provenance,indent=2)+'\n')
    return provenance

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('catalog')
    for command in ['plan','build']:
        c=sub.add_parser(command);c.add_argument('spec',type=Path)
        if command=='build':c.add_argument('output',type=Path)
    a=p.parse_args()
    try:
        if a.command=='catalog':result=library()
        elif a.command=='plan':result=plan(json.loads(a.spec.read_text()))
        else:result=build(a.spec,a.output)
        print(json.dumps(result,indent=2))
    except (ValueError,KeyError,subprocess.CalledProcessError) as e:
        print(json.dumps({'status':'BUILD_NOT_COMPLETED','error':str(e)},indent=2),file=sys.stderr);return 2
    return 0
if __name__=='__main__':raise SystemExit(main())
