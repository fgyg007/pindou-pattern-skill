#!/usr/bin/env python3
"""Convert an arbitrary IMAGE into a clean bead grid.

This is the hard, judgement-driven path. The defaults auto-detect the subject,
but YOU (Claude) should look at the image first and pass parameters, then VIEW
the preview and re-run with adjustments until it looks right. See SKILL.md.

Pipeline: subject-crop (largest dark components) -> outline-preserving downsample
-> outline strengthen + gap-bridge -> background flood -> despeckle.

Usage:
  python image_to_pattern.py IN.png --out grid.json --preview prev.png \
      [--cells 52] [--crop x0 y0 x1 y1] [--outline 0.30] [--no-strengthen] \
      [--bg cream|transparent|keep] [--despeckle 2]
"""
import argparse, json, sys
from collections import deque, Counter
from PIL import Image, ImageFilter
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from pindou_lib import nearest_palette, lum, render_preview, hex2rgb, NAME_BY_HEX

BG_CREAM = "#F4ECD6"
BLACK = "#111111"
# colours treated as "background-ish" when flooding the exterior away
TRAVERSE = {"#F4ECD6", "#6FCF45", "#2DA44E", "#16633A", "#FBE6A2",
            "#CBCBCB", "#FFD9B3", "#57D9C0", "#8A8A8A", "#FFFFFF"}


