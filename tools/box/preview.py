import sys,numpy as np,cv2; sys.path.insert(0,'src'); from readply import read
for i,p in enumerate(sys.argv[1:]):
    s=read(p); x,y,z=s['xyz'].T; k=.25
    u=((x/z*s['f']+s['cx'])*k).astype(int); v=((y/z*s['f']+s['cy'])*k).astype(int)
    W,H=int(s['W']*k),int(s['H']*k); img=np.zeros((H,W,3)); zb=np.full((H,W),1e9)
    m=(u>=0)&(u<W)&(v>=0)&(v<H)&(s['op']>.2)
    o=np.argsort(-z[m]); uu,vv,zz,cc=u[m][o],v[m][o],z[m][o],s['col'][m][o]
    img[vv,uu]=cc; zb[vv,uu]=zz
    print(p.split('/')[-1], 'n',len(z),'z pct',np.percentile(z,[1,25,50,75,95,99]).round(2),'op>.2',m.mean().round(2),'scale med',np.median(s['sc'],0).round(4))
    cv2.imwrite(f'prev{i}.png',(img[:,:,::-1]*255).astype(np.uint8))
