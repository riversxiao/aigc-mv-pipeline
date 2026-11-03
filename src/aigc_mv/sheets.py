"""Step 3 of the show 定妆 flow: tile the locked views of each person into refs/<cast_key>_sheet.png.

Video units upload exactly one sheet per person (prompts.MAX_FACE_REFS), so the five step-2 views
(face / 34 / profile / half / full) go into one image on the dark grey background: the full-body view on the left at
the height of two rows, the four other views in a 2x2 grid next to it. That keeps the sheet near 3:2, so the faces
stay large when 即梦/Seedance shrink a reference image (one row of five would be about 3.6:1). No text is burned in.
A sheet is only written when all five views exist (partial=True writes it anyway and the marker records the gap, so
`ep prompts` keeps flagging it). A sheet that was not made by this command (no PNG marker) is only replaced with force.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from aigc_mv.episode import Episode
from aigc_mv.prompts import SHEET_TILES

TILE_H = 640  # height of one grid row; the full-body tile spans two rows
GAP = 24
BG = (38, 38, 40)
MARKER = "aigc-mv-sheet"


@dataclass
class SheetResult:
    written: dict[str, list[str]] = field(default_factory=dict)  # cast key -> tiles used
    missing: dict[str, list[str]] = field(default_factory=dict)  # cast key -> tile files not in refs/ yet
    kept: list[str] = field(default_factory=list)  # hand-made sheets left alone (use force)
    skipped: list[str] = field(default_factory=list)  # incomplete sets not assembled (use partial)


def _marker(path: Path) -> str | None:
    try:
        with Image.open(path) as im:
            return getattr(im, "text", {}).get(MARKER)
    except OSError:
        return None


def is_assembled(path: Path) -> bool:
    return _marker(path) is not None


def sheet_gaps(path: Path) -> list[str]:
    """Views missing from a sheet made by `ep sheets --partial`; [] for a full or hand-made sheet."""
    m = _marker(path)
    if m is None:
        return []
    used = {n.rsplit("_", 1)[-1].removesuffix(".png") for n in m.split(",") if n}
    return [t for t in SHEET_TILES if t not in used]


def _fit(p: Path, height: int) -> Image.Image:
    im = Image.open(p).convert("RGB")
    w = max(1, round(im.width * height / im.height))
    return im.resize((w, height), Image.LANCZOS)


def assemble(tiles: list[Path], out: Path, height: int = TILE_H) -> Path:
    full = [p for p in tiles if p.stem.endswith("_full")]
    rest = [p for p in tiles if p not in full]
    rows = min(2, len(rest)) or 1
    cols = math.ceil(len(rest) / rows) if rest else 0
    sheet_h = rows * height + (rows - 1) * GAP
    left = [_fit(p, sheet_h) for p in full]
    grid = [_fit(p, height) for p in rest]
    col_w = [max(grid[r * cols + c].width for r in range(rows) if r * cols + c < len(grid)) for c in range(cols)]
    width = sum(i.width for i in left) + sum(col_w) + GAP * (len(left) + cols + 1)
    sheet = Image.new("RGB", (width, sheet_h + 2 * GAP), BG)
    x = GAP
    for im in left:
        sheet.paste(im, (x, GAP))
        x += im.width + GAP
    for c in range(cols):
        for r in range(rows):
            i = r * cols + c
            if i < len(grid):
                sheet.paste(grid[i], (x + (col_w[c] - grid[i].width) // 2, GAP + r * (height + GAP)))
        x += col_w[c] + GAP
    meta = PngInfo()
    meta.add_text(MARKER, ",".join(p.name for p in tiles))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, "PNG", pnginfo=meta)
    return out


def build_sheets(project_dir: Path, ep: Episode, force: bool = False, keys: list[str] | None = None,
                 partial: bool = False) -> SheetResult:
    refs = Path(project_dir) / "refs"
    res = SheetResult()
    for k in keys or list(ep.cast):
        have, miss = [], []
        for t in SHEET_TILES:
            p = refs / f"{k}_{t}.png"
            (have if p.is_file() else miss).append(p)
        if miss:
            res.missing[k] = [p.name for p in miss]
        if not have:
            continue
        if miss and not partial:
            res.skipped.append(k)
            continue
        out = refs / f"{k}_sheet.png"
        if out.is_file() and not force and not is_assembled(out):
            res.kept.append(k)
            continue
        assemble(have, out)
        res.written[k] = [p.name for p in have]
    return res
