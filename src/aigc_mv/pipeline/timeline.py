"""Build timeline.json and an ffmpeg slideshow preview."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from aigc_mv.schemas import Timeline, TimelineClip


def _load_shots(project_dir: Path) -> list[dict]:
    path = project_dir / "shots.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing {path}. Run: aigc-mv storyboard {project_dir}"
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("shots") or [])


def _make_plate_png(path: Path, shot: dict, size: tuple[int, int] = (1280, 720)) -> None:
    """Simple labeled color plate when no real render exists."""
    colors = [
        (32, 48, 80),
        (60, 40, 70),
        (40, 70, 55),
        (80, 50, 40),
        (45, 45, 75),
    ]
    idx = int(shot.get("shot_id", "s01").lstrip("s") or "1")
    bg = colors[(idx - 1) % len(colors)]
    img = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36
        )
        font_sm = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22
        )
    except OSError:
        font = ImageFont.load_default()
        font_sm = font

    title = f"{shot.get('shot_id', '?')}  {shot.get('framing', '')}"
    who = ", ".join(shot.get("who") or [])
    lyric = (shot.get("lyric_excerpt") or "")[:48]
    draw.text((48, 280), title, fill=(240, 240, 240), font=font)
    draw.text((48, 340), who, fill=(200, 210, 230), font=font_sm)
    draw.text((48, 380), lyric, fill=(180, 190, 200), font=font_sm)
    draw.text((48, 640), "AIGC MV preview plate", fill=(140, 150, 160), font=font_sm)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def write_timeline(project_dir: Path) -> Timeline:
    project_dir = Path(project_dir)
    shots = _load_shots(project_dir)
    plates_dir = project_dir / "plates"
    plates_dir.mkdir(parents=True, exist_ok=True)

    clips: list[TimelineClip] = []
    for shot in shots:
        sid = shot["shot_id"]
        plate = plates_dir / f"{sid}.png"
        if not plate.is_file():
            _make_plate_png(plate, shot)
        clips.append(
            TimelineClip(
                shot_id=sid,
                t0=float(shot["t0"]),
                t1=float(shot["t1"]),
                source=str(plate.relative_to(project_dir)),
            )
        )

    duration = max((c.t1 for c in clips), default=0.0)
    timeline = Timeline(
        project=project_dir.name,
        duration_sec=duration,
        clips=clips,
        output="edit/preview.mp4",
    )
    edit_dir = project_dir / "edit"
    edit_dir.mkdir(parents=True, exist_ok=True)
    out = edit_dir / "timeline.json"
    out.write_text(
        json.dumps(timeline.model_dump(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return timeline


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def render_preview(project_dir: Path, max_duration: float = 15.0) -> Path:
    """
    Render a short slideshow MP4 from plates using ffmpeg.
    Caps total length at max_duration for a quick local preview.
    """
    project_dir = Path(project_dir)
    timeline = write_timeline(project_dir)
    edit_dir = project_dir / "edit"
    edit_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = project_dir / timeline.output

    if not timeline.clips:
        raise RuntimeError("No clips in timeline.")

    if not _ffmpeg_available():
        raise RuntimeError("ffmpeg not found on PATH. Install ffmpeg to render preview.")

    # Build concat list with per-clip durations, capped
    remaining = max_duration
    list_path = edit_dir / "concat.txt"
    lines: list[str] = []
    for clip in timeline.clips:
        if remaining <= 0.05:
            break
        dur = min(clip.t1 - clip.t0, remaining)
        if dur <= 0:
            continue
        src = (project_dir / clip.source).resolve()
        # ffmpeg concat demuxer: duration after each file except we use -t via filter;
        # for image slideshow, classic pattern:
        lines.append(f"file '{src}'")
        lines.append(f"duration {dur:.3f}")
        remaining -= dur
    if not lines:
        raise RuntimeError("Nothing to render after duration cap.")
    # Repeat last file path without duration (concat demuxer requirement)
    last_file = next(l for l in reversed(lines) if l.startswith("file "))
    lines.append(last_file)
    list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_path),
        "-vsync",
        "vfr",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(out_mp4),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{proc.stderr[-2000:]}")
    return out_mp4
