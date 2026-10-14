import sys; sys.path.insert(0,__import__('os').path.dirname(__file__))
import numpy as np, cv2, qrcode, zxingcpp
from qrembed import qr_matrix, embed, simulate, decodes
URL='https://superpranit.github.io/FRIENDS/m'
img=cv2.imread(sys.argv[1])[:,:,::-1].astype(np.float32)/255
M,ver=qr_matrix(URL, qrcode.constants.ERROR_CORRECT_Q, 4); print('version',ver,M.shape)
x0,y0,size=1985,502,492
def whole(im,rng):
    H,W=im.shape[:2]; FW,FH=1080,1920; s=rng.uniform(.8,.95)*FW/W
    src=np.float32([[0,0],[W,0],[W,H],[0,H]]); j=lambda: rng.uniform(-.04,.04)*FW
    dst=np.float32([[(x-W/2)*s+FW/2+j(),(y-H/2)*s+FH/2+j()] for x,y in src])
    f=cv2.warpPerspective(im,cv2.getPerspectiveTransform(src,dst),(FW,FH),borderValue=(.4,.4,.4))
    f=cv2.GaussianBlur(f,(0,0),rng.uniform(.6,1.3)); m=f[FH//4:3*FH//4,FW//4:3*FW//4].mean()
    f=np.clip(f*(rng.uniform(.4,.5)/m)+rng.normal(0,rng.uniform(.01,.02),f.shape),0,1)
    ok,e=cv2.imencode('.jpg',(f*255).astype(np.uint8),[cv2.IMWRITE_JPEG_QUALITY,int(rng.uniform(70,90))]); return cv2.imdecode(e,0)
for dark in [.3,.34,.38]:
    out=embed(img,M,ver,x0,y0,size,dark=dark,light=0,dot=.46)
    rng=np.random.default_rng(7)
    c=sum(decodes(simulate(out,rng,(x0,y0,size)),URL)[0] for _ in range(30))
    w=sum(decodes(whole(out,rng),URL)[0] for _ in range(20))
    print('dark',dark,'close',c,'/30 whole',w,'/20',flush=True)
    if c>=29 and w>=19: break
cv2.imwrite('poster.png',(out[:,:,::-1]*255).round().astype(np.uint8)); print('saved dark',dark)
