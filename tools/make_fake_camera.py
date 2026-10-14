"""Generate a looping camera fixture for tools/ar-check.cjs."""
from pathlib import Path
import cv2,numpy as np
from PIL import Image
root=Path(__file__).resolve().parents[1];(root/'qa').mkdir(exist_ok=True)
photo=Image.open(root/'memory/memory-target.jpg').resize((462,616))
frame=Image.new('RGB',(960,720),(125,128,121));frame.paste(photo,(249,52))
yuv=cv2.cvtColor(np.array(frame),cv2.COLOR_RGB2YUV_I420)
with open(root/'qa/fake.y4m','wb') as out:
 out.write(b'YUV4MPEG2 W960 H720 F15:1 Ip A1:1 C420jpeg\n')
 for _ in range(2):out.write(b'FRAME\n');out.write(yuv.tobytes())
print('Wrote qa/fake.y4m')
