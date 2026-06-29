#!/usr/bin/env python3
"""Render a bead grid to a 1:1, mm-accurate printable PDF.

The whole point: when printed at 100% (actual size), the pattern's cell centres
sit exactly pitch_mm apart, so a real board laid on top lines up peg-for-peg.
Includes a 100mm calibration line, a major grid every 5 cells, peg dots on empty
cells, and a materials list.

REQUIRES a CJK font for Chinese text. Default looks for Noto Sans CJK; pass
--font to override. If none is found, falls back to a Latin font (codes/counts
still render; Chinese names may not).

Usage:
  python make_pdf.py grid.json --out pattern.pdf \
      [--dots 52] [--span 140] [--names names.json] [--title "..."]
"""
import argparse, json, os, sys, glob
from collections import Counter
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from pindou_lib import hex2rgb, pitch_mm, name_for

FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]


def find_font(override=None):
    for f in ([override] if override else []) + FONT_CANDIDATES:
        if f and os.path.exists(f):
            return f
    hits = glob.glob("/usr/share/fonts/**/*CJK*", recursive=True)
    return hits[0] if hits else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("grid")
    ap.add_argument("--out", default="pattern.pdf")
    ap.add_argument("--dots", type=int, default=52)
    ap.add_argument("--span", type=float, default=140.0)
    ap.add_argument("--names", default=None, help="optional json {hex: name}")
    ap.add_argument("--title", default=None)
    ap.add_argument("--font", default=None)
    a = ap.parse_args()

    grid = json.load(open(a.grid))
    N = a.dots
    pitch = pitch_mm(N, a.span)
    names = json.load(open(a.names)) if a.names else None

    DPI = 300; MM = DPI / 25.4
    def mm(v): return int(round(v * MM))
    PW, PH = 210, 297
    img = Image.new("RGB", (mm(PW), mm(PH)), "white")
    d = ImageDraw.Draw(img)
    fp = find_font(a.font)
    def font(sz): return ImageFont.truetype(fp, mm(sz)) if fp else ImageFont.load_default()
    def ctext(x, y, s, sz, fill=(34, 34, 34), anchor="mm"):
        d.text((mm(x), mm(y)), s, font=font(sz), fill=fill, anchor=anchor)

    # calibration line
    cal = 100; calX = (PW - cal) / 2; calY = 16
    d.line([mm(calX), mm(calY), mm(calX + cal), mm(calY)], fill=(20, 20, 20), width=mm(0.5))
    for xx in (calX, calX + cal):
        d.line([mm(xx), mm(calY - 2), mm(xx), mm(calY + 2)], fill=(20, 20, 20), width=mm(0.5))
    ctext(PW / 2, calY + 5, f"校准线 {cal}mm — 打印请选「100% / 实际大小」，打印后用尺子核对此线", 3.0)
    title = a.title or f"拼豆图纸 · 底板 {N}×{N} · 中心间距 {pitch:.3f}mm（{a.span:g}÷{N-1}）"
    ctext(PW / 2, calY + 11, title, 4.2, fill=(20, 20, 20))

    gridW = N * pitch; gx = (PW - gridW) / 2; gy = 33
    # fills
    for r in range(N):
        for c in range(N):
            col = grid[r][c]
            if col:
                x = gx + c * pitch; y = gy + r * pitch
                d.rectangle([mm(x), mm(y), mm(x + pitch), mm(y + pitch)], fill=hex2rgb(col))
    # grid lines (major every 5)
    for i in range(N + 1):
        w = mm(0.5) if i % 5 == 0 else max(1, mm(0.12))
        sh = (60, 60, 60) if i % 5 == 0 else (175, 175, 175)
        d.line([mm(gx + i * pitch), mm(gy), mm(gx + i * pitch), mm(gy + gridW)], fill=sh, width=w)
        d.line([mm(gx), mm(gy + i * pitch), mm(gx + gridW), mm(gy + i * pitch)], fill=sh, width=w)
    # peg dots on empty cells
    for r in range(N):
        for c in range(N):
            if not grid[r][c]:
                cxp = gx + c * pitch + pitch / 2; cyp = gy + r * pitch + pitch / 2
                d.ellipse([mm(cxp) - 2, mm(cyp) - 2, mm(cxp) + 2, mm(cyp) + 2], fill=(205, 205, 205))
    d.rectangle([mm(gx), mm(gy), mm(gx + gridW), mm(gy + gridW)], outline=(30, 30, 30), width=mm(0.6))

    # materials list
    cnt = Counter(grid[r][c] for r in range(N) for c in range(N) if grid[r][c])
    arr = cnt.most_common(); ly = gy + gridW + 8
    ctext(gx, ly, f"用料清单 · 共 {sum(cnt.values())} 颗 / {len(arr)} 色", 4.0, anchor="lm", fill=(20, 20, 20))
    ly += 7; colw = gridW / 3
    for i, (hex_, k) in enumerate(arr):
        col = i % 3; row = i // 3
        ex = gx + col * colw; ey = ly + row * 6.5
        d.rectangle([mm(ex), mm(ey - 2), mm(ex + 4), mm(ey + 2)], fill=hex2rgb(hex_),
                    outline=(120, 120, 120), width=max(1, mm(0.2)))
        ctext(ex + 5.5, ey, f"{name_for(hex_, names)}  ×{k}", 3.4, anchor="lm")

    img.save(a.out, "PDF", resolution=DPI)
    print("PDF saved ->", a.out, f"| pitch {pitch:.3f}mm | font {'OK' if fp else 'Latin-only'}")


if __name__ == "__main__":
    main()
