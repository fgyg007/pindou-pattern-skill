# 拼豆 / Perler-Bead Pattern Maker

A [Claude Code](https://claude.com/claude-code) **Skill** that turns an **image** or an **existing pattern sheet** into a clean bead chart, then delivers an **editable HTML tool** + a **1:1 printable PDF** + a **materials list**.

> 把一张图片或现成图纸，变成干净的拼豆图纸：可编辑的网页工具 + 1:1 可打印 PDF + 用料清单。

The defining feature is **physical accuracy**: when the PDF is printed at 100%, every cell centre sits one bead-pitch apart, so you can lay your real pegboard on top and bead it directly.

## Features

- **Image → pattern** — vision-guided conversion of a photo / sticker / logo into a low-res bead chart (52×52 by default), with iterative preview.
- **Pattern sheet → cleaned chart** — parse an existing (often watermarked) pattern image back into an editable grid.
- **1:1 printable PDF** — carries a 100mm calibration line; print at *actual size* and the grid matches a standard 140mm / 52-dot board (pitch 2.745mm).
- **Editable HTML tool** — a pixel-grid editor pre-loaded with your pattern.
- **Materials list** — per-colour bead counts.

## Installation

This is a Claude Code skill. Install it into your user-level skills directory:

```bash
git clone https://github.com/fgyg007/pindou-pattern.git ~/.claude/skills/pindou-pattern
```

Then restart Claude Code (or start a new session) so the skill is loaded. You can now say things like *"把这张图做成拼豆图纸"* / *"make this image into a perler pattern"*, or invoke `/pindou-pattern`.

## Requirements

The scripts need Python with:

```bash
pip install -r requirements.txt
```

- **Pillow** + **numpy** are required.
- The PDF labels Chinese colour names if a CJK font (Noto Sans CJK) is available; otherwise codes/counts still print.

## Usage

The skill drives the scripts for you, but you can also run them directly from `scripts/`:

```bash
# Image → pattern (preview, then iterate)
python scripts/image_to_pattern.py INPUT.png --out grid.json --preview prev.png --cells 52 --bg transparent

# Existing sheet → cleaned chart
python scripts/parse_sheet.py SHEET.png --rows 52 --cols 52 --bounds X0 Y0 X1 Y1 --out grid.json --preview prev.png

# 1:1 printable PDF
python scripts/make_pdf.py grid.json --out pattern_52x52.pdf --dots 52 --span 140

# Editable HTML tool
python scripts/build_tool.py grid.json --out tool.html
```

See [`SKILL.md`](SKILL.md) for the full workflow and [`references/workflow.md`](references/workflow.md) for palette/values rationale.

## Board physics

`pitch_mm = span_mm / (dots − 1)`. Standard board: **dots = 52, span = 140mm → pitch = 2.745mm**. The #1 reason a printed chart "doesn't match the board" is **print scaling** — always print at **100% / actual size** and measure the calibration line.

## License

[MIT](LICENSE)
