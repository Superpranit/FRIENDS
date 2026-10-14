import numpy as np, qrcode, zxingcpp, cv2, io, sys
from PIL import Image, ImageFilter

def qr_matrix(url, ec, version=None):
    q = qrcode.QRCode(version=version, error_correction=ec, border=0); q.add_data(url); q.make(fit=version is None)
    M = np.array(q.get_matrix(), bool); return M, q.version

def function_mask(n, version):
    """modules that belong to finder / timing / alignment patterns: drawn solid, never as dots"""
    f = np.zeros((n, n), bool)
    for (r, c) in [(0, 0), (0, n - 7), (n - 7, 0)]:
        f[max(r-1,0):r + 8, max(c-1,0):c + 8] = True
    f[6, :] = True; f[:, 6] = True
    if version >= 2:
        a = n - 7; f[a - 2:a + 3, a - 2:a + 3] = True
    return f

def embed(img, M, version, x0, y0, size, dark=.35, light=.12, dot=.42, quiet=2, soft=.25, blend=1.0, calm=0.0, qz=1.0, maxlift=1.0):
    """Set each module's centre brightness relative to the LOCAL average brightness (so the scene's own
    texture can't be mistaken for code), keep each pixel's colour, and leave the texture between dots."""
    n = M.shape[0]; tot = n + 2 * quiet; px = size / tot
    S = int(np.ceil(size)) + 2
    region = img[y0:y0 + S, x0:x0 + S].astype(np.float32)
    lum = region @ np.array([.2126, .7152, .0722], np.float32)
    base = cv2.GaussianBlur(lum, (0, 0), size / 7)
    if calm > 0:   # soften the scene's texture under the code (feathered at the edges)
        yy0, xx0 = np.mgrid[0:S, 0:S].astype(np.float32); c = (S - 1) / 2
        feather = np.clip((S / 2 - np.maximum(np.abs(yy0 - c), np.abs(xx0 - c))) / (S * .08), 0, 1)
        sm = cv2.GaussianBlur(lum, (0, 0), size / 60)
        lum_c = lum * (1 - calm * feather) + sm * (calm * feather)
        region = region * (lum_c / np.maximum(lum, 1e-3))[..., None]; lum = lum_c
    Fm = function_mask(n, version)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    W = np.zeros((S, S), np.float32); T = np.zeros((S, S), np.float32)   # weight and target factor
    for i in range(-quiet, n + quiet):
        for j in range(-quiet, n + quiet):
            inside = 0 <= i < n and 0 <= j < n
            isdark = inside and M[i, j]
            cy = (i + quiet + .5) * px; cx = (j + quiet + .5) * px
            sl = (slice(max(int(cy - px), 0), min(int(cy + px) + 1, S)), slice(max(int(cx - px), 0), min(int(cx + px) + 1, S)))
            ys, xs = yy[sl], xx[sl]
            if inside and Fm[i, j]:
                d = np.maximum(np.abs(ys - cy), np.abs(xs - cx)) / (px * .5); w = np.clip((1.08 - d) / .16, 0, 1)
            else:
                d = np.hypot(ys - cy, xs - cx) / (px * dot); w = np.clip((1 - d) / soft, 0, 1)
            take = w > W[sl]
            W[sl] = np.where(take, w, W[sl]); T[sl] = np.where(take, (1 - dark) if isdark else (1 + (light if inside else light * qz)), T[sl])
    W *= blend
    target = base * T
    newL = lum * (1 - W) + target * W
    ratio = newL / np.maximum(lum, 1e-3)
    out = img.copy()
    out[y0:y0 + S, x0:x0 + S] = np.clip(region * ratio[..., None], 0, 1)
    # very dark pixels can't be brightened by ratio alone: add a neutral lift where needed
    lift = np.clip(newL - (region * ratio[..., None]) @ np.array([.2126, .7152, .0722], np.float32), 0, maxlift)
    out[y0:y0 + S, x0:x0 + S] = np.clip(out[y0:y0 + S, x0:x0 + S] + lift[..., None], 0, 1)
    return out

def simulate(img, rng, qr_box):
    """photograph the poster: perspective tilt, framing, blur, auto-exposure, noise, jpeg"""
    H, W = img.shape[:2]
    src = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
    FW, FH = 1080, 1920
    # phone held so the code region is reasonably large (people step close to scan)
    scale = rng.uniform(.62, .95) * FW / (qr_box[2] * 3.0)
    cx, cy = qr_box[0] + qr_box[2] / 2, qr_box[1] + qr_box[2] / 2
    jit = lambda: rng.uniform(-.06, .06) * W * scale
    dst = []
    for (x, y) in src:
        dst.append([(x - cx) * scale + FW / 2 + jit(), (y - cy) * scale + FH / 2 + jit()])
    Mtx = cv2.getPerspectiveTransform(src, np.float32(dst))
    bg = np.full((FH, FW, 3), rng.uniform(.3, .55), np.float32)
    frame = cv2.warpPerspective(img.astype(np.float32), Mtx, (FW, FH), dst=bg, borderMode=cv2.BORDER_TRANSPARENT)
    frame = cv2.GaussianBlur(frame, (0, 0), rng.uniform(.8, 1.8))
    # auto exposure on the centre of the frame + mild warm/cool lighting cast
    m = frame[FH//4:3*FH//4, FW//4:3*FW//4].mean()
    frame = frame * (rng.uniform(.4, .5) / max(m, 1e-3)) * np.array([rng.uniform(.9, 1.1), 1, rng.uniform(.9, 1.1)])
    frame = np.clip(frame + rng.normal(0, rng.uniform(.012, .025), frame.shape), 0, 1)
    ok, enc = cv2.imencode('.jpg', (frame * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, int(rng.uniform(70, 90))])
    return cv2.imdecode(enc, cv2.IMREAD_GRAYSCALE)

def decodes(gray, url):
    z = any(r.text == url for r in zxingcpp.read_barcodes(gray))
    try:
        t, _, _ = cv2.QRCodeDetector().detectAndDecode(gray); c = (t == url)
    except Exception: c = False
    return z, c
