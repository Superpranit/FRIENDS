# Memory Box

A private, unpublished GitHub Pages package made from the supplied hillside photograph and its calibrated Apple SHARP Gaussian splat. The site renders a layered depth photograph, not the 33 MB splat. The friends' faces have not been regenerated.

## Open the experience locally

Extract this package, open a terminal in its folder, then run:

```sh
python3 -m http.server 8765
```

Open `http://localhost:8765/memory/?preview` for the complete camera-free experience. Open `/memory/` for the desktop introduction. Internet access is needed for the pinned Three.js and MindAR modules on jsDelivr. Opening the HTML directly with `file://` will not load the binary depth files.

On a published HTTPS page, touch devices request camera access automatically. `#ar` also requests AR on a desktop. A browser's camera permission dialog cannot be bypassed. If access is denied, the page offers a camera-free preview. Audio begins only after a gesture. The AR and cinematic interfaces use icons; the desktop introduction and exceptional error messages use plain text.

## Included

- `memory/index.html`: complete HTML, styles and application module.
- `memory/memory.json`: calibrated camera, quantization and poster status.
- `memory/depth.bin`: little-endian uint16 front 384 x 512 and background 192 x 256 grids.
- `memory/mask.bin`: 384 x 512 person mask.
- `memory/fg.jpg`, `bg.jpg`: graded photo and filled background.
- `memory/memory-target.jpg`, `targets.mind`: matched poster proof and compiled tracking data.
- `m/index.html`: short-route redirect, preserving query and hash.
- `artwork/memory-box-poster-proof.pdf` and `.jpg`: text-free artwork, **without a QR code**. The PDF is exactly 30 x 40 cm. The JPG is 2898 x 3864 pixels, approximately 245 dpi at that size; upsampling cannot add source detail.
- `tools/`: repeatable conversion, QR generation, compilation and checks.
- `qa/`: machine-readable test results only. Browser screenshots are intentionally omitted.
- `.github/workflows/pages.yml`: manual deployment for a new dedicated repository. Nothing deploys on push.

The photo, depth and tracking assets plus HTML total approximately **2.2 MB**, before shared external JavaScript dependencies. A complete uncached AR load exceeds the 2-3 MB photo-asset budget because MindAR and Three.js are additional downloads. 60 fps is a target, not a measured phone result.

## What is ready

Calibrated depth reveal, constrained poster window, mist, particles, petals, drifting light, second-renderer fly-in, letterboxing, subtle bloom/grade, touch drag, pinch/wheel dolly, reduced-motion timing, sound toggle, close/replay, and person-only tap blooms are implemented. Background depth is kept behind foreground silhouettes. The AR reveal uses a shallow, view-calibrated depth window; it expands to the full calibrated depth during entry, avoiding a floating, misaligned rectangle when the phone is closer than the reconstruction camera.

The artwork remains a **proof** until a real public destination is supplied. Do not print it expecting a camera scan to open a website yet.

## Finish the QR poster

First confirm that the people in the photo may be published, and choose the real GitHub owner/repository. Then:

```sh
python3 -m pip install -r tools/requirements.txt
npm ci --ignore-scripts
python3 tools/finalize_poster.py https://YOUR-OWNER.github.io/YOUR-REPOSITORY/m/
```

Use your real URL, not the example. This generates final PDF/JPG artwork and replaces the tracking image. The generator starts at QR version 4, Q correction; it increases the version if the actual URL needs more capacity. It uses four quiet-zone modules for reliability, soft data dots and solid functional patterns. It tests 30 close-up and 20 whole-poster simulated views with both ZXing and OpenCV. It only writes final artwork after both decoders reach 95% in both groups. If it fails, enlarge the QR and rerun. Simulation is not a guarantee for a physical print.

After changing the poster, **recompile the target**. With the local server running, open `http://localhost:8765/tools/compile-target.html`, compile, and save the downloaded `targets.mind` over `memory/targets.mind`. This runs locally in your browser; it does not upload the photo. Mark `posterStatus` as `final-qr-compiled` in `memory/memory.json` after replacing it. The existing target is for the QR-free proof.

## Publish when approved

For a **new dedicated repository**, upload this package, excluding `node_modules` and private scratch outputs. In Settings > Pages, choose GitHub Actions. Run the manual **Publish Memory Box** workflow. It publishes only `memory/`, `m/` and `.nojekyll`. The page will be at `https://OWNER.github.io/REPOSITORY/memory/`.

For an **existing repository**, copy only `memory/`, `m/` and `.nojekyll` into it. Integrate these directories into its existing deployment. **Do not replace its root page or deployment workflow with the dedicated-repository workflow**, which only stages this experience.

GitHub Pages normally makes the photograph and its assets publicly accessible. This package has not been pushed to GitHub or published. There is no live URL yet.

## Validation and practical limits

The supplied calibration was read from the PLY metadata: focal length 3494.611236, centre 575.5 / 767.5, source camera 1152 x 1536. All 589,824 splats were projected, and the derived depth and silhouette overlays were visually inspected. The proof PDF was rendered and reviewed.

Read `qa/browser-report.json` and `qa/ar-report.json` for actual browser results. Chromium software rendering is a functional smoke test, not a performance benchmark. Mobile viewport checks are not real-device certification. Before printing a batch, test the final QR and final target on a physical proof with iPhone Safari and Android Chrome, including camera denial, tracking loss, low light, and sound.

Single-image reconstruction cannot reveal unseen geometry. The filled hillside is an approximation and wider camera movement may expose reconstruction artifacts; controls deliberately limit movement. The upper half is low-detail sky, so keep the lower half of the print visible during acquisition.

## Rebuild and developer checks

```sh
python3 tools/build_assets.py /path/to/photo.jpeg /path/to/reconstruction.ply
python3 tools/check-assets.py
npm ci --ignore-scripts
npx playwright install chromium
npm run qa
```

Rebuilding assets resets the poster to its QR-free proof; finalize and compile again afterward. `CHROME_PATH` can select an installed Chromium executable. The browser check maps CDN imports to local npm packages for offline dependency testing; the production HTML retains the requested jsDelivr import map. For the fake-camera test, run `python3 tools/make_fake_camera.py` then `node tools/ar-check.cjs`. Its generated fixture and binary browser files are not included in the package.

Upstream documentation: https://hiukim.github.io/mind-ar-js-doc/installation/ and https://hiukim.github.io/mind-ar-js-doc/quick-start/compile/ . Dependencies remain under their respective upstream licenses. The user's photograph and reconstruction remain their own materials.
