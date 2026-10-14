"""Canon knowledge layer: load characters, get_canon, build_prompt."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from aigc_mv.schemas import Character

# Default knowledge root: <repo>/knowledge
_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KNOWLEDGE_DIR = _REPO_ROOT / "knowledge"
DEFAULT_CHARS_DIR = DEFAULT_KNOWLEDGE_DIR / "characters"

FRAMING_MAP = {
    "ECU": "extreme close-up",
    "CU": "close-up",
    "MCU": "medium close-up",
    "MS": "medium shot",
    "MLS": "medium long shot",
    "WS": "wide shot",
    "EWS": "extreme wide shot",
}


def _chars_dir(knowledge_dir: Path | None = None) -> Path:
    if knowledge_dir is None:
        return DEFAULT_CHARS_DIR
    return Path(knowledge_dir) / "characters"


def list_character_ids(knowledge_dir: Path | None = None) -> list[str]:
    d = _chars_dir(knowledge_dir)
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.yaml") if p.is_file())


def load_character(character_id: str, knowledge_dir: Path | None = None) -> Character:
    path = _chars_dir(knowledge_dir) / f"{character_id}.yaml"
    if not path.is_file():
        available = list_character_ids(knowledge_dir)
        raise FileNotFoundError(
            f"Character '{character_id}' not found at {path}. Available: {available}"
        )
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if "id" not in data:
        data["id"] = character_id
    return Character.model_validate(data)


def get_canon(character_id: str, knowledge_dir: Path | None = None) -> dict[str, Any]:
    """Return canon as a plain dict (JSON-serializable) for CLI / MCP."""
    char = load_character(character_id, knowledge_dir)
    return char.model_dump()


def build_prompt(
    character_id: str,
    scene: str,
    framing: str = "MCU",
    wardrobe: str | None = None,
    style_family: str | None = None,
    knowledge_dir: Path | None = None,
    extra_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Assemble a Midjourney-style prompt in fixed order:

    framing → identity (verbatim) → wardrobe → scene → style family → no-text ban.
    """
    char = load_character(character_id, knowledge_dir)
    framing_key = framing.upper().strip()
    framing_phrase = FRAMING_MAP.get(framing_key, framing.strip() or "medium close-up")

    wardrobe_text = (wardrobe if wardrobe is not None else char.wardrobe_default).strip()
    style_text = (style_family if style_family is not None else char.style_family).strip()
    scene_text = scene.strip()
    identity = char.identity.strip()

    parts = [
        framing_phrase,
        identity,
        wardrobe_text,
        scene_text,
        style_text,
        "no text, no letters, no logos",
    ]
    prompt = ", ".join(p for p in parts if p)

    params: dict[str, Any] = {
        "ar": "16:9",
        "stylize": 250,
        "v": "6",
    }
    if extra_params:
        params.update(extra_params)

    checklist = [
        "Identity text pasted verbatim (no paraphrase)",
        f"Framing set to {framing_key} ({framing_phrase})",
        "Wardrobe present",
        "Scene / action present",
        "Style family present",
        "No-text / no-logos ban present",
        *[f"Avoid: {f}" for f in char.forbidden],
    ]

    return {
        "character_id": character_id,
        "prompt": prompt,
        "params": params,
        "checklist": checklist,
        "mj_string": f"{prompt} --ar {params['ar']} --stylize {params['stylize']} --v {params['v']}",
    }
