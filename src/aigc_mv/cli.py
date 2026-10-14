"""Typer CLI for aigc-mv."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Optional

import typer
import yaml

from aigc_mv import __version__
from aigc_mv.canon import DEFAULT_KNOWLEDGE_DIR, build_prompt, get_canon, list_character_ids
from aigc_mv.lore import get_lore, list_lore_ids, load_lore, render_lyric_brief
from aigc_mv.pipeline.align import align_project
from aigc_mv.pipeline.storyboard import storyboard_project
from aigc_mv.pipeline.timeline import render_preview

app = typer.Typer(
    name="aigc-mv",
    help="AIGC music-video pipeline: canon + lore + align → storyboard → preview",
    no_args_is_help=True,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEMO_SRC = _REPO_ROOT / "projects" / "demo_og"


def _knowledge_opt() -> Path:
    return DEFAULT_KNOWLEDGE_DIR


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None, "--version", "-V", help="Show version and exit.", is_eager=True
    ),
) -> None:
    if version:
        typer.echo(__version__)
        raise typer.Exit()


@app.command("init-project")
def init_project(
    name: str = typer.Argument(..., help="New project folder name under projects/"),
    dest_root: Path = typer.Option(
        None, "--root", help="Projects root (default: <repo>/projects)"
    ),
) -> None:
    """Copy demo project structure into projects/NAME."""
    root = dest_root or (_REPO_ROOT / "projects")
    target = root / name
    if target.exists():
        typer.echo(f"Refusing to overwrite existing: {target}", err=True)
        raise typer.Exit(code=1)
    if not _DEMO_SRC.is_dir():
        typer.echo(f"Demo template missing: {_DEMO_SRC}", err=True)
        raise typer.Exit(code=1)

    shutil.copytree(_DEMO_SRC, target, ignore=shutil.ignore_patterns("edit", "plates", "clips", "*.json"))
    # Refresh brief name
    brief_path = target / "brief.yaml"
    if brief_path.is_file():
        data = yaml.safe_load(brief_path.read_text(encoding="utf-8")) or {}
        data["name"] = name
        brief_path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
    (target / "audio").mkdir(exist_ok=True)
    (target / "plates").mkdir(exist_ok=True)
    (target / "edit").mkdir(exist_ok=True)
    typer.echo(f"Created project: {target}")


@app.command("list-characters")
def list_characters_cmd(
    knowledge: Path = typer.Option(None, "--knowledge", help="Knowledge directory"),
) -> None:
    """List character IDs in the knowledge library."""
    kd = knowledge or _knowledge_opt()
    ids = list_character_ids(kd)
    if not ids:
        typer.echo("(no characters)")
        return
    for cid in ids:
        typer.echo(cid)


@app.command("get-canon")
def get_canon_cmd(
    character_id: str = typer.Argument(...),
    knowledge: Path = typer.Option(None, "--knowledge", help="Knowledge directory"),
) -> None:
    """Print character canon as JSON."""
    kd = knowledge or _knowledge_opt()
    try:
        data = get_canon(character_id, kd)
    except FileNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2))


@app.command("build-prompt")
def build_prompt_cmd(
    character_id: str = typer.Argument(...),
    scene: str = typer.Option(..., "--scene", help="Scene / action description"),
    framing: str = typer.Option("MCU", "--framing", help="ECU/CU/MCU/MS/WS/..."),
    wardrobe: Optional[str] = typer.Option(None, "--wardrobe"),
    style: Optional[str] = typer.Option(None, "--style", help="Override style family"),
    knowledge: Path = typer.Option(None, "--knowledge"),
    mj: bool = typer.Option(False, "--mj", help="Print Midjourney one-liner only"),
) -> None:
    """Build a Midjourney-style prompt from canon + scene."""
    kd = knowledge or _knowledge_opt()
    try:
        result = build_prompt(
            character_id,
            scene=scene,
            framing=framing,
            wardrobe=wardrobe,
            style_family=style,
            knowledge_dir=kd,
        )
    except FileNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)
    if mj:
        typer.echo(result["mj_string"])
    else:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("list-lore")
def list_lore_cmd(
    knowledge: Path = typer.Option(None, "--knowledge", help="Knowledge directory"),
) -> None:
    """List lore / 典故 card IDs."""
    kd = knowledge or _knowledge_opt()
    ids = list_lore_ids(kd)
    if not ids:
        typer.echo("(no lore)")
        return
    for lid in ids:
        typer.echo(lid)


@app.command("get-lore")
def get_lore_cmd(
    lore_id: str = typer.Argument(...),
    knowledge: Path = typer.Option(None, "--knowledge", help="Knowledge directory"),
) -> None:
    """Print lore card as JSON."""
    kd = knowledge or _knowledge_opt()
    try:
        data = get_lore(lore_id, kd)
    except FileNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2))


@app.command("lyric-brief")
def lyric_brief_cmd(
    lore_id: str = typer.Argument(...),
    knowledge: Path = typer.Option(None, "--knowledge", help="Knowledge directory"),
) -> None:
    """Print a Chinese-friendly lyric writing brief from a lore card."""
    kd = knowledge or _knowledge_opt()
    try:
        lore = load_lore(lore_id, kd)
    except FileNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)
    typer.echo(render_lyric_brief(lore))


@app.command("align")
def align_cmd(
    project: Path = typer.Argument(..., help="Project directory"),
    duration: Optional[float] = typer.Option(None, "--duration", help="Force duration seconds"),
) -> None:
    """Write beatmap.json (stub equal-split unless WhisperX later)."""
    try:
        bm = align_project(project, duration_sec=duration)
    except Exception as e:
        typer.echo(f"align failed: {e}", err=True)
        raise typer.Exit(code=1)
    typer.echo(
        f"Wrote {Path(project) / 'beatmap.json'} "
        f"({len(bm.segments)} segments, {bm.duration_sec}s, source={bm.source})"
    )


@app.command("storyboard")
def storyboard_cmd(
    project: Path = typer.Argument(...),
    knowledge: Path = typer.Option(None, "--knowledge"),
) -> None:
    """Write shots.json from beatmap + brief."""
    kd = knowledge or _knowledge_opt()
    try:
        shots = storyboard_project(project, knowledge_dir=kd)
    except Exception as e:
        typer.echo(f"storyboard failed: {e}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"Wrote {Path(project) / 'shots.json'} ({len(shots)} shots)")


@app.command("preview")
def preview_cmd(
    project: Path = typer.Argument(...),
    max_duration: float = typer.Option(15.0, "--max-duration", help="Cap preview length (sec)"),
) -> None:
    """ffmpeg slideshow preview → projects/.../edit/preview.mp4"""
    try:
        out = render_preview(project, max_duration=max_duration)
    except Exception as e:
        typer.echo(f"preview failed: {e}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"Preview: {out}")


if __name__ == "__main__":
    app()
