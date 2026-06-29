#!/usr/bin/env python3
"""Bake a bead grid into the editable HTML tool so it opens pre-loaded.

The user can then tweak with pen / eraser / fill in the browser and export their
own 1:1 PDF. The grid should be 52x52 (place smaller patterns centred first with
pindou_lib.place_centered) since the tool defaults to the 52x52 board.

Usage:
  python build_tool.py grid.json --out tool.html [--template assets/tool_template.html]
"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TPL = os.path.join(HERE, "..", "assets", "tool_template.html")

INIT_OLD = ('grid=makeGrid(cols,rows);setSelected(selected);setTool("pen");'
            'refreshBoardReadout();resizeCanvas();refreshUndo();')
INIT_NEW = ('grid=(window.__INITIAL&&window.__INITIAL.length===rows&&'
            'window.__INITIAL[0].length===cols)?window.__INITIAL.map(r=>r.slice()):'
            'makeGrid(cols,rows);setSelected(selected);setTool("pen");'
            'refreshBoardReadout();resizeCanvas();refreshUndo();')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("grid")
    ap.add_argument("--out", default="tool.html")
    ap.add_argument("--template", default=DEFAULT_TPL)
    a = ap.parse_args()
    grid = json.load(open(a.grid))
    html = open(a.template, encoding="utf-8").read()
    inject = "<script>window.__INITIAL=" + json.dumps(grid, separators=(",", ":")) + ";</script>\n<script>"
    if "window.__INITIAL" not in html:
        html = html.replace("<script>\n(function(){", inject + "\n(function(){", 1)
    if INIT_OLD in html:
        html = html.replace(INIT_OLD, INIT_NEW, 1)
    open(a.out, "w", encoding="utf-8").write(html)
    print("tool written ->", a.out, f"({round(len(html)/1024,1)} KB)")


if __name__ == "__main__":
    main()