def auto_crop(im):
    """Square crop framing the subject via the union of sizable dark blocks."""
    W, H = im.size
    px = im.load()
    s = max(1, max(W, H) // 230)
    sw, sh = W // s, H // s
    dark = [[max(px[x * s, y * s]) < 95 for x in range(sw)] for y in range(sh)]
    seen = [[False] * sw for _ in range(sh)]
    comps = []
    for y in range(sh):
        for x in range(sw):
            if dark[y][x] and not seen[y][x]:
                q = deque([(y, x)]); seen[y][x] = True; comp = []
                while q:
                    cy, cx = q.popleft(); comp.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < sh and 0 <= nx < sw and dark[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True; q.append((ny, nx))
                comps.append(comp)
    big = [p for comp in comps if len(comp) >= 40 for p in comp]
    if not big:
        return (0, 0, W, H)
    ys = [p[0] for p in big]; xs = [p[1] for p in big]
    minx, maxx, miny, maxy = min(xs) * s, max(xs) * s, min(ys) * s, max(ys) * s
    padx = int((maxx - minx) * 0.06) + 5; pady = int((maxy - miny) * 0.06) + 5
    minx = max(0, minx - padx); maxx = min(W, maxx + padx)
    miny = max(0, miny - pady); maxy = min(H, maxy + pady)
    side = max(maxx - minx, maxy - miny)
    cx, cy = (minx + maxx) // 2, (miny + maxy) // 2
    l = max(0, cx - side // 2); t = max(0, cy - side // 2)
    r = min(W, l + side); b = min(H, t + side)
    l = max(0, r - side); t = max(0, b - side)
    return (l, t, r, b)


def convert(path, cells=52, crop=None, outline=0.30, strengthen=True,
            bg="cream", despeckle=2):
    im = Image.open(path).convert("RGB")
    box = tuple(crop) if crop else auto_crop(im)
    bs = 10
    cl = im.crop(box).resize((cells * bs, cells * bs), Image.BILINEAR)
    cp = cl.load()

    avg = [[None] * cells for _ in range(cells)]
    dfrac = [[0.0] * cells for _ in range(cells)]
    for r in range(cells):
        for c in range(cells):
            ar = ag = ab = nd = 0
            for yy in range(bs):
                for xx in range(bs):
                    R, G, B = cp[c * bs + xx, r * bs + yy]
                    ar += R; ag += G; ab += B
                    if lum(R, G, B) < 75:
                        nd += 1
            t = bs * bs
            avg[r][c] = (ar // t, ag // t, ab // t)
            dfrac[r][c] = nd / t

    blk = [[dfrac[r][c] >= outline for c in range(cells)] for r in range(cells)]
    if strengthen:
        for _ in range(2):
            add = []
            for r in range(cells):
                for c in range(cells):
                    if blk[r][c] or dfrac[r][c] < 0.12:
                        continue
                    lf = c > 0 and blk[r][c - 1]; rg = c < cells - 1 and blk[r][c + 1]
                    up = r > 0 and blk[r - 1][c]; dn = r < cells - 1 and blk[r + 1][c]
                    if (lf and rg) or (up and dn):
                        add.append((r, c))
            for r, c in add:
                blk[r][c] = True
        for r in range(cells):
            for c in range(cells):
                if blk[r][c]:
                    nb = any(0 <= r + dr < cells and 0 <= c + dc < cells and blk[r + dr][c + dc]
                             for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                            (1, 1), (1, -1), (-1, 1), (-1, -1)))
                    if not nb and dfrac[r][c] < 0.5:
                        blk[r][c] = False

    grid = [[BLACK if blk[r][c] else nearest_palette(*avg[r][c]) for c in range(cells)]
            for r in range(cells)]

    if bg in ("cream", "transparent"):
        repl = None if bg == "transparent" else BG_CREAM
        seen = [[False] * cells for _ in range(cells)]
        dq = deque()
        seeds = [(0, 0), (0, cells - 1), (cells - 1, 0), (cells - 1, cells - 1),
                 (0, cells // 2), (cells - 1, cells // 2), (cells // 2, 0), (cells // 2, cells - 1)]
        for r, c in seeds:
            if grid[r][c] in TRAVERSE and not blk[r][c]:
                dq.append((r, c)); seen[r][c] = True
        while dq:
            r, c = dq.popleft(); grid[r][c] = repl
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if (0 <= nr < cells and 0 <= nc < cells and not seen[nr][nc]
                        and not blk[nr][nc] and grid[nr][nc] in TRAVERSE):
                    seen[nr][nc] = True; dq.append((nr, nc))

    for _ in range(despeckle):
        cp2 = [row[:] for row in grid]
        for r in range(cells):
            for c in range(cells):
                if blk[r][c]:
                    continue
                nb = [grid[r + dr][c + dc] for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                      if 0 <= r + dr < cells and 0 <= c + dc < cells]
                if nb and grid[r][c] not in nb:
                    m = Counter(nb).most_common(1)[0]
                    if m[1] >= 3:
                        cp2[r][c] = m[0]
        grid = cp2
    return grid, box


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--out", default="grid.json")
    ap.add_argument("--preview", default="preview.png")
    ap.add_argument("--cells", type=int, default=52)
    ap.add_argument("--crop", type=int, nargs=4, default=None,
                    help="x0 y0 x1 y1 in source pixels (override auto-crop)")
    ap.add_argument("--outline", type=float, default=0.30,
                    help="dark fraction to call a cell black (lower=thicker outline)")
    ap.add_argument("--no-strengthen", dest="strengthen", action="store_false")
    ap.add_argument("--bg", choices=["cream", "transparent", "keep"], default="cream")
    ap.add_argument("--despeckle", type=int, default=2)
    a = ap.parse_args()
    grid, box = convert(a.image, a.cells, a.crop, a.outline, a.strengthen, a.bg, a.despeckle)
    json.dump(grid, open(a.out, "w"))
    render_preview(grid, a.preview)
    cnt = Counter(v for row in grid for v in row if v)
    print("crop box:", box)
    print("beads:", sum(cnt.values()), "/ colours:", len(cnt))
    for h, n in cnt.most_common():
        print(f"  {NAME_BY_HEX.get(h.upper(), h):>3} {h} x{n}")
    print("saved grid ->", a.out, "| preview ->", a.preview)


if __name__ == "__main__":
    main()
