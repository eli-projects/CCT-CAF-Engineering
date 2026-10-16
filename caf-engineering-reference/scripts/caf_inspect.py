#!/usr/bin/env python3
"""Read-only, empirical AHU-1-style CAF inspector. No writing to the CAF."""
import argparse, zipfile, json
from pathlib import Path
from xml.etree import ElementTree as ET
N='{http://johnsoncontrols.com/MetasysIII/2002/3/Core}'
def data(obj,pid):
 if obj is None:return None
 q=obj.find(f"{N}property[@id='{pid}']/{N}data")
 return q[0] if q is not None and len(q) else None
def inspect_file(path):
 with zipfile.ZipFile(path) as z:
  bad=z.testzip()
  if bad:raise ValueError('bad CRC entry: '+bad)
  if len(z.namelist())!=1:raise ValueError('This tool supports only single-XML-member CAFs')
  member=z.namelist()[0]
  root=ET.fromstring(z.read(member))
 objs=root.findall(N+'object'); mp={o.get('ref'):o for o in objs}
 if len(mp)!=len(objs):raise ValueError('duplicate ref')
 main=mp.get('8-1/575_1')
 if main is None: raise ValueError('unsupported CAF: expected diagram ref not found')
 b,ordr,geom,wire,meta=[data(main,x) for x in [3375,3117,3383,3118,3384]]
 if None in (b,ordr,geom,wire,meta):raise ValueError('one or more expected diagram properties missing')
 blocks=[]
 for i,item in enumerate(b):
  ref=f"8-1/575_1.{item.get('id')}_{item.text}"
  name=data(mp.get(ref),2390)
  ports=data(mp.get(ref),3184)
  blocks.append({'index':i,'ref':ref,'class_id':item.get('id'),'id':item.text,'name':name.text if name is not None else None,'ports':[x.text for x in ports] if ports is not None else None})
 edges=[[int(v.text) for v in c.iter(N+'unsignedShort')] for c in wire]
 return {'file':str(path),'member':member,'object_count':len(objs), 'main_blocks':len(b),'main_order':len(ordr),'main_geometry':len(geom),'main_connections':len(wire),'main_connection_meta':len(meta),'block_array_lengths_consistent':len(b)==len(ordr)==len(geom),'edge_meta_lengths_consistent':len(wire)==len(meta),'blocks':blocks,'connections':[{'idx':i,'src':e[0], 'src_name':blocks[e[0]]['name'] if e[0]<len(blocks) else None,'src_port':e[1], 'dst':e[2], 'dst_name':blocks[e[2]]['name'] if e[2]<len(blocks) else None,'dst_port':e[3]} for i,e in enumerate(edges)]}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('caf',type=Path);a.add_argument('--summary',action='store_true');args=a.parse_args()
 result=inspect_file(args.caf)
 if args.summary:result={k:v for k,v in result.items() if k not in ('blocks','connections')}
 print(json.dumps(result,indent=2))
