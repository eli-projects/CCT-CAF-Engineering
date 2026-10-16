from pathlib import Path
from zipfile import ZipFile
from lxml import etree
import hashlib

base=Path('/mnt/data/AHU-1_Temp_Occupancy_Wiring_TEST1.caf')
output=Path('/mnt/data/AHU-1_Phase1_ZN1_TOCC_Redirect_TEST.caf')
ns='{http://johnsoncontrols.com/MetasysIII/2002/3/Core}'
with ZipFile(base) as z:
    assert len(z.infolist())==1
    member=z.infolist()[0]
    xml=z.read(member.filename)

old=(b'<struct><structElement><unsignedShort>102</unsignedShort></structElement>'
     b'<structElement><unsignedShort>8000</unsignedShort></structElement>'
     b'<structElement><unsignedShort>59</unsignedShort></structElement>'
     b'<structElement><unsignedShort>3110</unsignedShort></structElement></struct>')
new=old.replace(b'<unsignedShort>102</unsignedShort>',b'<unsignedShort>103</unsignedShort>',1)
assert xml.count(old)==1, f'Expected exactly one established connection, got {xml.count(old)}'
changed=xml.replace(old,new,1)
root_old=etree.fromstring(xml)
root_new=etree.fromstring(changed)
assert len(root_old.findall(ns+"object"))==len(root_new.findall(ns+"object"))==2137
assert [(o.get('ref'),o.get('classid'),o.get('objectid')) for o in root_old]==[(o.get('ref'),o.get('classid'),o.get('objectid')) for o in root_new]

def main_obj(tree):return next(o for o in tree if o.get('ref')=='8-1/575_1')
def get_arr(obj,pid):return next(p for p in obj if p.get('id')==str(pid))[0][0]
old_obj=main_obj(root_old)
new_obj=main_obj(root_new)
ids=list(get_arr(new_obj,3375))
assert ids[102].get('id')=='556' and ids[102].text=='300140'
assert ids[103].get('id')=='556' and ids[103].text=='300143'
connections=list(get_arr(new_obj,3118))
def vals(c):return [el.text for el in c.iter() if el.tag.endswith('unsignedShort')]
assert sum(vals(c)==['103','8000','59','3110'] for c in connections)==1
assert sum(vals(c)==['102','8000','59','3110'] for c in connections)==0
assert len(connections)==len(get_arr(new_obj,3384))==131
assert len(ids)==len(get_arr(new_obj,3117))==len(get_arr(new_obj,3383))==105
assert len(get_arr(old_obj,3118))==len(connections)
assert changed.replace(new,old,1)==xml
for obj in root_new:
    if obj.get('classid')=='641':
        pass
# Additional verify all sensor config stays same as prior successful test.
for label,oid in [('ZN', '10000'),('ZN1','10004'),('ZN2','10005'),('ZN3','10006')]:
    a=[o for o in root_old if f'.910_{oid}.' in (o.get('ref') or '')]
    b=[o for o in root_new if f'.910_{oid}.' in (o.get('ref') or '')]
    assert len(a)==len(b)
    assert all(etree.tostring(x)==etree.tostring(y) for x,y in zip(a,b)),label
with ZipFile(output,'w') as z:
    z.writestr(member,changed)
with ZipFile(output) as z:
    assert z.testzip() is None and z.read(member.filename)==changed
print('Output',output)
print('Size',output.stat().st_size)
print('sha256',hashlib.sha256(output.read_bytes()).hexdigest())
print('Only changed wire source block: 102 (ZN-TOCC) -> 103 (ZN1-TOCC), temp occupancy input block 59/3110 unchanged')
print('Verified 2137 objects, 105 diagram blocks, 131 connections, 131 connection metadata, unchanged sensor device settings')
