/* Memory Box Studio: turns an Apple SHARP splat (.ply) into a memory-box point cloud.
   A JavaScript port of tools/box/convert.py, plus a photo-like render of the splat.
   in:  { buf: ArrayBuffer, n: target point count, seed }
   out: { meta, bin: ArrayBuffer (12 bytes/point), photo: { w, h, rgba: ArrayBuffer } } */

function mulberry32(a){ return function(){ a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function normalRng(rnd){ return () => { let u = 0, v = 0; while (u === 0) u = rnd(); v = rnd(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }; }

// separable gaussian blur with mirrored edges (like scipy/cv2 reflect)
function gauss(src, w, h, sigma){
  const r = Math.ceil(sigma * 3), k = new Float32Array(2 * r + 1); let s = 0;
  for (let i = -r; i <= r; i++){ k[i + r] = Math.exp(-i * i / (2 * sigma * sigma)); s += k[i + r]; }
  for (let i = 0; i < k.length; i++) k[i] /= s;
  const refl = (i, n) => { while (i < 0 || i >= n){ if (i < 0) i = -i - 1; if (i >= n) i = 2 * n - i - 1; } return i; };
  const tmp = new Float32Array(w * h), out = new Float32Array(w * h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++){ let a = 0; for (let j = -r; j <= r; j++) a += src[y * w + refl(x + j, w)] * k[j + r]; tmp[y * w + x] = a; }
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++){ let a = 0; for (let j = -r; j <= r; j++) a += tmp[refl(y + j, h) * w + x] * k[j + r]; out[y * w + x] = a; }
  return out;
}

function parsePly(buf){
  const u8 = new Uint8Array(buf);
  const head = new TextDecoder('latin1').decode(u8.subarray(0, Math.min(u8.length, 1 << 16)));
  const k = head.indexOf('end_header');
  if (!head.startsWith('ply') || k < 0) throw new Error('This is not a .ply file.');
  const hlen = head.indexOf('\n', k) + 1;
  const h = head.slice(0, hlen);
  if (!/format\s+binary_little_endian/.test(h)) throw new Error('Only binary .ply files are supported (Apple SHARP writes these).');
  const SZ = { char: 1, uchar: 1, int8: 1, uint8: 1, short: 2, ushort: 2, int16: 2, uint16: 2, int: 4, uint: 4, int32: 4, uint32: 4, float: 4, float32: 4, double: 8, float64: 8 };
  let count = 0, inV = false, stride = 0; const props = {};
  for (const line of h.split('\n')){
    const t = line.trim().split(/\s+/);
    if (t[0] === 'element'){ inV = t[1] === 'vertex'; if (inV) count = +t[2]; }
    else if (t[0] === 'property' && inV){
      if (t[1] === 'list') throw new Error('Unexpected list property in vertex data.');
      props[t[2]] = { off: stride, type: t[1] }; stride += SZ[t[1]] || 4;
    }
  }
  for (const p of ['x', 'y', 'z', 'f_dc_0', 'f_dc_1', 'f_dc_2', 'opacity', 'scale_0', 'scale_1'])
    if (!props[p]) throw new Error('This .ply has no "' + p + '" values, so it is not a Gaussian splat.');
  const intr = h.match(/sharp_intrinsic\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)/);
  const size = h.match(/sharp_image_size\s+(\d+)\s+(\d+)/);
  if (!intr || !size) throw new Error('This splat has no camera information. Use the .ply that Apple SHARP made from a photo.');
  const dv = new DataView(buf, hlen);
  if (dv.byteLength < count * stride) throw new Error('The file is cut short. Try exporting it again.');
  const get = (name) => {
    const { off, type } = props[name], a = new Float32Array(count);
    if (type === 'float' || type === 'float32') for (let i = 0; i < count; i++) a[i] = dv.getFloat32(i * stride + off, true);
    else if (type === 'double' || type === 'float64') for (let i = 0; i < count; i++) a[i] = dv.getFloat64(i * stride + off, true);
    else throw new Error('Unsupported value type for ' + name + '.');
    return a;
  };
  return { n: count, x: get('x'), y: get('y'), z: get('z'), c0: get('f_dc_0'), c1: get('f_dc_1'), c2: get('f_dc_2'), op: get('opacity'), s0: get('scale_0'), s1: get('scale_1'),
    f: +intr[1], cx: +intr[3], cy: +intr[4], W: +size[1], H: +size[2] };
}

function convert(buf, N, seed){
  const s = parsePly(buf);
  const { n, x, y, z, f, cx, cy, W, H } = s;
  const rnd = mulberry32(seed || 3), nrm = normalRng(rnd);
  const col = new Float32Array(n * 3), op = new Float32Array(n), u = new Float32Array(n), v = new Float32Array(n);
  const cl = (a) => a < 0 ? 0 : a > 1 ? 1 : a;
  for (let i = 0; i < n; i++){
    col[i * 3] = cl(.5 + .28209479 * s.c0[i]); col[i * 3 + 1] = cl(.5 + .28209479 * s.c1[i]); col[i * 3 + 2] = cl(.5 + .28209479 * s.c2[i]);
    op[i] = 1 / (1 + Math.exp(-s.op[i]));
    u[i] = (x[i] / z[i] * f + cx) / W; v[i] = (y[i] / z[i] * f + cy) / H;
  }
  // how far away the subject is (scenes from selfies to landscapes): the sky fade starts beyond it
  const zs = []; for (let i = 0; i < n; i += 7) if (z[i] > 0 && Math.abs(u[i] - .5) < .22 && Math.abs(v[i] - .55) < .25 && op[i] > .3) zs.push(z[i]);
  zs.sort((a, b) => a - b);
  const zc = zs.length ? zs[Math.floor(zs.length * .4)] : 3;
  const z0 = Math.max(4.4, zc * 1.3), zr = Math.max(1.9, zc * .58), zh = Math.max(6.25, zc * 1.9);
  // a smooth noise field for ragged, organic edges
  let noise = new Float32Array(64 * 64); for (let i = 0; i < noise.length; i++) noise[i] = nrm();
  noise = gauss(noise, 64, 64, 4);
  let m = 0, q = 0; for (const a of noise){ m += a; q += a * a; } m /= noise.length; const sd = Math.sqrt(q / noise.length - m * m) || 1;
  for (let i = 0; i < noise.length; i++) noise[i] /= sd;
  const samp = (yy, xx) => { const x0 = Math.min(62, Math.floor(xx)), y0 = Math.min(62, Math.floor(yy)), fx = xx - x0, fy = yy - y0;
    return noise[y0 * 64 + x0] * (1 - fx) * (1 - fy) + noise[y0 * 64 + x0 + 1] * fx * (1 - fy) + noise[(y0 + 1) * 64 + x0] * (1 - fx) * fy + noise[(y0 + 1) * 64 + x0 + 1] * fx * fy; };
  const w = new Float32Array(n), keep = new Uint8Array(n);
  for (let i = 0; i < n; i++){
    const ok = z[i] > 0 && u[i] > -.02 && u[i] < 1.02 && v[i] > -.02 && v[i] < 1.02 && op[i] > .05;
    if (!ok) continue;
    const du = (u[i] - .5) * 2, dvv = (v[i] - .5) * 2, r = Math.sqrt(du * du + dvv * dvv * .92);
    const nz = samp(cl(v[i]) * 63, cl(u[i]) * 63);
    let e = cl((1.18 - (r + .16 * nz)) / .5); e = e * e * (3 - 2 * e);
    const bd = Math.min(Math.min(u[i], 1 - u[i]), Math.min(v[i], 1 - v[i])) + .03 * nz;
    e *= Math.pow(cl(bd / .13), 1.5);
    const far = cl((z[i] - z0) / zr), depthw = (1 - .9 * far) * (z[i] > zh ? .45 : 1);
    w[i] = e * depthw * cl(op[i]);
    if (w[i] > .02) keep[i] = 1;
  }
  // keep each point with a probability that follows its weight, about N in all
  const p = new Float32Array(n);
  let sum = 0; for (let i = 0; i < n; i++) if (keep[i]){ p[i] = Math.pow(w[i], .6); sum += p[i]; }
  if (sum === 0) throw new Error('Nothing usable was found in this splat.');
  for (let it = 0; it < 5; it++){ const k = N / sum; sum = 0; for (let i = 0; i < n; i++) if (keep[i]){ p[i] = Math.min(1, p[i] * k); sum += p[i]; } }
  let sel = []; for (let i = 0; i < n; i++) if (keep[i] && rnd() < p[i]) sel.push(i);
  for (let i = sel.length - 1; i > 0; i--){ const j = Math.floor(rnd() * (i + 1)); const t = sel[i]; sel[i] = sel[j]; sel[j] = t; }
  const K = sel.length;
  const P = new Float32Array(K * 3), size = new Float32Array(K);
  const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  let lsMin = Infinity, lsMax = -Infinity;
  for (let k = 0; k < K; k++){
    const i = sel[k];
    P[k * 3] = x[i]; P[k * 3 + 1] = -y[i]; P[k * 3 + 2] = -z[i];               // three.js: camera at the origin looking down -z
    for (let a = 0; a < 3; a++){ lo[a] = Math.min(lo[a], P[k * 3 + a]); hi[a] = Math.max(hi[a], P[k * 3 + a]); }
    // a point big enough to fill the gap left by the sub-sampling
    let sz = 1.75 * z[i] / f / Math.sqrt(Math.max(.02, Math.min(1, p[i])));
    sz = Math.max(sz, 2.2 * Math.sqrt(Math.exp(s.s0[i]) * Math.exp(s.s1[i])));
    size[k] = Math.log(sz); lsMin = Math.min(lsMin, size[k]); lsMax = Math.max(lsMax, size[k]);
  }
  for (let a = 0; a < 3; a++) if (hi[a] - lo[a] < 1e-6) hi[a] = lo[a] + 1e-6;
  if (lsMax - lsMin < 1e-6) lsMax = lsMin + 1e-6;
  const bin = new ArrayBuffer(K * 12), q16 = new Uint16Array(bin), q8 = new Uint8Array(bin);
  for (let k = 0; k < K; k++){
    const i = sel[k];
    for (let a = 0; a < 3; a++) q16[k * 6 + a] = Math.round((P[k * 3 + a] - lo[a]) / (hi[a] - lo[a]) * 65535);
    q8[k * 12 + 6] = Math.round(col[i * 3] * 255); q8[k * 12 + 7] = Math.round(col[i * 3 + 1] * 255); q8[k * 12 + 8] = Math.round(col[i * 3 + 2] * 255);
    q8[k * 12 + 9] = Math.round((size[k] - lsMin) / (lsMax - lsMin) * 255);
    q8[k * 12 + 10] = Math.round(w[i] * 255);
  }
  // the focus: the people, the central near points
  const cen = []; for (let k = 0; k < K; k++){ const i = sel[k]; if (Math.abs(u[i] - .5) < .22 && Math.abs(v[i] - .55) < .25) cen.push(k); }
  let F = [0, 0, 0], cnt = 0;
  if (cen.length > 20){
    const zz = cen.map((k) => z[sel[k]]).sort((a, b) => a - b), pct = zz[Math.floor((zz.length - 1) * .4)];
    for (const k of cen) if (z[sel[k]] < pct){ F[0] += P[k * 3]; F[1] += P[k * 3 + 1]; F[2] += P[k * 3 + 2]; cnt++; }
  }
  if (!cnt) for (let k = 0; k < K; k++){ F[0] += P[k * 3]; F[1] += P[k * 3 + 1]; F[2] += P[k * 3 + 2]; cnt++; }
  F = F.map((a) => +(a / cnt).toFixed(4));
  const meta = { n: K, lo: lo.map((a) => +a.toFixed(5)), hi: hi.map((a) => +a.toFixed(5)), smin: lsMin, smax: lsMax, focus: F, f, W, H, cx, cy };
  return { meta, bin, photo: render(s, col, op) };
}

/* a photo-like picture of the splat, from the camera that took the photo (for thumbnails, and the print if no photo is given) */
function render(s, col, op){
  const { n, x, y, z, f, cx, cy, W, H } = s;
  const img = new Float32Array(W * H * 3);
  const idx = new Uint32Array(n); for (let i = 0; i < n; i++) idx[i] = i;
  const zz = s.z; idx.sort((a, b) => zz[b] - zz[a]);                          // far first
  for (let t = 0; t < n; t++){
    const i = idx[t]; if (z[i] <= 0 || op[i] < .02) continue;
    const px = x[i] / z[i] * f + cx, py = y[i] / z[i] * f + cy;
    let sg = Math.sqrt(Math.exp(s.s0[i]) * Math.exp(s.s1[i])) * f / z[i];
    sg = Math.max(.8, Math.min(sg, 3.2));
    const r = Math.ceil(sg * 2.2);
    if (px < -r || py < -r || px > W + r || py > H + r) continue;
    const x0 = Math.max(0, Math.floor(px - r)), x1 = Math.min(W - 1, Math.ceil(px + r)), y0 = Math.max(0, Math.floor(py - r)), y1 = Math.min(H - 1, Math.ceil(py + r));
    const a0 = op[i], k2 = 1 / (2 * sg * sg), cr = col[i * 3], cg = col[i * 3 + 1], cb = col[i * 3 + 2];
    for (let yy = y0; yy <= y1; yy++) for (let xx = x0; xx <= x1; xx++){
      const dx = xx + .5 - px, dy = yy + .5 - py, a = a0 * Math.exp(-(dx * dx + dy * dy) * k2);
      if (a < .004) continue;
      const o = (yy * W + xx) * 3;
      img[o] += (cr - img[o]) * a; img[o + 1] += (cg - img[o + 1]) * a; img[o + 2] += (cb - img[o + 2]) * a;
    }
  }
  const rgba = new Uint8ClampedArray(W * H * 4);
  for (let i = 0; i < W * H; i++){ rgba[i * 4] = img[i * 3] * 255; rgba[i * 4 + 1] = img[i * 3 + 1] * 255; rgba[i * 4 + 2] = img[i * 3 + 2] * 255; rgba[i * 4 + 3] = 255; }
  return { w: W, h: H, rgba: rgba.buffer };
}

self.onmessage = (e) => {
  const { id, buf, n, seed } = e.data;
  try {
    const out = convert(buf, n || 160000, seed || 3);
    self.postMessage({ id, ok: true, ...out }, [out.bin, out.photo.rgba]);
  } catch (err) {
    self.postMessage({ id, ok: false, error: (err && err.message) || String(err) });
  }
};
