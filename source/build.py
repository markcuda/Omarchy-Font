#!/usr/bin/env python3
"""Build "Omarchy Font.ttf" from glyphs.txt.

Every glyph in glyphs.txt is drawn on a grid of terminal cells using the
block characters the Omarchy wordmark is made of (█ ▀ ▄).  Each cell is one
unit wide and two units tall, exactly like the official logo.svg, so a
half-block is one square pixel.  The blocks of a glyph are traced into a
single set of merged outlines (no overlapping rectangles, hence no seams) and
written out as a TrueType font with fontTools.

    python3 build.py            # writes ../Omarchy Font.ttf
    python3 build.py out.ttf    # writes somewhere else
"""
from __future__ import annotations

import sys
from pathlib import Path

from fontTools.agl import UV2AGL
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables.O_S_2f_2 import Panose

UPM = 1000          # units per em
CELL_W = 50         # a terminal cell is 50 units wide ...
CELL_H = 100        # ... and 100 tall, the 1:2 aspect of the official logo.svg
PX = CELL_W // 2    # the drawing lattice: half a cell wide (for ▌ ▐) ...
PY = CELL_H // 2    # ... and half a cell tall (for ▀ ▄)
ROWS = 10           # row 0 = crown, rows 1-8 = body, row 9 = descender
TOP = 9 * CELL_H    # y of the top of row 0; the baseline is the bottom of row 8
ASCENDER = TOP
DESCENDER = TOP - ROWS * CELL_H   # -100: bottom of row 9
FAMILY = "Omarchy Font"
VERSION = 2.0

SPECIAL_NAMES = {"space": 0x20, "notdef": None}


def parse(path: Path) -> list[dict]:
    glyphs, cur = [], None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.startswith("## "):
            head = raw[3:].split()
            cur = {"key": head[0], "rows": [], "lsb": 1, "rsb": 1, "advance": None}
            for opt in head[1:]:
                k, v = opt.split("=")
                cur[k] = int(v)
            glyphs.append(cur)
        elif raw.startswith("|") and cur is not None:
            cur["rows"].append(raw.rstrip()[1:-1])
    for g in glyphs:
        if g["rows"]:
            assert len(g["rows"]) == ROWS, f"{g['key']}: expected {ROWS} rows"
            widths = {len(r) for r in g["rows"]}
            assert len(widths) == 1, f"{g['key']}: ragged rows {widths}"
            g["width"] = widths.pop()
        else:
            assert g["advance"] is not None, f"{g['key']}: empty glyph needs advance="
            g["width"] = 0
    return glyphs


# which quarters of a cell each block character fills: (left, right) x (upper, lower)
BLOCKS = {
    "█": {(0, 1), (1, 1), (0, 0), (1, 0)},
    "▀": {(0, 1), (1, 1)},
    "▄": {(0, 0), (1, 0)},
    "▌": {(0, 1), (0, 0)},
    "▐": {(1, 1), (1, 0)},
    " ": set(),
}


def pixels(g: dict) -> set[tuple[int, int]]:
    """Filled lattice squares as (x, y), y pointing up, in (PX, PY) units."""
    filled = set()
    for r, row in enumerate(g["rows"]):
        for c, ch in enumerate(row):
            if ch not in BLOCKS:
                raise ValueError(f"{g['key']}: unexpected character {ch!r}")
            x0 = 2 * (g["lsb"] + c)
            y0 = 2 * (ROWS - 2 - r)            # bottom of row 8 is y=0
            for dx, dy in BLOCKS[ch]:
                filled.add((x0 + dx, y0 + dy))
    return filled


