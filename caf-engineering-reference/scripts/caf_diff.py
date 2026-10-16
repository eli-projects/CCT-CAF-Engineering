#!/usr/bin/env python3
"""Read-only compare CCT CAF object sets, property values, and main-diagram wires."""
import argparse,zipfile,json,hashlib
from pathlib import Path
from xml.etree import ElementTree as ET
N='{http://johnsoncontrols.com/MetasysIII/2002/3/Core}'
def parse(path):
 with zipfile.ZipFile(path) as z:
  if z.testzip() is not None:raise ValueError('corrupted archive')
  if len(z.namelist())!=1:raise ValueError('unsupported multiple archive members')
  root=ET.fromstring(z.read(z.namelist()[0]))
 objs={o.get('ref'):o for o in root.findall(N+'object')}
 return objs

def prop(o):return {p.get('id'):ET.tostring(p,encoding='unicode') for p in o.findall(N+'property')}
def wires(o):
 q=o.find(f"{N}property[@id='3118']/{N}data/{N}array")
 return [[int(t.text) for t in e.iter(N+'unsignedShort')] for e in q] if q is not None else None

def diff(a,b):
 x=parse(a);y=parse(b);added=sorted(y.keys()-x.keys());removed=sorted(x.keys()-y.keys())
 changed=[]
 for ref in sorted(x.keys() & y.keys()):
  ax=prop(x[ref]);by=prop(y[ref]);ids=sorted([v for v in (ax.keys()|by.keys()) if ax.get(v)!=by.get(v)],key=int)
  if ids:changed.append({'ref':ref,'changed_property_ids':ids})
 wa=wires(x.get('8-1/575_1')) if '8-1/575_1' in x else None
 wb=wires(y.get('8-1/575_1')) if '8-1/575_1' in y else None
 wire_changes=[{'idx':i,'old':wa[i] if i<len(wa) else None,'new':wb[i] if i<len(wb) else None} for i in range(max(len(wa),len(wb))) if i>=len(wa) or i>=len(wb) or wa[i]!=wb[i]] if wa is not None and wb is not None else []
 return {'old':str(a),'new':str(b),'old_sha256':hashlib.sha256(a.read_bytes()).hexdigest(),'new_sha256':hashlib.sha256(b.read_bytes()).hexdigest(),'old_objects':len(x),'new_objects':len(y),'added_objects':added,'removed_objects':removed,'changed_objects':changed,'main_connection_changes':wire_changes}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('before',type=Path);p.add_argument('after',type=Path);args=p.parse_args();print(json.dumps(diff(args.before,args.after),indent=2))
