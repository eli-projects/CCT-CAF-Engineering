"""Minimal main-diagram wire redirects from obsolete ZN T/H to validated Activity average outputs.

Based on CAF that the user personally opened AND simulated successfully: temperature 70 F,
humidity 50%RH and CO2 900 ppm. Make no object additions/removals, sensor address
changes, or changes to nested Unit Enable Determination module.
"""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import re, hashlib

D=Path('/mnt/data')
SRC=D/'AHU-1_AVG-ZN-H_CO2_Cloned_3Sensor_Wiring_EXPERIMENT.caf'
DEST=D/'AHU-1_AVG_T_H_Control_Redirect_TEST.caf'
N='{http://johnsoncontrols.com/MetasysIII/2002/3/Core}'
with ZipFile(SRC) as z:
    assert z.testzip() is None
    assert len(z.infolist())==1
    info=z.infolist()[0]
    xml=z.read(info.filename)

def objs(buf):
    rt=E.fromstring(buf)
    object_list=rt.findall(N+'object')
    mp={o.get('ref'):o for o in object_list}
    assert len(mp)==len(object_list), 'Duplicate object refs'
    return rt, mp

def prop(o,i):
    x=o.find(f"{N}property[@id='{i}']/{N}data")
    assert x is not None and len(x)==1,(o.get('ref'),i)
    return x[0]

def diagram_edges(main):
    return [[int(t.text) for t in row.iter(N+'unsignedShort')] for row in prop(main,3118)]

orig_rt, old_objects=objs(xml)
main_ref='8-1/575_1'
main=old_objects[main_ref]
blocks=prop(main,3375)
assert len(old_objects)==2167
assert len(blocks)==len(prop(main,3117))==len(prop(main,3383))==108
assert len(prop(main,3118))==len(prop(main,3384))==140
for idx,cid,oid,lab in [(63,556,10002,'ZN-T'),(64,556,10006,'ZN-H'),(105,536,86471,'AVG-ZN-T'),(106,536,86472,'AVG-ZN-H'),(107,536,86473,'AVG-ZN-CO2')]:
    b=blocks[idx]
    assert (int(b.get('id')),int(b.text))==(cid,oid), (idx,E.tostring(b))
    pt=old_objects[f'{main_ref}.{cid}_{oid}']
    assert prop(pt,2390).text==lab
assert [int(n.text) for n in prop(old_objects[f'{main_ref}.536_86471'],3184)]==[7000,7001,8000,7002]
assert [int(n.text) for n in prop(old_objects[f'{main_ref}.536_86472'],3184)]==[7000,7001,8000,7002]
old_edges=diagram_edges(main)
# Existing ZN-T and ZN-H connections to main control modules.
# Preserve source output port and destination port; only change source block index.
edge_idxs={108:(63,105),109:(63,105),110:(63,105),111:(64,106),112:(64,106),114:(64,106)}
expect_destination={108:(19,7001),109:(58,7000),110:(60,7000),111:(33,7003),112:(62,7000),114:(68,7003)}
new_edges=[edge.copy() for edge in old_edges]
for edge_idx,(before,after) in edge_idxs.items():
    old=old_edges[edge_idx]
    dst=expect_destination[edge_idx]
    assert old==[before,8000,*dst], (edge_idx,old)
    new_edges[edge_idx][0]=after
