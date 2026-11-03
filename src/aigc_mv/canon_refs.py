"""Official canon art for fan-work episodes: place one local reference image per canon cast member.

Images land in projects/<ep>/refs/canon/<card_id>.jpg, which is gitignored: official art is copyrighted and must
never be committed. Sources: a local folder (--src) first, otherwise the Bangumi API (images.large).
"""

from __future__ import annotations

import io
import json
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from aigc_mv.episode import Episode
from aigc_mv.prompts import characters

BANGUMI_API = "https://api.bgm.tv/v0/characters/{id}"
USER_AGENT = "aigc-mv-pipeline/0.1 (fan-work reference fetch; local use only)"
CANON_DIR = Path("refs") / "canon"
IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp")


@dataclass
class CanonResult:
    placed: dict[str, str] = field(default_factory=dict)  # cast key -> how ("copied" / "downloaded" / "exists")
    original: list[str] = field(default_factory=list)  # cast keys without canon art
    failed: dict[str, str] = field(default_factory=dict)  # cast key -> error
    sources: dict[str, tuple[str, str]] = field(default_factory=dict)  # card id -> (page url, image url or path)


def api_url(char_id: int) -> str:
    return BANGUMI_API.format(id=char_id)


def _get(url: str, timeout: float = 30.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, image/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def bangumi_image_url(char_id: int) -> str:
    data = json.loads(_get(api_url(char_id)).decode("utf-8"))
    imgs = data.get("images") or {}
    url = imgs.get("large") or imgs.get("medium") or ""
    if not url:
        raise ValueError(f"Bangumi character {char_id} has no image")
    return url


def _local(src: Path | None, card_id: str) -> Path | None:
    if src is None:
        return None
    for ext in IMG_EXTS:
        p = Path(src) / f"{card_id}{ext}"
        if p.is_file():
            return p
    return None


def _save_jpeg(data: bytes, dst: Path) -> None:
    """Store the image as real JPEG: step-1 uploads always point at refs/canon/<card_id>.jpg."""
    if data[:2] == b"\xff\xd8":
        dst.write_bytes(data)
        return
    from PIL import Image

    with Image.open(io.BytesIO(data)) as im:
        im.convert("RGB").save(dst, "JPEG", quality=95)


def _read_sources(out_dir: Path) -> dict[str, tuple[str, str]]:
    """Rows of an earlier SOURCES.md, so provenance survives re-runs."""
    p = out_dir / "SOURCES.md"
    rows: dict[str, tuple[str, str]] = {}
    if not p.is_file():
        return rows
    for line in p.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[0] not in ("角色卡", "") and not set(cells[0]) <= set("-"):
            rows[cells[0]] = (cells[1], cells[2])
    return rows


def fetch_canon(ep_dir: Path, ep: Episode, src: Path | None = None, knowledge_dir: Path | None = None) -> CanonResult:
    out_dir = Path(ep_dir) / CANON_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    res = CanonResult()
    old = _read_sources(out_dir)
    for k, ch in characters(ep, knowledge_dir).items():
        if not ch.canon_refs:
            res.original.append(k)
            continue
        ref = ch.canon_refs[0]
        dst = out_dir / f"{ch.id}.jpg"
        if dst.is_file():
            res.placed[k] = "exists"
            res.sources.setdefault(ch.id, old.get(ch.id) or (ref.url, f"existing local file {dst.name}"))
            continue
        try:
            local = _local(src, ch.id)
            if local is not None:
                _save_jpeg(local.read_bytes(), dst)
                res.placed[k] = "copied"
                res.sources[ch.id] = (ref.url, f"local copy of {local.name}")
            elif ref.site == "bangumi":
                img = bangumi_image_url(ref.id)
                _save_jpeg(_get(img), dst)
                res.placed[k] = "downloaded"
                res.sources[ch.id] = (ref.url, img)
            else:
                raise ValueError(f"no local image and site {ref.site!r} is not fetchable")
        except Exception as exc:  # noqa: BLE001 - report and keep going for the rest of the cast
            res.failed[k] = str(exc)
    for cid, row in old.items():  # rows for cards no longer in this cast stay on record
        res.sources.setdefault(cid, row)
    _write_sources(out_dir, ep, res)
    return res


def _write_sources(out_dir: Path, ep: Episode, res: CanonResult) -> None:
    lines = [
        "# 原作参考图来源（仅本地使用，不提交）",
        "",
        "这些是官方版权图，只用来给第一步「原作图 -> 真人正面像」做参考，文件夹已被 .gitignore 忽略，不要提交，不要二次发布。",
        "",
        "| 角色卡 | 角色页 | 图片来源 |",
        "|---|---|---|",
    ]
    for cid, (page, img) in sorted(res.sources.items()):
        lines.append(f"| {cid} | {page} | {img} |")
    if res.original:
        names = "、".join(ep.cast[k].name_cn for k in res.original)
        lines += ["", f"原创角色（无原作图，第一步用文生图）：{names}"]
    (out_dir / "SOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
