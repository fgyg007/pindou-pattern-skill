#!/usr/bin/env python3
"""Read an EXISTING pattern SHEET (a printed/exported grid with colour codes)
into a bead grid. This is the easier path: we copy what's already there.

Robustness comes from YOU looking at the sheet first and supplying the geometry:
the grid size and the pixel rectangle covering the cell area (from the top-left
corner of cell (1,1) to the bottom-right corner of cell (N,N)). Read these off the
numbered axes. Colours are auto-clustered from the cells (no need to type them).

Key trick: sample a RING near each cell's edges, not the centre — the centre holds
the code label text, which would corrupt the colour. Background is detected as the
light colour reachable from the border and set to None (no bead).

Usage:
  python parse_sheet.py SHEET.png --rows 52 --cols 52 \
      --bounds X0 Y0 X1 Y1 --out grid.json --preview prev.png \
      [--bg-light 1] [--despeckle 3]
"""
import argparse, json, sys
from collections import deque, Counter
import numpy as np
from PIL import Image
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from pindou_lib import rgb2hex, lum, render_preview


def sample_ring(A, cx, cy, px, py, W, H):
    pts = []
    for dx, dy in [(-.30, -.30), (.30, -.30), (-.30, .30), (.30, .30),
                   (-.33, 0), (.33, 0), (0, -.33), (0, .33)]:
        x = int(round(cx + dx * px)); y = int(round(cy + dy * py))
        if 0 <= x < W and 0 <= y < H:
            pts.append(A[y, x])
    return tuple(int(v) for v in np.median(np.array(pts), axis=0))


def cluster(colors, thresh=900):
    centers = []  # (rgb, count)
    for col in colors:
        for k, (cen, n) in enumerate(centers):
            if sum((cen[i] - col[i]) ** 2 for i in range(3)) < thresh:
                centers[k] = (tuple((cen[i] * n + col[i]) // (n + 1) for i in range(3)), n + 1)
                break
        else:
            centers.append((col, 1))
    centers = [c for c in centers if c[1] >= 2]
    centers.sort(key=lambda x: -x[1])
    return [c[0] for c in centers]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("--rows", type=int, required=True)
    ap.add_argument("--cols", type=int, required=True)
    ap.add_argument("--bounds", type=float, nargs=4, required=True,
                    help="X0 Y0 X1 Y1: cell-area rectangle in source pixels")
    ap.add_argument("--out", default="grid.json")
    ap.add_argument("--preview", default="preview.png")
    ap.add_argument("--bg-light", type=int, default=1,
                    help="1: treat the light border-connected colour as empty (no bead)")
    ap.add_argument("--despeckle", type=int, default=3)
    a = ap.parse_args()

    im = Image.open(a.sheet).convert("RGB")
    A = np.asarray(im).astype(int); H, W, _ = A.shape
    x0, y0, x1, y1 = a.bounds
    px = (x1 - x0) / a.cols; py = (y1 - y0) / a.rows

    cells = [[sample_ring(A, x0 + (c + .5) * px, y0 + (r + .5) * py, px, py, W, H)
              for c in range(a.cols)] for r in range(a.rows)]

    centers = cluster([cells[r][c] for r in range(a.rows) for c in range(a.cols)])

    def classify(col):
        return min(range(len(centers)),
                   key=lambda k: sum((col[i] - centers[k][i]) ** 2 for i in range(3)))
    idx = [[classify(cells[r][c]) for c in range(a.cols)] for r in range(a.rows)]
    hexc = [rgb2hex(*centers[k]) for k in range(len(centers))]

    # detect lavender/orange border lines (a row/col that is mostly one off-pattern hue)
    def is_border_color(col):
        r, g, b = col
        return (b > 185 and b - r > 40) or (r > 200 and g > 120 and b < 120)  # lavender or orange
    border_cols = {c for c in range(a.cols)
                   if sum(is_border_color(cells[r][c]) for r in range(a.rows)) >= a.rows * 0.6}
    border_rows = {r for r in range(a.rows)
                   if sum(is_border_color(cells[r][c]) for c in range(a.cols)) >= a.cols * 0.6}
    keepC = [c for c in range(a.cols) if c not in border_cols]
    keepR = [r for r in range(a.rows) if r not in border_rows]
    idx = [[idx[r][c] for c in keepC] for r in keepR]
    ROWS, COLS = len(keepR), len(keepC)

    val = [[hexc[idx[r][c]] for c in range(COLS)] for r in range(ROWS)]

    if a.bg_light:
        # background = light colour(s) reachable from the border -> None
        def light(hx):
            r, g, b = (int(hx[i:i + 2], 16) for i in (1, 3, 5))
            return lum(r, g, b) > 222 and (max(r, g, b) - min(r, g, b)) < 26
        seen = [[False] * COLS for _ in range(ROWS)]; dq = deque()
        for r in range(ROWS):
            for c in range(COLS):
                if (r in (0, ROWS - 1) or c in (0, COLS - 1)) and light(val[r][c]) and not seen[r][c]:
                    dq.append((r, c)); seen[r][c] = True
        while dq:
            r, c = dq.popleft(); val[r][c] = None
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < ROWS and 0 <= nc < COLS and not seen[nr][nc] and val[nr][nc] and light(val[nr][nc]):
                    seen[nr][nc] = True; dq.append((nr, nc))

    for _ in range(a.despeckle):
        cp = [row[:] for row in val]
        for r in range(ROWS):
            for c in range(COLS):
                nb = [val[r + dr][c + dc] for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                      if 0 <= r + dr < ROWS and 0 <= c + dc < COLS]
                if nb and val[r][c] not in nb:
                    m = Counter([x if x else "_" for x in nb]).most_common(1)[0]
                    if m[1] >= 3:
                        cp[r][c] = None if m[0] == "_" else m[0]
        val = cp
    # remove floating singles in empty space
    for _ in range(2):
        for r in range(ROWS):
            for c in range(COLS):
                if val[r][c] is None:
                    continue
                nb = [val[r + dr][c + dc] for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                      if 0 <= r + dr < ROWS and 0 <= c + dc < COLS]
                if nb and all(x is None for x in nb):
                    val[r][c] = None

    json.dump(val, open(a.out, "w"))
    render_preview(val, a.preview)
    cnt = Counter(v for row in val for v in row if v)
    print(f"parsed {COLS}x{ROWS} | dropped border cols {sorted(border_cols)} rows {sorted(border_rows)}")
    print("beads:", sum(cnt.values()), "/ colours:", len(cnt))
    for h, n in cnt.most_common():
        print(f"  {h} x{n}")
    print("saved grid ->", a.out, "| preview ->", a.preview)


if __name__ == "__main__":
    main()
