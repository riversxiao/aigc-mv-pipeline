"""Rule-based storyboard from beatmap + brief (no paid LLM required)."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from aigc_mv.canon import build_prompt
from aigc_mv.lore import load_lore
from aigc_mv.schemas import Beatmap, LoreStory, ProjectBrief, Shot

FRAMING_CYCLE = ["WS", "MCU", "CU", "MS", "MCU"]
CAMERA_CYCLE = ["slow push-in", "static", "gentle pan left", "static", "orbit soft"]


def _load_brief(project_dir: Path) -> ProjectBrief:
    path = project_dir / "brief.yaml"
    if not path.is_file():
        return ProjectBrief(name=project_dir.name, concept="untitled")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if "name" not in data:
        data["name"] = project_dir.name
    return ProjectBrief.model_validate(data)


def _load_beatmap(project_dir: Path) -> Beatmap:
    path = project_dir / "beatmap.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing {path}. Run: aigc-mv align {project_dir}"
        )
    return Beatmap.model_validate_json(path.read_text(encoding="utf-8"))


def _optional_lore(brief: ProjectBrief, knowledge_dir: Path | None) -> LoreStory | None:
    if not brief.lore_id:
        return None
    try:
        return load_lore(brief.lore_id, knowledge_dir)
    except FileNotFoundError:
        return None


def storyboard_project(project_dir: Path, knowledge_dir: Path | None = None) -> list[Shot]:
    """One shot per lyric segment; rotate framing/camera; attach build_prompt plates."""
    project_dir = Path(project_dir)
    brief = _load_brief(project_dir)
    beatmap = _load_beatmap(project_dir)
    lore = _optional_lore(brief, knowledge_dir)

    cast = brief.characters or ["example_poet"]
    primary = cast[0]
    shots: list[Shot] = []

    lore_theme_hint = ""
    lore_allegory_hint = ""
    if lore:
        lore_theme_hint = " · ".join(lore.themes[:3]) if lore.themes else lore.classic_title
        lore_allegory_hint = lore.modern_allegory.strip().split("。")[0][:80]

    for i, seg in enumerate(beatmap.segments):
        framing = FRAMING_CYCLE[i % len(FRAMING_CYCLE)]
        camera = CAMERA_CYCLE[i % len(CAMERA_CYCLE)]
        who = [cast[i % len(cast)]]
        beat_hint = ""
        if lore and lore.scene_beats:
            beat_hint = lore.scene_beats[i % len(lore.scene_beats)]
        action = f"performing on stage, lip-sync feel, lyric vibe: {seg.text[:40]}"
        if beat_hint:
            action = f"{beat_hint}; {action}"
        if lore_theme_hint:
            action = f"{action} [themes: {lore_theme_hint}]"

        scene_bits = [brief.concept, action]
        if lore_allegory_hint:
            scene_bits.append(f"allegory mood: {lore_allegory_hint}")
        scene_bits.append(
            "Ancient-meets-concert aesthetic, stage lights, vintage microphone."
        )
        scene = ". ".join(scene_bits)

        try:
            built = build_prompt(
                who[0],
                scene=scene,
                framing=framing,
                knowledge_dir=knowledge_dir,
            )
            plate_prompt = built["mj_string"]
        except FileNotFoundError:
            # Fallback if character yaml missing
            plate_prompt = (
                f"{framing}, {scene}, {brief.style}, no text, no letters, no logos"
            )

        shots.append(
            Shot(
                shot_id=f"s{i + 1:02d}",
                t0=seg.t0,
                t1=seg.t1,
                who=who,
                framing=framing,
                action=action,
                plate_prompt=plate_prompt,
                camera=camera,
                lyric_excerpt=seg.text,
            )
        )

    # Always bookend with a wide establishing / group vibe if multi-cast
    if len(shots) >= 2 and len(cast) > 1:
        shots[0].who = cast[: min(3, len(cast))]
        shots[0].framing = "WS"
        shots[-1].who = cast[: min(3, len(cast))]
        shots[-1].framing = "WS"
        shots[-1].action = "group chorus energy, full stage"

    out = project_dir / "shots.json"
    payload = {
        "project": brief.name,
        "concept": brief.concept,
        "primary_character": primary,
        "lore_id": brief.lore_id,
        "shots": [s.model_dump() for s in shots],
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return shots
