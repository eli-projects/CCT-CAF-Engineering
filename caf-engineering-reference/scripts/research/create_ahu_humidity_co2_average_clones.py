"""Create experimental CCT native averaging module clones using entirely byte-preserving CAF XML edits.

Base CAF was CCT-validated by user (AVG-ZN-T with 3 sensors calculating 70 for 60/70/80).
No plant control consumption, zone sensor deletion, or address changes are made.
"""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from collections import Counter
import re, hashlib, csv

DATA=Path('/mnt/data')
BASE=DATA/'AHU-1_CCT_AVG-ZN-T_3Sensor_Wiring_TEST.caf'
N='{http://johnsoncontrols.com/MetasysIII/2002/3/Core}'
with ZipFile(BASE) as z:
 info=z.infolist()[0]; original=z.read(info.filename)
 assert z.testzip() is None

ORIGINAL_XML=E.fromstring(original)
OBJS={o.get('ref'):o for o in ORIGINAL_XML.findall(N+'object')}
assert len(OBJS)==2147

MODULE='8-1/575_1.536_86471'
START=b'<object ref="8-1/575_1.536_86471"'
END=b'<object ref="8-1/575_1.536_86470"'
s=original.index(START);e=original.index(END,s)
template=original[s:e]
assert len(re.findall(rb'<object\s+ref=',template))==10
assert b'AVG-ZN-T' in template
assert template.startswith(START)
assert b'</object>' in template
assert b'86470' not in template

# maps are unique across whole document; preserve base object instances
MAPS={
 'H': {'id':86472,'calc':265250, 'pointmap': dict(zip([300173,300174,300175,300176,300177,300178,300179,300181],range(300200,300208))), 'name':'AVG-ZN-H', 'sources':[86,90,94], 'index':106},
 'CO2': {'id':86473,'calc':265251, 'pointmap': dict(zip([300173,300174,300175,300176,300177,300178,300179,300181],range(300208,300216))), 'name':'AVG-ZN-CO2', 'sources':[85,89,93], 'index':107},
}
for name,spec in MAPS.items():
 for v in [spec['id'],spec['calc'], *spec['pointmap'].values()]:
  assert not re.search(rb'(?<![0-9])'+str(v).encode()+rb'(?![0-9])',original),(name,v)

def encode_module(spec):
 mp={86471:spec['id'],265195:spec['calc'],**spec['pointmap']}
 out=template
 for a,b in mp.items():
  pat=rb'(?<![0-9])'+str(a).encode()+rb'(?![0-9])'
  assert re.search(pat,out),a
  out=re.sub(pat,str(b).encode(),out)
 assert out.count(b'AVG-ZN-T')==1
 out=out.replace(b'AVG-ZN-T',spec['name'].encode())
 assert len(re.findall(rb'<object\s+ref=',out))==10
 assert b'86471' not in out and b'265195' not in out
 return out

def raw_struct(*terms):
 return b'<struct>'+b''.join(b'<structElement><unsignedShort>'+str(term).encode()+b'</unsignedShort></structElement>' for term in terms)+b'</struct>'

def raw_position(x,y,k=12):
 return (b'<struct><structElement><float>'+str(x).encode()+b'</float></structElement>'
         b'<structElement><float>'+str(y).encode()+b'</float></structElement>'
         b'<structElement><unsignedShort>'+str(k).encode()+b'</unsignedShort></structElement></struct>')

meta=b'<struct><structElement><boolean>false</boolean></structElement><structElement><string/></structElement></struct>'

# main diagram edits are made without reserializing XML
pat=rb'<object ref="8-1/575_1" classid="575"[^>]*>.*?</object>'
match=re.search(pat,original,re.DOTALL)
assert match
main_raw=match.group(0)

def append_prop(source,pid,term,payload):
 regex=rb'(<property id="'+str(pid).encode()+rb'"><data><(?:array|listof)>)(.*?)(</'+term+rb'></data></property>)'
 matches=list(re.finditer(regex,source,re.DOTALL))
 assert len(matches)==1,(pid,len(matches))
 m=matches[0]
 return source[:m.start(3)]+payload+source[m.start(3):]

