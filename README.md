# Memory Box — FRIENDS

Scan the poster QR (https://superpranit.github.io/FRIENDS/m): the camera opens, point it at the poster, the hilltop comes alive in AR and the camera flies inside, then it continues through a white flash into the memory box void (https://superpranit.github.io/FRIENDS/box/).

Scan the poster with any phone camera. The page opens, the camera starts by itself, and the print turns into a misty 3D window of the hilltop. After a few seconds the camera flies inside: drag to look around, pinch to move closer, tap a friend for a burst of flowers. Add `?preview` to the link to play it on a laptop without a camera.

## Memory Box — the void (`/box/`)

Live: https://superpranit.github.io/FRIENDS/box/

Six memories (the big group in March, the June trip, mountain viewpoint, misty hilltop, party under the lights, the street at night) float as dust in a dark void. A fluorescent light is born in the middle, flies to each one in turn, and the memory assembles in 3D as the light reaches it, then settles into a glowing photo card. At the end the camera pulls back to show all of them together, and the journey loops. Drag to look around, pinch or scroll to zoom, tap a memory to send the light there. Sound starts on the first touch.

`tools/box/convert.py` turns the SHARP splat `.ply` files into the light point clouds in `box/` (about 160k points each).

## Memory Box Studio — make your own boxes (`/create/`)

Live: https://superpranit.github.io/FRIENDS/create/

A web app that builds a complete memory box like this one for anyone, entirely in the browser (nothing is uploaded):

1. Name the box.
2. Drop 1–12 Apple SHARP splat `.ply` files (one per photo). Reorder or rename them; the box previews live.
3. Pick the memory that goes on the print and add its original photo.
4. Choose the address: a GitHub username plus a box name (`https://USER.github.io/BOX/`), or any https address.
5. Build. The studio converts the splats (a JavaScript port of `tools/box/convert.py`), hides the QR in the photo at the faintest strength a QR decoder reads every time in simulated phone shots (or puts it on a small white card when the photo is too busy), teaches the camera the print (MindAR compile), and packs everything.

Then download the `.zip` (upload it to any https host) or press **Publish** with a GitHub token (`public_repo` scope) to create the repository, upload the files and switch on GitHub Pages in one go. The print comes as a PDF at the chosen width and as a JPG.

Each generated box has the same flow as FRIENDS: scan the QR, point the camera at the print, the photo turns into its point cloud and the void opens inside that memory; double tap for the next one.

Files: `create/index.html` (the studio), `create/convert-worker.js` (splat converter), `create/player/box.html` (the void, reads everything from `box.json`) and `create/player/ar.html` (the scan page).

## Print
- `artwork/friends-memory-poster-30x40cm.pdf` — final poster, 30 × 40 cm, no text, QR woven into the sky (top right).
- `artwork/friends-memory-poster.jpg` — same, 2898 × 3864 px.
- `artwork/memory-box-poster-proof.*` — the earlier proof without the QR (it does **not** open the site).

Print the final poster as is (no cropping or colour changes) — the camera tracks this exact image.

## Files
- `memory/` — the experience (index.html, depth layers, photo textures, tracking target `targets.mind`).
- `m/` — short-link redirect for the QR. `index.html` at the root redirects to `memory/`.
- `tools/` — asset build, QR embedding (`make_qr_poster.py` + `qrembed.py`) and target compile helpers.

The site is published from the `gh-pages` branch (only `index.html`, `memory/`, `m/`, `box/`, `create/`, `.nojekyll`).

The photo is public on this site. To take it down, delete the `gh-pages` branch or make the repo private.
