"""Lore knowledge layer: load classical anecdote cards for MV allegory."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from aigc_mv.schemas import LoreStory

# Default knowledge root: <repo>/knowledge
_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KNOWLEDGE_DIR = _REPO_ROOT / "knowledge"
DEFAULT_LORE_DIR = DEFAULT_KNOWLEDGE_DIR / "lore"


def _lore_dir(knowledge_dir: Path | None = None) -> Path:
    if knowledge_dir is None:
        return DEFAULT_LORE_DIR
    return Path(knowledge_dir) / "lore"


def get_lore_path(lore_id: str, knowledge_dir: Path | None = None) -> Path:
    return _lore_dir(knowledge_dir) / f"{lore_id}.yaml"


def list_lore_ids(knowledge_dir: Path | None = None) -> list[str]:
    d = _lore_dir(knowledge_dir)
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.yaml") if p.is_file())


def load_lore(lore_id: str, knowledge_dir: Path | None = None) -> LoreStory:
    path = get_lore_path(lore_id, knowledge_dir)
    if not path.is_file():
        available = list_lore_ids(knowledge_dir)
        raise FileNotFoundError(
            f"Lore '{lore_id}' not found at {path}. Available: {available}"
        )
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if "id" not in data:
        data["id"] = lore_id
    return LoreStory.model_validate(data)


def get_lore(lore_id: str, knowledge_dir: Path | None = None) -> dict[str, Any]:
    """Return lore as a plain dict (JSON-serializable) for CLI / MCP."""
    return load_lore(lore_id, knowledge_dir).model_dump()


def render_lyric_brief(lore: LoreStory | str, knowledge_dir: Path | None = None) -> str:
    """
    Chinese-friendly brief for songwriting: classic summary + allegory + seeds.

    Accepts a LoreStory or lore id string.
    """
    if isinstance(lore, str):
        lore = load_lore(lore, knowledge_dir)

    themes = " · ".join(lore.themes) if lore.themes else "（未填）"
    seeds = "\n".join(f"- {s}" for s in lore.lyric_seeds) or "- （暂无）"
    beats = "\n".join(f"- {b}" for b in lore.scene_beats) or "- （暂无）"
    avoid = "、".join(lore.avoid) if lore.avoid else "政治讽刺"

    lines = [
        f"# 歌词创作简报 · {lore.classic_title}",
        f"典故 ID：{lore.id}　出处：{lore.source}",
        "",
        "## 经典本事（中性）",
        lore.classic_summary.strip(),
        "",
        "## 借古讽今（非政治）",
        lore.modern_allegory.strip(),
        "",
        f"## 主题关键词\n{themes}",
        "",
        "## 歌词种子",
        seeds,
        "",
        "## 分镜节拍建议",
        beats,
        "",
        f"## 创作禁区\n勿写：{avoid}",
    ]
    if lore.notes.strip():
        lines.extend(["", "## 备注", lore.notes.strip()])
    return "\n".join(lines) + "\n"
