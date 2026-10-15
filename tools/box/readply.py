import numpy as np, re
def read(path):
    with open(path,'rb') as f:
        hdr=b''
        while not hdr.endswith(b'end_header\n'): hdr+=f.readline()
        h=hdr.decode(); n=int(re.search(r'element vertex (\d+)',h).group(1))
        props=re.findall(r'property float (\w+)',h)
        a=np.frombuffer(f.read(n*4*len(props)),np.float32).reshape(n,len(props))
    intr=[float(x) for x in re.search(r'sharp_intrinsic ([\d. ]+)',h).group(1).split()]
    size=[int(x) for x in re.search(r'sharp_image_size (\d+) (\d+)',h).group(1,2)]
    d={p:a[:,i] for i,p in enumerate(props)}
    xyz=np.stack([d['x'],d['y'],d['z']],1)
    col=np.clip(.5+.28209479*np.stack([d['f_dc_0'],d['f_dc_1'],d['f_dc_2']],1),0,1)
    op=1/(1+np.exp(-d['opacity']))
    sc=np.exp(np.stack([d['scale_0'],d['scale_1'],d['scale_2']],1))
    rot=np.stack([d['rot_0'],d['rot_1'],d['rot_2'],d['rot_3']],1)
    return dict(xyz=xyz,col=col,op=op,sc=sc,rot=rot,f=intr[0],cx=intr[2],cy=intr[3],W=size[0],H=size[1])
