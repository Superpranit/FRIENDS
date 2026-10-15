# Memory Box — FRIENDS

Live: https://superpranit.github.io/FRIENDS/box/ — the poster QR (https://superpranit.github.io/FRIENDS/m) now opens this memory void. The earlier AR hilltop page is still at https://superpranit.github.io/FRIENDS/memory/

Scan the poster with any phone camera. The page opens, the camera starts by itself, and the print turns into a misty 3D window of the hilltop. After a few seconds the camera flies inside: drag to look around, pinch to move closer, tap a friend for a burst of flowers. Add `?preview` to the link to play it on a laptop without a camera.

## Memory Box — the void (`/box/`)

Live: https://superpranit.github.io/FRIENDS/box/

Four memories (mountain viewpoint, misty hilltop, party under the lights, the street at night) float as dust in a dark void. A fluorescent light is born in the middle, flies to each one in turn, and the memory assembles in 3D as the light reaches it, then settles into a glowing photo card. At the end the camera pulls back to show all of them together, and the journey loops. Drag to look around, pinch or scroll to zoom, tap a memory to send the light there. Sound starts on the first touch.

`tools/box/convert.py` turns the SHARP splat `.ply` files into the light point clouds in `box/` (about 160k points each).

## Print
- `artwork/friends-memory-poster-30x40cm.pdf` — final poster, 30 × 40 cm, no text, QR woven into the sky (top right).
- `artwork/friends-memory-poster.jpg` — same, 2898 × 3864 px.
- `artwork/memory-box-poster-proof.*` — the earlier proof without the QR (it does **not** open the site).

Print the final poster as is (no cropping or colour changes) — the camera tracks this exact image.

## Files
- `memory/` — the experience (index.html, depth layers, photo textures, tracking target `targets.mind`).
- `m/` — short-link redirect for the QR. `index.html` at the root redirects to `memory/`.
- `tools/` — asset build, QR embedding (`make_qr_poster.py` + `qrembed.py`) and target compile helpers.

The site is published from the `gh-pages` branch (only `index.html`, `memory/`, `m/`, `.nojekyll`).

The photo is public on this site. To take it down, delete the `gh-pages` branch or make the repo private.
