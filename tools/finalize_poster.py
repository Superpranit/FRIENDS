"""Build a QR print only when the real public destination is known.
Usage: python tools/finalize_poster.py https://USERNAME.github.io/REPO/m/
Then compile the updated target with tools/compile-target.html.
"""
import sys,json,io
from pathlib import Path
from urllib.parse import urlparse
import numpy as np
import cv2,qrcode,zxingcpp
from PIL import Image,ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
ROOT=Path(__file__).resolve().parents[1]
url=sys.argv[1] if len(sys.argv)>1 else ''
if urlparse(url).scheme!='https' or not urlparse(url).netloc or any(v in url for v in ['<','>','USERNAME','REPO']):
 raise SystemExit('Supply the real HTTPS public URL. No placeholder QR will be produced.')
base=Image.open(ROOT/'artwork/memory-box-poster-proof.jpg').convert('RGB')
qr=qrcode.QRCode(version=4,error_correction=qrcode.constants.ERROR_CORRECT_Q,border=4,box_size=12);qr.add_data(url);qr.make(fit=True)
matrix=np.array(qr.get_matrix());n=len(matrix);module=13;size=n*module;x0=base.width-size-135;y0=160
# Four-module quiet zone, squared finder/timing/alignment patterns for reliability.
def candidate(dark):
 a=np.array(base).astype(float);region=a[y0:y0+size,x0:x0+size].copy();overlay=Image.new('L',(size,size));draw=ImageDraw.Draw(overlay)
 for y in range(n):
  for x in range(n):
   if not matrix[y,x]:continue
   xx=x-4;yy=y-4;inner=n-8
   functional=(xx<9 and yy<9) or (xx>=inner-8 and yy<9) or (xx<9 and yy>=inner-8) or xx==6 or yy==6 or (abs(xx-(inner-7))<=2 and abs(yy-(inner-7))<=2)
   box=(x*module,y*module,(x+1)*module,(y+1)*module)
   if functional:draw.rectangle(box,fill=255)
   else:draw.ellipse((box[0]+module*.04,box[1]+module*.04,box[2]-module*.04,box[3]-module*.04),fill=255)
 weight=np.array(overlay)/255
 region*=1-weight[:,:,None]*dark;a[y0:y0+size,x0:x0+size]=region
 return np.uint8(np.clip(a,0,255))
def simulate(im,close,seed):
 rng=np.random.default_rng(seed)
 if close:im=im[max(0,y0-100):y0+size+100,x0-100:x0+size+100]
 height=1100 if close else 1500;width=round(height*im.shape[1]/im.shape[0]);im=cv2.resize(im,(width,height),interpolation=cv2.INTER_AREA)
 a=np.float32([[0,0],[width-1,0],[width-1,height-1],[0,height-1]])
 jitter=rng.uniform(-.025,.025,(4,2))*[width,height];b=(a+jitter).astype(np.float32)
 im=cv2.warpPerspective(im,cv2.getPerspectiveTransform(a,b),(width,height),borderMode=cv2.BORDER_REPLICATE)
 im=cv2.GaussianBlur(im,(0,0),rng.uniform(.8,1.8));im=im.astype(float)*rng.uniform(.88,1.10)*rng.uniform(.97,1.03,(1,1,3))+rng.normal(0,1.5,im.shape)
 im=np.uint8(np.clip(im,0,255));ok,buf=cv2.imencode('.jpg',im[:,:,::-1],[cv2.IMWRITE_JPEG_QUALITY,int(rng.integers(70,91))]);return cv2.imdecode(buf,cv2.IMREAD_COLOR)[:,:,::-1]
def evaluate(im):
 result={}
 for close,count in [(True,30),(False,20)]:
  z=0;c=0
  for i in range(count):
   sample=simulate(im,close,1000+i+int(close)*100);reads=zxingcpp.read_barcodes(sample);z+=any(r.text==url for r in reads)
   try:c+=cv2.QRCodeDetector().detectAndDecode(sample)[0]==url
   except cv2.error:pass
  result['close' if close else 'whole']={'trials':count,'zxing_passes':z,'opencv_passes':c}
 return result
for contrast in [.30,.38,.46,.55,.65,.75]:
 im=candidate(contrast);result=evaluate(im)
 print('Contrast',contrast,result,flush=True)
 if all(v['zxing_passes']/v['trials']>=.95 and v['opencv_passes']/v['trials']>=.95 for v in result.values()):break
else:raise SystemExit('QR did not reach 95% in both decoders. Enlarge the QR before printing.')
out=ROOT/'artwork/memory-box-poster.jpg';Image.fromarray(im).save(out,quality=97,dpi=(245.364,245.364))
pdf=canvas.Canvas(str(ROOT/'artwork/memory-box-poster.pdf'),pagesize=(30*cm,40*cm));pdf.setTitle('Memory Box');pdf.drawImage(str(out),0,0,30*cm,40*cm);pdf.showPage();pdf.save()
Image.fromarray(im).resize((744,992),Image.Resampling.LANCZOS).save(ROOT/'memory/memory-target.jpg',quality=92)
qr.make_image(fill_color='black',back_color='white').save(ROOT/'memory/qr.png')
p=ROOT/'memory/memory.json';meta=json.loads(p.read_text());meta['publicUrl']=url;meta['posterStatus']='final-qr-target-needs-recompilation';p.write_text(json.dumps(meta,indent=2))
(ROOT/'qa/qr-report.json').write_text(json.dumps({'url':url,'contrast':contrast,'version':qr.version,'results':result,'simulationOnly':True},indent=2))
print('Poster generated. Recompile targets.mind before deploying. Verify scanning on a real printed copy.')
