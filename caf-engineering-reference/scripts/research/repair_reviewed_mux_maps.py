"""Apply only the reviewed 36 MUX-map corrections to the exact uploaded CAF."""
import argparse
import hashlib
from pathlib import Path
import re
import xml.etree.ElementTree as E
from zipfile import ZipFile

SOURCE_SHA='d8554931f40cc2d69f515c004964281b6f0c9e1e9dcacf7d1a984e4ac914fe51'
OUTPUT_SHA='46b41438f157068c5546210a54f733859df617abcc2f83a2e6f99ba4afd86a64'
N='{http://johnsoncontrols.com/MetasysIII/2002/3/Core}'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('destination',type=Path)
    args=parser.parse_args()
    assert args.source.resolve()!=args.destination.resolve(),'Keep the source file.'
    assert hashlib.sha256(args.source.read_bytes()).hexdigest()==SOURCE_SHA
    with ZipFile(args.source) as archive:
        assert archive.testzip() is None and len(archive.infolist())==1
        info=archive.infolist()[0];comment=archive.comment;xml=archive.read(info.filename)
    selected=set()
    for obj in E.fromstring(xml).findall(N+'object'):
        ref=obj.get('ref')
        if obj.get('classid')=='562' and any(ref.startswith('8-1/575_1.536_'+str(number)+'.') for number in [500019,500762,400008]):
            selected.add(ref)
    assert len(selected)==36
    def patch(match):
        raw=match.group(0)
        if match.group(1).decode() not in selected:return raw
        for number,data in [(2381,b'<listof><unsignedShort>1</unsignedShort><unsignedShort>2</unsignedShort></listof>'),(3122,b'<unsignedShort>0</unsignedShort>')]:
            raw,count=re.subn(rb'<property id="'+str(number).encode()+rb'">.*?</property>',b'<property id="'+str(number).encode()+b'"><data>'+data+b'</data></property>',raw,flags=re.S)
            assert count==1
        return raw
    fixed=re.sub(rb'<object\s+ref="([^"]+)"[^>]*>.*?</object>',patch,xml,flags=re.S)
    args.destination.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(args.destination,'w') as archive:
        archive.comment=comment;archive.writestr(info,fixed)
    assert hashlib.sha256(args.destination.read_bytes()).hexdigest()==OUTPUT_SHA
    print(f'Wrote {args.destination}; only 36 MUX maps and defaults changed. CCT testing is required.')

if __name__=='__main__':main()
