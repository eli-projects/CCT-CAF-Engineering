"""Wire numbered zone sensor temperatures to user-built CCT AVG-ZN-T Activity.
No deletion, readdressing, or AHU control consumption of average.
"""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
import re, hashlib
BASE=Path('/mnt/data/AHU-1_Average_3Inputs_CCT.caf')
OUT=Path('/mnt/data/AHU-1_CCT_AVG-ZN-T_3Sensor_Wiring_TEST.caf')
NS='{http://johnsoncontrols.com/MetasysIII/2002/3/Core}'
with ZipFile(BASE) as z:
 info=z.infolist()[0]
 data=z.read(info.filename)
 assert z.testzip() is None

def tag(n):return NS+n

def getp(o,pid):
 p=o.find(f"{NS}property[@id='{pid}']")
 assert p is not None,(o.get('ref'),pid)
 return p.find(NS+'data')[0]

def objs(xml):
 r=etree.fromstring(xml)
 m={o.get('ref'):o for o in r.findall(NS+'object')}
 assert len(m)==2147
 return r,m
r,m=objs(data)
main=m['8-1/575_1']
bs=getp(main,3375)
for i,oid in [(87,300055),(91,300070),(95,300085)]:
 assert bs[i].get('id')=='556' and bs[i].text==str(oid)
 assert getp(m[f'8-1/575_1.556_{oid}'],2390).text in ('ZN1-T','ZN2-T','ZN3-T')
assert bs[105].get('id')=='536' and bs[105].text=='86471'
activity=m['8-1/575_1.536_86471']
assert [n.text for n in getp(activity,3184)]==['7000','7001','8000','7002']
assert [n.text for n in getp(m['8-1/575_1.536_86471.561_265195'],3184)]==['7000','7001','85','7002']
assert len(getp(activity,3118))==len(getp(activity,3384))==4
assert len(getp(main,3118))==len(getp(main,3384))==131
assert len(bs)==len(getp(main,3117))==len(getp(main,3383))==106
added=[[87,8000,105,7000],[91,8000,105,7001],[95,8000,105,7002]]
existing=[[int(v.text) for v in c.iter() if v.tag==tag('unsignedShort')] for c in getp(main,3118)]
for row in added:
 assert row not in existing
 assert all(n.text!=str(row[3]) for n in getp(activity,3184) if False)  # intentionally empty - port existence verified above
# Keep entire XML bytes unchanged except the two append operations in the main diagram.
pat=rb'<object\s+ref="8-1/575_1"\s+classid="575"[^>]*>.*?</object>'
match=re.search(pat,data,flags=re.DOTALL)
assert match
old_obj=match.group(0)
add_conn=b''.join(b'<struct>'+b''.join(b'<structElement><unsignedShort>'+str(v).encode()+b'</unsignedShort></structElement>' for v in edge)+b'</struct>' for edge in added)
add_meta=b'<struct><structElement><boolean>false</boolean></structElement><structElement><string/></structElement></struct>'*len(added)
# Unique 'property id' within main diagram object. No layout/block counts changed.
def append_to_property(xml, propid,closing,payload):
 p=re.compile(rb'(<property id="'+str(propid).encode()+rb'"><data><(?:array|listof)>)(.*?)(</'+closing+rb'></data></property>)',flags=re.DOTALL)
 m=p.search(xml)
 assert m is not None, (propid,'not found')
 assert len(p.findall(xml))==1, (propid,'duplicate props')
 return xml[:m.start(3)]+payload+xml[m.start(3):]
changed_obj=append_to_property(old_obj,3118,b'array',add_conn)
changed_obj=append_to_property(changed_obj,3384,b'listof',add_meta)
new=data[:match.start()]+changed_obj+data[match.end():]
newr,newm=objs(new)
newmain=newm['8-1/575_1']
assert len(getp(newmain,3118))==len(getp(newmain,3384))==134
assert len(getp(newmain,3375))==len(getp(newmain,3117))==len(getp(newmain,3383))==106
newconns=[[int(v.text) for v in c.iter() if v.tag==tag('unsignedShort')] for c in getp(newmain,3118)]
assert newconns==existing+added
assert len(newm)==len(m)==2147 and newm.keys()==m.keys()
# Original root operating edges unchanged; no non-main object changes.
assert all(etree.tostring(m[k])==etree.tostring(newm[k]) for k in m if k!='8-1/575_1')
assert new.replace(add_conn,b'',1).replace(add_meta,b'',1)==data
assert getp(newm['8-1/575_1.2_300134'],3113).text=='3600'
with ZipFile(OUT,'w') as out:
 out.writestr(info,new)
with ZipFile(OUT) as z:
 assert z.testzip() is None
 assert z.read(info.filename)==new
print('output',OUT)
print('original bytes',len(data),'edited',len(new),'added XML bytes',len(new)-len(data))
print('objects',len(m),'main blocks',len(bs),'connections',len(existing),'->',len(newconns),'activity inner connections',len(getp(activity,3118)))
print('added wires',added)
print('SHA256',hashlib.sha256(OUT.read_bytes()).hexdigest())
