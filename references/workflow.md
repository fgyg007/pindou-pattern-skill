# 拼豆 pattern reference

Deeper notes for the skill. Read when you need palette values, parameter detail, or to debug a
conversion. The SKILL.md workflow is the source of truth for *steps*; this file is *detail*.

## Board geometry

- `pitch_mm = span_mm / (dots − 1)`.
- Standard square board: dots 52, span (first-peg-centre to last-peg-centre) 140mm → pitch 2.745mm.
  Full board ≈ dots × pitch ≈ 142.7mm.
- Other boards: ask for the user's two numbers (dots per side, and the centre-to-centre span in mm)
  and pass them to `make_pdf.py` via `--dots`/`--span`. The pitch is a board property; a design
  smaller than the board still uses the board's pitch (place it centred, leave the rest empty).
- Printing: the cause of misalignment is almost always the printer scaling the page. Always print
  at 100% / actual size, disable "fit to page", and verify the 100mm calibration line with a ruler.

## Generic bead palette (for IMAGE conversion)

Used by `image_to_pattern.py` (nearest-colour). Names are Chinese; hex is the swatch.

| name | hex | | name | hex |
|---|---|---|---|---|
| 白色 | #FFFFFF | | 草绿 | #6FCF45 |
| 米白 | #F4ECD6 | | 绿色 | #2DA44E |
| 浅灰 | #CBCBCB | | 深绿 | #16633A |
| 灰色 | #8A8A8A | | 薄荷 | #57D9C0 |
| 深灰 | #4D4D4D | | 青色 | #1FB6C1 |
| 黑色 | #111111 | | 天蓝 | #56B4E8 |
| 红色 | #E4322B | | 蓝色 | #2D6CDF |
| 大红 | #C8102E | | 深蓝 | #1F3A93 |
| 酒红 | #7A1F2B | | 紫色 | #7B4BC9 |
| 粉红 | #FF8FB1 | | 浅紫 | #B79CE6 |
| 浅粉 | #FFC2D4 | | 棕色 | #7A4B2B |
| 玫红 | #E63E8E | | 驼色 | #C79A5B |
| 橙色 | #FF7A1A | | 肤色 | #FFD9B3 |
| 橘黄 | #FF9F1C | | 咖啡 | #5A3A22 |
| 黄色 | #FFD60A | | | |
| 浅黄 | #FBE6A2 | | | |

When parsing an existing SHEET, ignore this palette — keep the sheet's own clustered colours so the
result matches the original brand codes.

## image_to_pattern.py parameters

- `--cells N` board/grid size (default 52).
- `--crop X0 Y0 X1 Y1` override the auto subject crop. The auto crop frames the union of sizable
  near-black blocks (good for outlined cartoons). For images without dark outlines, the auto crop
  falls back to the whole image — pass an explicit crop you judged by eye.
- `--outline F` dark-fraction threshold for calling a cell black (default 0.30). Lower → thicker,
  more continuous outline. Raise or `--no-strengthen` → softer, no forced black edges.
- `--bg cream|transparent|keep`:
  - `transparent` → exterior becomes empty (no bead); best when the user lays a board on the print.
  - `cream` → exterior filled with #F4ECD6 (soft tile look).
  - `keep` → no background processing; quantised background stays.
- `--despeckle K` passes of lone-cell cleanup (default 2).

Pipeline order: subject-crop → block-downsample (avg colour + dark fraction per cell) →
black mask at threshold → (strengthen: bridge 1-cell gaps between black neighbours, drop isolated
black) → quantise non-black cells to palette → background flood from corners → despeckle.

## parse_sheet.py parameters

- `--rows`/`--cols` the grid size from the sheet's axis numbers.
- `--bounds X0 Y0 X1 Y1` the cell-area rectangle in source pixels (corner of cell 1,1 to corner of
  last cell). Read it from the numbered axes. Excluding the axis-number band matters.
- Sampling uses an **edge ring** per cell (avoids the centre code label). Colours auto-cluster.
- `--bg-light 1` (default) floods the light border-connected colour to empty (no bead). Set 0 to
  keep every cell as a bead.
- Auto-drops a row/column that is ≥60% lavender or orange (common axis/border tints).

If a parse is shifted: the bounds are off by a fraction of a cell; re-read the corners. If a thin
coloured strip appears at one edge: an axis number column slipped into the bounds — tighten them.

## make_pdf.py / build_tool.py

- PDF is A4 portrait at 300 DPI, image saved with DPI metadata so 1mm in the doc = 1mm on paper.
- Empty cells render as light peg dots so the unused board area is still visible for alignment.
- `build_tool.py` injects the grid as `window.__INITIAL` into `assets/tool_template.html`; the tool
  defaults to a 52×52 board, so feed it a 52×52 grid.

## Honest limits

- 52×52 is low resolution. Fine detail (small faces, text, thin lines) won't survive. Pick subjects
  whose silhouette and big shapes carry the recognition.
- Multi-subject or photographic scenes: offer to (a) focus on one subject, (b) go to a larger board
  if the user has one, or (c) accept a loose, impressionistic result. Don't pretend the algorithm
  can make it crisp.
- Vision-in-the-loop beats the in-browser button every time for non-trivial images; that button is
  only a convenience fallback.
