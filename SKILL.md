---
name: pindou-pattern
description: >
  Make perler-bead / fuse-bead / Hama-bead patterns (拼豆/拼豆图纸/咕卡像素图) that print
  1:1 to match a physical pegboard, and turn images or existing pattern sheets into clean,
  editable bead charts. Use this whenever the user wants to convert a picture into a 拼豆/perler
  pattern, clean up or resize an existing pattern sheet, generate a printable bead chart that
  lines up with their board, count how many beads of each colour are needed, or get an editable
  pixel-grid tool for beads — even if they just paste an image and say "make this into 拼豆" or
  mention pegboard sizes, bead counts, or printing a pattern to scale. Prefer this skill over
  ad-hoc pixelation; the value is vision-guided conversion plus mm-accurate output.
---

# 拼豆 / Perler-Bead Pattern Maker

Turn an **image** or an **existing pattern sheet** into a clean bead chart, then deliver an
**editable HTML tool** + a **1:1 printable PDF** + a **materials list**. The defining feature is
physical accuracy: when the PDF is printed at 100%, every cell centre sits one bead-pitch apart,
so the user can lay their real board on top and bead it directly.

## The core principle (read this first)

Turning a picture into a good low-resolution bead chart is a **judgement** task, not a fixed
algorithm. The scripts here are precise tools; **you** are the eyes. The workflow is always:
**look → set parameters → run → VIEW the preview → adjust → repeat.** Never hand the user a
raw auto-conversion without looking at the rendered preview yourself and iterating at least once.

Be honest about the ceiling: a **single clear subject** (cartoon, sticker, emoji, logo, pixel
art) converts beautifully. A **busy photo or multi-subject scene** cannot be made clean at
52×52 — that's a resolution limit no method escapes. Say so, and offer to focus on one subject
or go larger.

## Board physics

`pitch_mm = span_mm / (dots − 1)`. Standard board: **dots = 52, span = 140mm → pitch = 2.745mm**
(`140 ÷ 51`). The board pitch is a property of the *board*, independent of how many cells the
design uses. Default to a 52×52 board; place smaller designs centred inside it.

The #1 reason a printed chart "doesn't match the board" is **print scaling**, not the grid. The
PDF always carries a 100mm calibration line — tell the user to print at **100% / actual size**
(not "fit to page") and measure that line.

## Environment

- Python with Pillow + numpy. Run scripts from `scripts/` (they import `pindou_lib.py`).
- The PDF needs a CJK font for Chinese text; `make_pdf.py` finds Noto Sans CJK automatically. If
  absent, codes/counts still print (Chinese names may not).
- All work happens locally on the user's files.

---

## Path A — Image → pattern (vision-driven, iterate)

Use when the user gives a photo/illustration/sticker to convert.

1. **Look at the image.** Identify the subject, a sensible square crop, roughly how many colours,
   and whether it has clear dark outlines (cartoons do; photos don't). Decide background handling:
   `transparent` (bead only the subject — usually best for a board), `cream` (soft filled
   background), or `keep`.

2. **Convert and preview:**
   ```bash
   python scripts/image_to_pattern.py INPUT.png --out grid.json --preview prev.png \
       --cells 52 --bg transparent
   ```
   Useful flags: `--crop X0 Y0 X1 Y1` to override the auto subject-crop (pass the pixel box you
   judged); `--outline 0.26` for a thicker black outline, higher (e.g. `0.40`) or `--no-strengthen`
   for a softer block look.

3. **VIEW `prev.png`.** Judge it like a human: Is the subject framed well? Are outlines continuous?
   Colours right? Stray specks? Re-run with adjusted `--crop` / `--outline` / `--bg` until it reads
   cleanly. This loop is the whole point — expect 1–3 passes.

4. When happy, **finalize** (place into the board, build deliverables): see "Deliverables" below.
   The output of step 2 is already 52×52 if `--cells 52`, so it can go straight to PDF/tool. If you
   converted at a smaller `--cells`, centre it first (see Deliverables).

## Path B — Existing pattern sheet → cleaned chart

Use when the user gives an already-made pattern image (rows of coloured cells with code labels and
a legend, often watermarked).

1. **Look at the sheet** and read off the geometry from the numbered axes: the grid size
   (`--rows`, `--cols`) and the **pixel rectangle of the cell area** — top-left corner of cell
   (1,1) to bottom-right corner of the last cell. Watch for a row/column of axis *numbers* that
   isn't part of the pattern; exclude it from the rectangle (the script also auto-drops obvious
   lavender/orange border lines).

2. **Parse and preview:**
   ```bash
   python scripts/parse_sheet.py SHEET.png --rows 52 --cols 52 \
       --bounds X0 Y0 X1 Y1 --out grid.json --preview prev.png
   ```
   Colours are auto-clustered from the cells; the light border-connected colour becomes empty
   (no bead). Critical detail handled for you: cells are sampled on an **edge ring**, avoiding the
   centre code text.

3. **VIEW `prev.png`** and compare to the sheet. If it's shifted or shows a stray border strip,
   your `--bounds`/size are slightly off — re-read the axes and rerun. A correct parse reproduces
   the picture and its colour counts closely.

4. **Finalize** as below. Existing sheets are often already 52×52; if smaller, centre into the board.

---

## Deliverables (both paths)

1. **Place into the board if needed.** If the grid isn't 52×52, centre it:
   ```python
   import json, sys; sys.path.insert(0,"scripts"); from pindou_lib import place_centered, save_grid
   save_grid(place_centered(json.load(open("grid.json")), 52), "grid52.json")
   ```

2. **1:1 PDF:**
   ```bash
   python scripts/make_pdf.py grid52.json --out 拼豆图纸_52x52.pdf --dots 52 --span 140
   ```
   (Pass `--names names.json` with `{hex: "名称"}` to label the materials list; `--title "..."` to
   customize.)

3. **Editable HTML tool (pre-loaded):**
   ```bash
   python scripts/build_tool.py grid52.json --out 拼豆工具.html
   ```

4. **Present both files** with `present_files`, and give the materials list (printed by the
   scripts). Remind the user to **print the PDF at 100% / actual size** and check the calibration
   line, then lay the board on top.

## Tips & troubleshooting

- Outlines came out grey/broken → lower `--outline` (e.g. 0.26) so more dark cells read as solid
  black; strengthening then bridges gaps.
- Background bled into the subject → the outline has a gap; lower `--outline` to close the ring, or
  switch `--bg keep` and clean by hand in the tool.
- Sheet parse shows a thin coloured strip at an edge → an axis number column got included; tighten
  `--bounds`.
- Colours look off after parsing a sheet → that sheet uses its own brand palette; clustering keeps
  the actual colours, which is what you want for fidelity.
- More palette/values and rationale: see `references/workflow.md`.

The in-browser "上传图片" button in the tool runs a lightweight version of Path A as a convenience,
but it can't apply your visual judgement — for anything beyond a clean single subject, do the
conversion here (vision + code) rather than relying on that button.
