import sys, json, numpy as np, cv2
sys.path.insert(0,'src'); from readply import read
U='/mnt/user-data/uploads/'
MEMS=[('mountain',U+'WhatsApp_Image_2026-10-15_at_6_47_41_PM_3d.ply'),
      ('hilltop', U+'WhatsApp_Image_2026-10-14_at_11_23_16_AM_3d.ply'),
      ('party',   U+'WhatsApp_Image_2026-10-15_at_6_50_41_PM_3d.ply'),
      ('street',  U+'WhatsApp_Image_2026-10-15_at_6_53_18_PM_3d.ply')]
N=int(sys.argv[1]) if len(sys.argv)>1 else 160000
rng=np.random.default_rng(3)
# smooth noise field for ragged, organic edges
noise=cv2.GaussianBlur(rng.normal(0,1,(64,64)).astype(np.float32),(0,0),4); noise/=noise.std()
out=[]
for i,(name,path) in enumerate(MEMS):
    s=read(path); x,y,z=s['xyz'].T
    u=(x/z*s['f']+s['cx'])/s['W']; v=(y/z*s['f']+s['cy'])/s['H']
    ok=(u>-.02)&(u<1.02)&(v>-.02)&(v<1.02)&(s['op']>.05)
    # elliptical edge mask in image space + noise -> soft island
    asp=s['W']/s['H']; du=(u-.5)*2; dv=(v-.5)*2
    r=np.sqrt((du)**2+(dv)**2*0.92)
    from scipy.ndimage import map_coordinates
    nz=map_coordinates(noise,[np.clip(v,0,1)*63,np.clip(u,0,1)*63],order=1)
    rr=r+.16*nz
    edge=np.clip((1.18-rr)/.5,0,1); edge=edge*edge*(3-2*edge)
    bd=np.minimum(np.minimum(u,1-u),np.minimum(v,1-v))+.03*nz
    edge*=np.clip(bd/.13,0,1)**1.5
    # far background / sky fades to haze
    far=np.clip((z-4.4)/1.9,0,1); depthw=(1-.9*far)*np.where(z>6.25,.45,1)
    w=edge*depthw*np.clip(s['op'],0,1)
    keep=ok&(w>.02)
    # keep probability proportional to weight, normalised to N points
    p=np.zeros_like(w); p[keep]=w[keep]**.6
    p*=N/p.sum(); p=np.clip(p,0,1)
    for _ in range(4): p*=N/p.sum(); p=np.clip(p,0,1)
    sel=np.where(keep&(rng.random(len(p))<p))[0]; rng.shuffle(sel)
    P=np.stack([x,-y,-z],1)[sel]          # three.js: camera at origin looking -z
    col=s['col'][sel]; ws=w[sel]
    # world size of a point that fills the gap left by sub-sampling
    size=1.75*z[sel]/s['f']/np.sqrt(np.clip(p[sel],.02,1))
    size=np.maximum(size, 2.2*np.sqrt(s['sc'][sel,0]*s['sc'][sel,1]))
    lo=P.min(0); hi=P.max(0)
    q=np.round((P-lo)/(hi-lo)*65535).astype(np.uint16)
    ls=np.log(size); smin,smax=float(ls.min()),float(ls.max())
    sq=np.round((ls-smin)/(smax-smin)*255).astype(np.uint8)
    rec=np.zeros(len(sel),dtype=[('p','<u2',3),('c','u1',3),('s','u1'),('w','u1'),('pad','u1')])
    rec['p']=q; rec['c']=np.round(col*255); rec['s']=sq; rec['w']=np.round(ws*255)
    rec.tofile(f'box/{name}.bin')
    # focus: the people — central, near points
    cen=(abs(u[sel]-.5)<.22)&(abs(v[sel]-.55)<.25)
    zc=z[sel][cen]; near=cen.copy(); near[cen]=zc<np.percentile(zc,40)
    F=P[near].mean(0)
    out.append(dict(name=name,file=f'{name}.bin',n=int(len(sel)),lo=lo.round(5).tolist(),hi=hi.round(5).tolist(),smin=smin,smax=smax,
        focus=F.round(4).tolist(),f=s['f'],W=s['W'],H=s['H'],cx=s['cx'],cy=s['cy']))
    print(name,len(sel),'focus',F.round(2),'bytes',len(sel)*12, 'size px@orig', np.median(size*s['f']/z[sel]).round(2))
json.dump(dict(memories=out),open('box/box.json','w'),indent=1)
