"""Step 3 of the show 定妆 flow: tile the locked views of each person into refs/<cast_key>_sheet.png.

Video units upload exactly one sheet per person (prompts.MAX_FACE_REFS), so the five step-2 views
(face / 34 / profile / half / full) are laid out side by side at a fixed height on the dark grey backdrop.
No text is burned in. A sheet that was not made by this command (no PNG marker) is only replaced with force.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from aigc_mv.episode import Episode
from aigc_mv.prompts import SHEET_TILES

TILE_H = 768
GAP = 24
BG = (38, 38, 40)
MARKER = "aigc-mv-sheet"


@dataclass
class SheetResult:
    written: dict[str, list[str]] = field(default_factory=dict)  # cast key -> tiles used
    missing: dict[str, list[str]] = field(default_factory=dict)  # cast key -> tile files not in refs/ yet
    kept: list[str] = field(default_factory=list)  # hand-made sheets left alone (use force)


def is_assembled(path: Path) -> bool:
    try:
        with Image.open(path) as im:
            return MARKER in getattr(im, "text", {})
    except OSError:
        return False


def assemble(tiles: list[Path], out: Path, height: int = TILE_H) -> Path:
    ims = []
    for p in tiles:
        im = Image.open(p).convert("RGB")
        w = max(1, round(im.width * height / im.height))
        ims.append(im.resize((w, height), Image.LANCZOS))
    width = sum(i.width for i in ims) + GAP * (len(ims) + 1)
    sheet = Image.new("RGB", (width, height + 2 * GAP), BG)
    x = GAP
    for im in ims:
        sheet.paste(im, (x, GAP))
        x += im.width + GAP
    meta = PngInfo()
    meta.add_text(MARKER, ",".join(p.name for p in tiles))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, "PNG", pnginfo=meta)
    return out


def build_sheets(project_dir: Path, ep: Episode, force: bool = False, keys: list[str] | None = None) -> SheetResult:
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
        out = refs / f"{k}_sheet.png"
        if out.is_file() and not force and not is_assembled(out):
            res.kept.append(k)
            continue
        assemble(have, out)
        res.written[k] = [p.name for p in have]
    return res
