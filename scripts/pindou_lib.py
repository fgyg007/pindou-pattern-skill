"""Shared helpers for the 拼豆 (perler-bead) pattern skill.

Board physics (the thing that makes a printed pattern line up with a real board):
  pitch_mm = span_mm / (dots - 1)
  Standard board: dots=52, span=140mm  ->  pitch = 140/51 = 2.745mm
A grid is a 2D list (rows x cols) of "#RRGGBB" hex strings or None (None = no bead).
"""
import json
from collections import Counter

# A generic bead palette used when converting an arbitrary IMAGE.
# (When parsing an existing pattern SHEET we use the sheet's own legend colours instead.)
PALETTE = [
    ("白色", "#FFFFFF"), ("米白", "#F4ECD6"), ("浅灰", "#CBCBCB"),
    ("灰色", "#8A8A8A"), ("深灰", "#4D4D4D"), ("黑色", "#111111"),
    ("红色", "#E4322B"), ("大红", "#C8102E"), ("酒红", "#7A1F2B"),
    ("粉红", "#FF8FB1"), ("浅粉", "#FFC2D4"), ("玫红", "#E63E8E"),
    ("橙色", "#FF7A1A"), ("橘黄", "#FF9F1C"), ("黄色", "#FFD60A"),
    ("浅黄", "#FBE6A2"), ("草绿", "#6FCF45"), ("绿色", "#2DA44E"),
    ("深绿", "#16633A"), ("薄荷", "#57D9C0"), ("青色", "#1FB6C1"),
    ("天蓝", "#56B4E8"), ("蓝色", "#2D6CDF"), ("深蓝", "#1F3A93"),
    ("紫色", "#7B4BC9"), ("浅紫", "#B79CE6"), ("棕色", "#7A4B2B"),
    ("驼色", "#C79A5B"), ("肤色", "#FFD9B3"), ("咖啡", "#5A3A22"),
]
NAME_BY_HEX = {h.upper(): n for n, h in PALETTE}
PRGB = [(n, h, tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))) for n, h in PALETTE]


def hex2rgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rgb2hex(r, g, b):
    return "#%02X%02X%02X" % (int(r), int(g), int(b))


def lum(r, g, b):
    return 0.299 * r + 0.587 * g + 0.114 * b


def nearest_palette(r, g, b):
    """Nearest bead colour, weighted toward how the eye perceives differences."""
    best, bd = PALETTE[0][1], 1e18
    for _, h, (pr, pg, pb) in PRGB:
        dr, dg, db = r - pr, g - pg, b - pb
        d = 2 * dr * dr + 4 * dg * dg + 3 * db * db
        if d < bd:
            bd = d
            best = h
    return best


def pitch_mm(dots, span_mm=140.0):
    return span_mm / (dots - 1)


def count_beads(grid):
    """Return (total, [(hex, n), ...] sorted desc)."""
    c = Counter(v for row in grid for v in row if v)
    return sum(c.values()), c.most_common()


def name_for(hex_, name_map=None):
    if name_map and hex_ in name_map:
        return name_map[hex_]
    return NAME_BY_HEX.get(hex_.upper(), hex_)


def load_grid(path):
    return json.load(open(path))


def save_grid(grid, path):
    json.dump(grid, open(path, "w"))


def place_centered(small, N=52):
    """Center a rows x cols pattern into an N x N board of None."""
    rows, cols = len(small), len(small[0])
    oR, oC = (N - rows) // 2, (N - cols) // 2
    g = [[None] * N for _ in range(N)]
    for r in range(rows):
        for c in range(cols):
            g[oR + r][oC + c] = small[r][c]
    return g


def render_preview(grid, path, cell=14, board=(231, 227, 218), bead=True):
    """Render a grid as a bead-style PNG so you can VIEW it and judge quality."""
    from PIL import Image, ImageDraw
    R, Cn = len(grid), len(grid[0])
    im = Image.new("RGB", (Cn * cell, R * cell), board)
    d = ImageDraw.Draw(im)

    def shade(hx, f):
        r, g, b = hex2rgb(hx)
        return (int(r * f), int(g * f), int(b * f))

    for r in range(R):
        for c in range(Cn):
            x, y = c * cell, r * cell
            col = grid[r][c]
            if not col:
                d.ellipse([x + cell / 2 - 1, y + cell / 2 - 1,
                           x + cell / 2 + 1, y + cell / 2 + 1], fill=(205, 200, 192))
                continue
            if bead:
                rad = cell * 0.46
                X, Y = x + cell / 2, y + cell / 2
                d.ellipse([X - rad, Y - rad, X + rad, Y + rad], fill=col)
                hr = rad * 0.34
                d.ellipse([X - hr, Y - hr, X + hr, Y + hr], fill=shade(col, 0.78))
            else:
                d.rectangle([x, y, x + cell, y + cell], fill=col)
    im.save(path)
    return path
