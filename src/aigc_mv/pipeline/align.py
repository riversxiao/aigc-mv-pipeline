"""Align lyrics to time — stub without WhisperX."""

from __future__ import annotations

import json
import wave
from pathlib import Path

from aigc_mv.schemas import Beatmap, LyricSegment

DEFAULT_DURATION = 30.0
DEFAULT_BPM = 90.0


def _audio_duration_sec(audio_path: Path) -> float | None:
    """Best-effort duration from WAV; return None for other formats."""
    if not audio_path.is_file():
        return None
    if audio_path.suffix.lower() != ".wav":
        return None
    try:
        with wave.open(str(audio_path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate <= 0:
                return None
            return frames / float(rate)
    except Exception:
        return None


def _read_lyrics_lines(lyrics_path: Path) -> list[str]:
    if not lyrics_path.is_file():
        return ["(no lyrics)"]
    lines = []
    for raw in lyrics_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    return lines or ["(empty lyrics)"]


def align_project(project_dir: Path, duration_sec: float | None = None) -> Beatmap:
    """
    Produce beatmap.json for a project.

    Without WhisperX: equal-split lyrics.txt across duration.
    Duration sources (first hit): explicit arg → audio/*.wav → brief target → 30s.
    """
    project_dir = Path(project_dir)
    name = project_dir.name

    if duration_sec is None:
        audio_dir = project_dir / "audio"
        wavs = sorted(audio_dir.glob("*.wav")) if audio_dir.is_dir() else []
        for wav in wavs:
            d = _audio_duration_sec(wav)
            if d is not None and d > 0:
                duration_sec = d
                break

    if duration_sec is None:
        brief_path = project_dir / "brief.yaml"
        if brief_path.is_file():
            import yaml

            brief = yaml.safe_load(brief_path.read_text(encoding="utf-8")) or {}
            duration_sec = float(brief.get("target_duration_sec") or DEFAULT_DURATION)
        else:
            duration_sec = DEFAULT_DURATION

    lines = _read_lyrics_lines(project_dir / "lyrics.txt")
    n = len(lines)
    slot = duration_sec / n
    segments = [
        LyricSegment(text=line, t0=round(i * slot, 3), t1=round((i + 1) * slot, 3))
        for i, line in enumerate(lines)
    ]

    beatmap = Beatmap(
        project=name,
        duration_sec=round(duration_sec, 3),
        bpm=DEFAULT_BPM,
        segments=segments,
        source="stub_equal_split",
        meta={"note": "Replace with WhisperX forced alignment when available."},
    )

    out = project_dir / "beatmap.json"
    out.write_text(
        json.dumps(beatmap.model_dump(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return beatmap