def trace(filled: set[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    """Merge pixels into closed, non-overlapping outlines.

    Outer contours run clockwise (fill on the right-hand side of travel, y up),
    which is the TrueType convention, and holes come out counter-clockwise
    automatically.  Where two pixels only touch at a corner we prefer the
    right-hand turn so the shapes stay separate instead of pinching.
    """
    edges: dict[tuple[int, int], list[tuple[int, int]]] = {}

    def add(a, b):
        edges.setdefault(a, []).append(b)

    for (x, y) in filled:
        if (x, y + 1) not in filled: add((x, y + 1), (x + 1, y + 1))   # top
        if (x + 1, y) not in filled: add((x + 1, y + 1), (x + 1, y))   # right
        if (x, y - 1) not in filled: add((x + 1, y), (x, y))           # bottom
        if (x - 1, y) not in filled: add((x, y), (x, y + 1))           # left

    contours = []
    while edges:
        start = next(iter(edges))
        cur, prev_dir = start, None
        loop = []
        while True:
            outs = edges[cur]
            if prev_dir is None or len(outs) == 1:
                nxt = outs[0]
            else:
                dx, dy = prev_dir
                prefs = [(dy, -dx), (dx, dy), (-dy, dx)]        # right, straight, left
                nxt = next(o for d in prefs for o in outs if (o[0] - cur[0], o[1] - cur[1]) == d)
            outs.remove(nxt)
            if not outs:
                del edges[cur]
            loop.append(cur)
            prev_dir = (nxt[0] - cur[0], nxt[1] - cur[1])
            cur = nxt
            if cur == start:
                break
        # drop collinear points
        pts = []
        n = len(loop)
        for i, p in enumerate(loop):
            a, b = loop[i - 1], loop[(i + 1) % n]
            if (p[0] - a[0], p[1] - a[1]) != (b[0] - p[0], b[1] - p[1]):
                pts.append(p)
        contours.append(pts)
    return contours


def outline(g: dict):
    pen = TTGlyphPen(None)
    for contour in trace(pixels(g)):
        pen.moveTo((contour[0][0] * PX, contour[0][1] * PY))
        for x, y in contour[1:]:
            pen.lineTo((x * PX, y * PY))
        pen.closePath()
    return pen.glyph()


def glyph_name(key: str) -> str:
    if key in SPECIAL_NAMES:
        return ".notdef" if key == "notdef" else "space"
    return UV2AGL.get(ord(key), f"uni{ord(key):04X}")


def build(src: Path, out: Path) -> None:
    glyphs = parse(src)
    order, outlines, metrics, cmap = [".notdef"], {}, {}, {}
    for g in glyphs:
        name = glyph_name(g["key"])
        if name != ".notdef":
            order.append(name)
        outlines[name] = outline(g)
        if g["rows"]:
            advance = (g["lsb"] + g["width"] + g["rsb"]) * CELL_W
            metrics[name] = (advance, g["lsb"] * CELL_W)
        else:
            metrics[name] = (g["advance"] * CELL_W, 0)
        if g["key"] == "space":
            cmap[0x20] = cmap[0xA0] = name
        elif g["key"] != "notdef":
            cp = ord(g["key"])
            cmap[cp] = name
            if "A" <= g["key"] <= "Z":          # the face is unicase
                cmap[cp + 32] = name

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(outlines)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASCENDER, descent=DESCENDER, lineGap=0)
    fb.setupNameTable({
        "familyName": FAMILY,
        "styleName": "Regular",
        "uniqueFontIdentifier": f"{FAMILY} Regular {VERSION:.3f}",
        "fullName": FAMILY,
        "psName": "OmarchyFont-Regular",
        "version": f"Version {VERSION:.3f}",
        "description": ("Block display face in the style of the Omarchy wordmark. "
                        "Letters extend the Delta Corps Priest 1 FIGlet font by CoSMiC cHiLD; "
                        "digits and punctuation were drawn to match."),
        "manufacturer": "Mark Cuda",
        "designer": "Mark Cuda",
        "licenseDescription": "Free to use, share and modify. Not affiliated with Omarchy or 37signals.",
    })
    panose = Panose()
    panose.bFamilyType, panose.bWeight, panose.bProportion = 4, 8, 2   # decorative, heavy, monospaced-ish
    fb.setupOS2(
        sTypoAscender=ASCENDER, sTypoDescender=DESCENDER, sTypoLineGap=0,
        usWinAscent=ASCENDER, usWinDescent=-DESCENDER,
        sxHeight=8 * CELL_H, sCapHeight=8 * CELL_H,
        usWeightClass=400, usWidthClass=5, fsType=0,
        fsSelection=0x40 | 0x80,          # REGULAR | USE_TYPO_METRICS
        achVendID="MCUD",
        version=4, panose=panose,
    )
    fb.setupPost()
    fb.font["head"].fontRevision = VERSION
    fb.save(str(out))
    ink = sum(1 for g in glyphs if g["rows"])
    print(f"wrote {out} — {len(order)} glyphs ({ink} drawn), {len(cmap)} code points")


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else here.parent / "Omarchy Font.ttf"
    build(here / "glyphs.txt", target)