def build(which,output):
 specs=[MAPS[name] for name in which]
 cloned=b''.join(encode_module(s) for s in reversed(specs))
 main=main_raw
 # 3117: display-order permutation. CCT inserted index 105 in the middle. Put further indexes next to it.
 displaypat=b'<unsignedShort>105</unsignedShort>'
 # Limit replacement to property 3117, since the main 3118 connection list also contains block index 105.
 prop_re=rb'(<property id="3117"><data><array>)(.*?)(</array></data></property>)'
 pm=re.search(prop_re,main,re.DOTALL)
 assert pm and pm.group(2).count(displaypat)==1
 updated_order=pm.group(2).replace(displaypat,displaypat+b''.join(b'<unsignedShort>'+str(item['index']).encode()+b'</unsignedShort>' for item in specs),1)
 main=main[:pm.start(2)]+updated_order+main[pm.end(2):]
 main=append_prop(main,3375,b'array',b''.join(b'<BACoid id="536">'+str(s['id']).encode()+b'</BACoid>' for s in specs))
 main=append_prop(main,3383,b'listof',b''.join(raw_position(20+i*10,-20-i*10) for i,_ in enumerate(specs)))
 edges=[]
 for spec in specs:
  for source,port in zip(spec['sources'],[7000,7001,7002]):
   edges.append((source,8000,spec['index'],port))
 main=append_prop(main,3118,b'array',b''.join(raw_struct(*edge) for edge in edges))
 main=append_prop(main,3384,b'listof',meta*len(edges))
 new_data=original[:match.start()]+main+original[match.end():]
 # Insert clones immediately before existing CCT module; avoid serializing full CAF XML
 insertion=new_data.index(START)
 new_data=new_data[:insertion]+cloned+new_data[insertion:]
 root=E.fromstring(new_data)
 byref={o.get('ref'):o for o in root.findall(N+'object')}
 assert len(byref)==len(OBJS)+10*len(specs)
 assert len(byref)==len(OBJS)+10*len(specs)
 assert len(byref)==len(root.findall(N+'object'))
 def p(o,pid):
  prop=o.find(f"{N}property[@id='{pid}']")
  assert prop is not None,(o.get('ref'),pid)
  return prop.find(N+'data')[0]
 newmain=byref['8-1/575_1']
 assert len(p(newmain,3375))==len(p(newmain,3117))==len(p(newmain,3383))==106+len(specs)
 assert set(int(n.text) for n in p(newmain,3117))==set(range(106+len(specs)))
 assert len(p(newmain,3118))==len(p(newmain,3384))==134+3*len(specs)
 all_edges=[[int(t.text) for t in connection.iter() if t.tag==N+'unsignedShort'] for connection in p(newmain,3118)]
 assert all_edges[-len(edges):]==[list(x) for x in edges]
 for spec in specs:
  ref=f"8-1/575_1.536_{spec['id']}"; mod=byref[ref]
  assert p(mod,2390).text==spec['name']
  assert len(p(mod,3118))==len(p(mod,3384))==4
  assert len(p(mod,3375))==len(p(mod,3117))==len(p(mod,3383))==5
  assert [i.text for i in p(mod,3184)]==['7000','7001','8000','7002']
  assert [i.text for i in p(byref[ref+f".561_{spec['calc']}"],3184)]==['7000','7001','85','7002']
  assert len([k for k in byref if k==ref or k.startswith(ref+'.')])==10
  # exact CID/OID local reference coverage
  for ptr in p(mod,3375):
   kind=ptr.get('id');oid=ptr.text
   child=f'{ref}.{kind}_{oid}' if kind!='2' else (f'{ref}.2_{oid}' if f'{ref}.2_{oid}' in byref else None)
   assert child in byref,(ref,ptr.attrib,ptr.text)
  for idx,port in zip(spec['sources'],[7000,7001,7002]):
   assert [idx,8000,spec['index'],port] in all_edges
 # old operating objects are byte-identical (including their original CCT native averaging module)
 for key,o in OBJS.items():
  if key!='8-1/575_1':
   assert E.tostring(o)==E.tostring(byref[key]),key
 assert p(byref['8-1/575_1.2_300134'],3113).text=='3600'
 for idx,(c,oid) in {85:(556,300047),86:(556,300051),87:(556,300055),89:(556,300062),90:(556,300066),91:(556,300070),93:(556,300077),94:(556,300081),95:(556,300085)}.items():
  item=p(newmain,3375)[idx]
  assert item.get('id')==str(c) and item.text==str(oid)
 # Baseline byte-exact preservation check, excluding two changes only
 assert new_data.replace(cloned,b'',1).replace(main,main_raw,1)==original
 with ZipFile(output,'w') as z:z.writestr(info,new_data)
 with ZipFile(output) as z:
  assert z.testzip() is None and z.read(info.filename)==new_data
 print(output,'len',len(new_data),'objects',len(byref),'main blocks',len(p(newmain,3375)),'main connections',len(all_edges),'SHA256',hashlib.sha256(output.read_bytes()).hexdigest())
 print('    new edges',edges)
 return new_data

build(['H'],DATA/'AHU-1_AVG-ZN-H_Cloned_3Sensor_Wiring_EXPERIMENT.caf')
build(['H','CO2'],DATA/'AHU-1_AVG-ZN-H_CO2_Cloned_3Sensor_Wiring_EXPERIMENT.caf')
