from pathlib import Path
import json,struct,re
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'memory'
m=json.loads((p/'memory.json').read_text())
assert len((p/'depth.bin').read_bytes())==2*(384*512+192*256)
mask=(p/'mask.bin').read_bytes();assert len(mask)==384*512 and set(mask)<={0,1}
assert m['f']>0 and m['W']==1152 and m['H']==1536
assert (p/'targets.mind').stat().st_size>1000
for file in ['fg.jpg','bg.jpg','memory-target.jpg','index.html']:assert (p/file).stat().st_size>0
assert (ROOT/'m/index.html').exists()
print('PASS: depth grid sizes, masks, calibration, compiled target, static routes')
print('Memory directory bytes:',sum(x.stat().st_size for x in p.iterdir() if x.is_file()))
print('Poster status:',m['posterStatus'])
