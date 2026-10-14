"""Reconstruct calibrated layered photo assets. No generative face editing."""
import sys,json
from pathlib import Path
import numpy as np
import cv2
from PIL import Image,ImageDraw
from plyfile import PlyData
from scipy.ndimage import distance_transform_edt,median_filter

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'memory'; OUT.mkdir(exist_ok=True)
src=Path(sys.argv[1]); ply=Path(sys.argv[2])
p=PlyData.read(ply)
intr=next(c.split()[1:] for c in p.comments if c.startswith('sharp_intrinsic'))
f,fy,cx,cy=map(float,intr); W,H=map(int,next(c.split()[1:] for c in p.comments if c.startswith('sharp_image_size')))
v=p['vertex'].data; z=v['z']; w,h=384,512
px=np.rint((v['x']/z*f+cx)/W*(w-1)).astype(int)
py=np.rint((v['y']/z*fy+cy)/H*(h-1)).astype(int)
valid=(z>0)&(px>=0)&(px<w)&(py>=0)&(py<h)&(v['opacity']>0)
d=np.full(w*h,np.inf,dtype=np.float32)
np.minimum.at(d,py[valid]*w+px[valid],z[valid]); d=d.reshape(h,w)
missing=~np.isfinite(d)
inds=distance_transform_edt(missing,return_distances=False,return_indices=True)
d[missing]=d[tuple(inds[:,missing])]; d=median_filter(d,size=3)
sky=d>6.3
im=Image.open(src).convert('RGB'); rgb=np.array(im.resize((w,h)))
# Hand-seeded silhouettes refined with GrabCut. Coordinates refer to supplied 1368x1824 image.
polys=[[(0,1182),(183,1072),(220,1017),(281,982),(309,947),(335,924),(373,923),(407,944),(450,993),(487,1020),(474,1088),(421,1106),(388,1094),(330,1198),(282,1324),(232,1324),(226,1224),(213,1162),(153,1201),(0,1256)],[(294,922),(300,867),(324,833),(363,816),(368,779),(397,775),(418,799),(423,831),(448,865),(459,950),(480,979),(514,1025),(580,1011),(576,1043),(543,1080),(502,1098),(453,1088),(422,1012),(399,974),(319,969)],[(536,966),(548,907),(562,871),(566,838),(594,826),(620,830),(643,860),(646,883),(673,899),(690,940),(724,991),(762,1012),(766,1043),(728,1052),(682,1027),(665,1083),(633,1090),(614,1070),(616,1040),(580,1018),(545,1014)],[(656,925),(661,891),(674,865),(690,838),(720,831),(741,846),(753,880),(765,925),(760,959),(786,978),(817,1004),(812,1036),(772,1040),(730,1021),(707,987),(676,967)],[(645,898),(650,849),(668,827),(684,810),(706,805),(729,816),(731,841),(761,860),(783,884),(802,901),(798,915),(774,909),(756,888),(733,884),(697,906),(674,935)],[(790,1027),(808,981),(812,945),(835,926),(869,924),(891,947),(908,974),(942,987),(970,1015),(992,1059),(1005,1091),(1068,1176),(1102,1265),(1169,1310),(1229,1370),(1296,1437),(1281,1473),(1248,1472),(1203,1428),(1161,1406),(1125,1355),(1068,1311),(1009,1287),(937,1219),(884,1151),(847,1139),(815,1108)],[(950,1015),(966,970),(981,937),(989,911),(1013,893),(1042,891),(1065,906),(1075,933),(1061,960),(1083,977),(1115,1028),(1144,1048),(1200,1126),(1241,1170),(1274,1199),(1280,1224),(1252,1237),(1209,1212),(1190,1263),(1160,1268),(1125,1248),(1104,1204),(1064,1168),(1038,1106),(991,1091)]]
seed=np.zeros((h,w),np.uint8)
for poly in polys:
 pts=np.array(poly,np.float32)*[w/1368,h/1824];cv2.fillPoly(seed,[pts.astype(np.int32)],1)
kernel=np.ones((3,3),np.uint8)
gc=np.full((h,w),cv2.GC_BGD,np.uint8)
gc[cv2.dilate(seed,kernel,iterations=2)>0]=cv2.GC_PR_BGD
gc[seed>0]=cv2.GC_PR_FGD;gc[cv2.erode(seed,kernel)>0]=cv2.GC_FGD
cv2.grabCut(rgb,gc,None,np.zeros((1,65)),np.zeros((1,65)),3,cv2.GC_INIT_WITH_MASK)
mask=np.isin(gc,[cv2.GC_FGD,cv2.GC_PR_FGD]).astype(np.uint8)
mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,kernel); mask[sky]=0
mask.tofile(OUT/'mask.bin')
fill=cv2.dilate(mask,kernel,iterations=3)*255
back=cv2.inpaint(d,fill,7,cv2.INPAINT_NS)
back=np.maximum(back,d+np.where(mask>0,.20,.045)).astype(np.float32)
back[sky]=6.45
back=cv2.resize(back,(192,256),interpolation=cv2.INTER_AREA)
def quant(a):
 q=np.rint(np.clip((a-2)/4.5,0,1)*65534).astype('<u2');q[a>6.3]=65535;return q
with open(OUT/'depth.bin','wb') as out:out.write(quant(d).tobytes());out.write(quant(back).tobytes())
def grade(a):
 a=a.astype(np.float32)/255; a=(a-.5)*1.025+.5;a*=np.array([1.012,1.003,.991]);return np.uint8(np.clip(a*255,0,255))
fg=grade(np.array(im.resize((1536,2048),Image.Resampling.LANCZOS)))
Image.fromarray(fg).save(OUT/'fg.jpg',quality=85,optimize=True)
bg=np.array(im.resize((768,1024),Image.Resampling.LANCZOS))
bg=cv2.inpaint(bg,cv2.resize(fill,(768,1024),interpolation=cv2.INTER_NEAREST),9,cv2.INPAINT_TELEA)
Image.fromarray(grade(bg)).save(OUT/'bg.jpg',quality=82,optimize=True)
skycol=np.mean(fg[:700].reshape(-1,3),axis=0)/255
meta=dict(fg=[w,h],bg=[192,256],zmin=2,zrange=4.5,f=f,fy=fy,cx=cx,cy=cy,W=W,H=H,sky=skycol.tolist(),scale=3.37,publicUrl=None,posterStatus='proof-no-qr')
(OUT/'memory.json').write_text(json.dumps(meta,indent=2))
Image.fromarray(fg).resize((744,992),Image.Resampling.LANCZOS).save(OUT/'memory-target.jpg',quality=92)
Image.fromarray(fg).resize((2898,3864),Image.Resampling.LANCZOS).save(ROOT/'artwork/memory-box-poster-proof.jpg',quality=95,dpi=(245.364,245.364))
vis=cv2.applyColorMap(np.uint8(np.clip((d-2)/4.5,0,1)*255),cv2.COLORMAP_TURBO)[:,:,::-1];vis[sky]=[220,230,240]
overlay=rgb.copy();overlay[mask>0]=(overlay[mask>0]*.5+[120,35,20]).astype(np.uint8)
Image.fromarray(np.concatenate([rgb,vis,overlay],axis=1)).save(ROOT/'qa/depth-and-mask.png')
np.save(ROOT/'qa/front-depth.npy',d)
print(json.dumps({'vertices':len(v),'intrinsics':[f,cx,cy],'sky_fraction':float(sky.mean()),'people_fraction':float(mask.mean()),'asset_bytes':sum(x.stat().st_size for x in OUT.iterdir())}))
