#!/usr/bin/env python3
"""Regenerate the JevGB logo SVGs. Dev-only: needs `fonttools` and IBM Plex Sans
(SIL Open Font License) installed locally. The wordmark is converted to outlines,
so the shipped SVGs need no font."""
from __future__ import annotations

import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "brand"
FONT = Path(sys.argv[1] if len(sys.argv) > 1 else
            "/usr/share/fonts/truetype/sand-box/google/IBM Plex Sans/IBMPlexSans-VariableFont_wdth,wght.ttf")

INK, PAPER, ACCENT, ACCENT_ON_DARK = "#14171C", "#F7F6F2", "#0F766E", "#5FD3C3"


def wordmark_path(text: str, size: float, x0: float, baseline: float, tracking: float = -0.012) -> tuple[str, float]:
    font = TTFont(FONT)
    if "fvar" in font:
        font = instantiateVariableFont(font, {"wght": 600, "wdth": 100})
    gs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font["hmtx"]
    upm = font["head"].unitsPerEm
    s = size / upm
    pen = SVGPathPen(gs)
    x = x0
    for ch in text:
        g = cmap[ord(ch)]
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x, baseline)))
        x += hmtx[g][0] * s + tracking * size
    return pen.getCommands(), x - x0


def mark(fg_bg: str, bars: str, dot: str, mono: bool = False) -> str:
    """64-unit mark: a rounded tile with three shortening lines (a long context condensed
    into a brief) ending in a dot (the handoff point)."""
    tile = "" if mono else f'<rect width="64" height="64" rx="15" fill="{fg_bg}"/>'
    return (f'{tile}'
            f'<rect x="14" y="17" width="36" height="6" rx="3" fill="{bars}"/>'
            f'<rect x="14" y="29" width="25" height="6" rx="3" fill="{bars}"/>'
            f'<rect x="14" y="41" width="13" height="6" rx="3" fill="{bars}"/>'
            f'<circle cx="38" cy="44" r="5" fill="{dot}"/>')


def svg(w: float, h: float, body: str, title: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}" '
            f'role="img" aria-label="{title}"><title>{title}</title>{body}</svg>\n')


def main() -> None:
    OUT.mkdir(exist_ok=True)
    # Short name: slightly larger type, cap height (~0.7 em) centered on the 64-unit tile, gap ≈ 0.28 × tile.
    d, width = wordmark_path("JevGB", 41, 82, 46.3, tracking=-0.004)
    W = 82 + width + 4
    variants = {
        "logo-color.svg": (mark(INK, PAPER, ACCENT), INK),
        "logo-on-dark.svg": (mark(PAPER, INK, ACCENT), PAPER),
        "logo-mono-black.svg": (mark(INK, PAPER, PAPER), INK),
        "logo-mono-white.svg": (mark(PAPER, INK, INK), PAPER),
    }
    for name, (m, txt) in variants.items():
        (OUT / name).write_text(svg(W, 64, f'<g>{m}</g><path d="{d}" fill="{txt}"/>', "JevGB"))
    (OUT / "mark-color.svg").write_text(svg(64, 64, mark(INK, PAPER, ACCENT), "JevGB mark"))
    (OUT / "mark-mono.svg").write_text(svg(64, 64, mark("", "currentColor", "currentColor", mono=True), "JevGB mark"))
    (OUT / "favicon.svg").write_text(svg(64, 64, mark(INK, PAPER, ACCENT_ON_DARK), "JevGB"))
    print("wrote", ", ".join(sorted(p.name for p in OUT.glob("*.svg"))))


if __name__ == "__main__":
    main()
