import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('factory',ROOT/'scripts/caf_from_spec.py')
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)

def example(name):return json.loads((ROOT/'references'/name).read_text())
def objects(caf):
    with ZipFile(caf) as z:return {o.get('ref'):o for o in E.fromstring(z.read(z.namelist()[0])).findall(f.N+'object')}

class RetainedWorkflowTests(unittest.TestCase):
    def test_all_retained_asset_hashes(self):f.verify_assets(f.library())
    def test_no_matching_model_and_release_are_capability_gaps(self):
        for model,release in [('M4-CGE09090-1','10.8'),('M4-CGE09090-0','11.0')]:
            x=example('ct-chws-example-spec.json');x['controller'].update(model=model,release=release)
            p=f.plan(x);self.assertEqual(p['status'],'NEEDS_CAPABILITY_WORK');self.assertFalse(p['new_CAF_upload_required'])
    def test_retained_profile_is_not_arbitrary_recipe_support(self):
        x=example('ct-chws-example-spec.json');x['controller']['model']='M4-CGM09090-0'
        self.assertEqual(f.plan(x)['missing_capabilities'][0]['kind'],'recipe')
    def test_omitted_release_is_an_explicit_authoring_assumption(self):
        x=example('single-fan-example-spec.json');del x['controller']['release']
        p=f.plan(x);self.assertFalse(p['missing_capabilities']);self.assertTrue(p['assumptions'])
    def test_hardware_topology_terminal_kind_extra_point_and_feature_mismatches(self):
        variants=[]
        x=example('single-fan-example-spec.json');x['controller']['expansions']=[{'model':'XPM04060','sa_address':4}];variants.append(x)
        x=example('single-fan-example-spec.json');x['points'][0]['terminal']='BI-2';variants.append(x)
        x=example('single-fan-example-spec.json');x['points'][0]['kind']='AI';variants.append(x)
        x=example('single-fan-example-spec.json');x['points'].append({'role':'extra','name':'EXTRA'});variants.append(x)
        x=example('single-fan-example-spec.json');x['requested_features'].append('fire_shutdown');variants.append(x)
        for x in variants:self.assertTrue(f.plan(x)['missing_capabilities'])
    def test_unsupported_electrical_signal_is_not_silently_reused(self):
        x=example('single-fan-example-spec.json');x['points'][1]['signal']='current_4_20'
        self.assertIn('signal_variant',[p['kind'] for p in f.plan(x)['missing_capabilities']])
    def test_invalid_setting_names_ranges_and_nonfinite_values(self):
        for value in [-1,float('nan'),True]:
            x=example('single-fan-example-spec.json');x['settings']['proof_delay']=value
            with self.assertRaises(ValueError):f.plan(x)
        x=example('single-fan-example-spec.json');x['settings']['invented_delay']=1
        with self.assertRaises(ValueError):f.plan(x)
    def test_duplicate_names_and_bad_span_fail_before_generation(self):
        x=example('single-fan-example-spec.json');x['points'][1]['name']=x['points'][0]['name']
        with self.assertRaises(ValueError):f.plan(x)
        x=example('single-fan-example-spec.json');x['settings']['pressure_minimum']=1
        with self.assertRaises(ValueError):f.plan(x)
    def test_partial_feature_deferral_and_unapplied_identity_are_explicit(self):
        x=example('single-fan-example-spec.json');x['requested_features'].append('fire_shutdown')
        x['deferred_features']=[{'feature':'fire_shutdown','reason':'No approved safety wiring/policy supplied','requirements':['R9']}]
        x['controller']['device_instance']=1234
        p=f.plan(x);self.assertFalse(p['missing_capabilities']);self.assertEqual(p['deferred_features'],x['deferred_features'])
        self.assertTrue(any('device_instance' in v for v in p['known_gaps']))
    def test_integrity_failure_is_detected(self):
        c=f.library();key=next(iter(c['asset_sha256']));c['asset_sha256'][key]='0'*64
        with self.assertRaisesRegex(ValueError,'integrity failed'):f.verify_assets(c)
    def test_unsupported_build_writes_no_CAF(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);x=example('single-fan-example-spec.json');x['points'][0]['terminal']='BI-2';spec=p/'spec.json';spec.write_text(json.dumps(x))
            with self.assertRaises(ValueError):f.build(spec,p/'out')
            self.assertFalse((p/'out').exists())
    def test_fan_build_from_spec_reproduces_and_preserves_hardware(self):
        source=ROOT/'assets/native/CGM04060_EF_10.8.caf';before=source.read_bytes();old=objects(source)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);spec=p/'spec.json';spec.write_text(json.dumps(example('single-fan-example-spec.json')))
            a=f.build(spec,p/'one');b=f.build(spec,p/'two');self.assertEqual(a['caf_sha256'],b['caf_sha256'])
            new=objects(Path(a['caf']));
            for o in new.values():
                ids=[p.get('id') for p in o.findall(f.N+'property')];self.assertEqual(len(ids),len(set(ids)))
            self.assertEqual(len(old),len(new));self.assertEqual(set(old),set(new))
            self.assertEqual(f.prop(new['8-1'],70).text,'M4-CGM04060-0')
            for ref,pid,value in [('8-1/575_1.19_10055',3113,'0'),('8-1/575_1.5_10093',3113,'false'),('8-1/575_1.536_10001.2_10012',3113,'45'),('8-1/575_1.2_10069',3113,'1800'),('8-1/0_10008',1296,'0.5')]:self.assertEqual(f.prop(new[ref],pid).text,value)
            for pid in [3926,3927,3118,3384]:self.assertEqual(E.tostring(f.prop(old[f.MAIN],pid)),E.tostring(f.prop(new[f.MAIN],pid)))
            for ref in ['8-1/3_9442','8-1/0_10008','8-1/4_10049']:
                for pid in [75,31,519 if old[ref].get('classid') in ['240','242'] else 990]:self.assertEqual(E.tostring(f.prop(old[ref],pid)),E.tostring(f.prop(new[ref],pid)))
            self.assertFalse(a['new_CAF_upload_required']);self.assertFalse(a['native_CCT_executed']);self.assertEqual(a['preflight'],'STATIC_PASS_CCT_NOT_EXECUTED')
            with self.assertRaises(ValueError):f.build(spec,p/'one')
            with ZipFile(source) as z, ZipFile(a['caf']) as zz:
                self.assertEqual(z.comment,zz.comment)
                for key in ['filename','date_time','compress_type','comment','extra','create_system','create_version','extract_version','flag_bits','volume','internal_attr','external_attr']:
                    self.assertEqual(getattr(z.infolist()[0],key),getattr(zz.infolist()[0],key),key)
        self.assertEqual(source.read_bytes(),before)
    def test_ct_custom_build_with_names_and_settings_has_25_scoped_model_groups(self):
        x=example('ct-chws-example-spec.json');x['project']['name']='TEST CHWS'
        # Swap names as well as rename to catch cascading name-based remap errors.
        x['points'][0]['name'],x['points'][1]['name']=x['points'][1]['name'],x['points'][0]['name']
        x['settings']={'pump_minimum_speed':23,'lwt_setpoint':62}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);spec=p/'spec.json';spec.write_text(json.dumps(x));r=f.build(spec,p/'out');m=json.loads((p/'out/CAF_Manifest.json').read_text())
            model=json.loads((p/'out/model-checks.json').read_text());self.assertEqual(model['scenario_groups'],25)
            self.assertFalse(model['native_CCT_executed']);self.assertFalse(model['whole_control_system_simulated'])
            by=objects(Path(r['caf']));
            for o in by.values():
                ids=[p.get('id') for p in o.findall(f.N+'property')];self.assertEqual(len(ids),len(set(ids)))
            self.assertEqual(f.prop(by['8-1/0_1356'],2390).text,x['points'][0]['name']);self.assertEqual(f.prop(by['8-1/0_1355'],2390).text,x['points'][1]['name'])
            self.assertEqual(f.prop(by[f.MAIN+'.2_259'],3113).text,'62')
            mins=[o for o in by.values() if f.prop(o,2390) is not None and f.prop(o,2390).text=='PUMP-MIN-SPEED'];self.assertEqual(len(mins),1);self.assertEqual(f.prop(mins[0],3113).text,'23')
            self.assertEqual(sum('physical_ref' in v for v in m['point_mapping']),20);self.assertEqual(m['physical_inputs_missing'],15)
            self.assertEqual(f.prop(by[f.MAIN+'.5_85'],3113).text,'false')
            ready=[o for o in by.values() if f.prop(o,2390) is not None and f.prop(o,2390).text=='CONFIGURATION-READY'];self.assertEqual(f.prop(ready[0],3113).text,'false')
            self.assertEqual(m['output_sha256'],r['caf_sha256'])
            self.assertEqual(m['constructor_reference_commit'],'c715dbfe9f3f9bb2a38dbd631b797d8afbfbd598')
            self.assertEqual(m['retained_library_reference_commit'],'2082a82adcb2022649935d5855bfd05336f33947')
            with ZipFile(ROOT/'assets/native/CGE09090_CT_CHWS_10.8.caf') as a, ZipFile(r['caf']) as b:
                self.assertEqual(a.infolist()[0].external_attr,b.infolist()[0].external_attr)
if __name__=='__main__':unittest.main()
