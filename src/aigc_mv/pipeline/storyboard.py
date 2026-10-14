"""Rule-based storyboard from beatmap + brief (no paid LLM required)."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from aigc_mv.canon import build_prompt
from aigc_mv.schemas import Beatmap, ProjectBrief, Shot

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


def storyboard_project(project_dir: Path, knowledge_dir: Path | None = None) -> list[Shot]:
    """One shot per lyric segment; rotate framing/camera; attach build_prompt plates."""
    project_dir = Path(project_dir)
    brief = _load_brief(project_dir)
    beatmap = _load_beatmap(project_dir)

    cast = brief.characters or ["example_poet"]
    primary = cast[0]
    shots: list[Shot] = []

    for i, seg in enumerate(beatmap.segments):
        framing = FRAMING_CYCLE[i % len(FRAMING_CYCLE)]
        camera = CAMERA_CYCLE[i % len(CAMERA_CYCLE)]
        who = [cast[i % len(cast)]]
        action = f"performing on stage, lip-sync feel, lyric vibe: {seg.text[:40]}"
        scene = (
            f"{brief.concept}. {action}. "
            f"Ancient-meets-concert aesthetic, stage lights, vintage microphone."
        )
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
        "shots": [s.model_dump() for s in shots],
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return shots