assert old_edges[113]==[59,50032,65,7000] # old OCC display, unchanged
assert old_edges[130]==[103,8000,59,3110] # original TOCC link, unchanged
assert old_edges[131:140]==[[87,8000,105,7000],[91,8000,105,7001],[95,8000,105,7002],[86,8000,106,7000],[90,8000,106,7001],[94,8000,106,7002],[85,8000,107,7000],[89,8000,107,7001],[93,8000,107,7002]]
# A diagram connection is serialized with four unsignedShort nodes. Replace byte-exact
# nested record in the main diagram only. Avoid XML parsing/re-serialization to preserve
# whitespace, namespaces, encoding, ordering, and all opaque data.
root_match=re.search(rb'<object ref="8-1/575_1" classid="575"[^>]*>.*?</object>',xml,re.S)
assert root_match is not None
raw_main=root_match.group(0)
wire_container_re=rb'(<property id="3118"><data><array>)(.*?)(</array></data></property>)'
wire_match=re.search(wire_container_re,raw_main,re.S)
assert wire_match is not None and len(re.findall(wire_container_re,raw_main,re.S))==1
wire_data=wire_match.group(2)
wire_regex=rb'<struct>(?:<structElement><unsignedShort>\d+</unsignedShort></structElement>){4}</struct>'
wire_matches=list(re.finditer(wire_regex,wire_data))
assert len(wire_matches)==len(old_edges)==140

def serialize(edge):
    return b'<struct>'+b''.join(b'<structElement><unsignedShort>'+str(v).encode()+b'</unsignedShort></structElement>' for v in edge)+b'</struct>'
assert [w.group(0) for w in wire_matches]==[serialize(edge) for edge in old_edges], 'unexpected wire serialization'
new_wires=b''.join(serialize(new_edges[i]) for i in range(len(new_edges)))
assert len(new_wires)==len(wire_data)+len(edge_idxs), 'Expected +1 digit per source block index' 
new_main=raw_main[:wire_match.start(2)]+new_wires+raw_main[wire_match.end(2):]
changed=xml[:root_match.start()]+new_main+xml[root_match.end():]
assert len(changed)==len(xml)+len(edge_idxs)
new_rt,new_objects=objs(changed)
assert new_objects.keys()==old_objects.keys()
assert len(new_objects)==2167
assert all(E.tostring(old_objects[ref])==E.tostring(new_objects[ref]) for ref in old_objects if ref!=main_ref)
new_main_obj=new_objects[main_ref]
assert diagram_edges(new_main_obj)==new_edges
assert len(prop(new_main_obj,3118))==len(prop(new_main_obj,3384))==140
assert len(prop(new_main_obj,3375))==len(prop(new_main_obj,3117))==len(prop(new_main_obj,3383))==108
assert all(new_edges[i]==old_edges[i] for i in range(140) if i not in edge_idxs)
assert E.tostring(prop(main,3384))==E.tostring(prop(new_main_obj,3384))
# All existing diagram properties apart from the connection array are identical.
for pp_old in main.findall(N+'property'):
    if pp_old.get('id')=='3118':continue
    pp_new=new_main_obj.find(f"{N}property[@id='{pp_old.get('id')}']")
    assert E.tostring(pp_old)==E.tostring(pp_new), pp_old.get('id')
# Preserve original sensor and nested reference for later separate cleanup
nested='8-1/575_1.536_86467'
assert E.tostring(old_objects[nested])==E.tostring(new_objects[nested])
assert prop(new_objects['8-1/575_1.2_300134'],3113).text=='3600'
# Confirm specific identity and unchanged inner module definitions
assert b'<object ref="8-1/575_1.536_86467.552_10002"' in changed
with ZipFile(DEST,'w') as z:z.writestr(info,changed)
with ZipFile(DEST) as z:
    assert z.testzip() is None
    assert z.read(info.filename)==changed

print('SRC',SRC.name,'sha256',hashlib.sha256(SRC.read_bytes()).hexdigest())
print('OUTPUT',DEST.name,'sha256',hashlib.sha256(DEST.read_bytes()).hexdigest())
print('archive bytes',len(changed),'objects',len(new_objects),'main blocks',len(prop(new_main_obj,3375)),'main wires',len(new_edges))
for i in edge_idxs:
    print('wire',i,old_edges[i],'->',new_edges[i])
print('Unchanged:', '134 other main edges, all 108 diagram blocks, all 2167 object records, nested Unit Enable wiring, all sensors/addresses, CO2 module')
