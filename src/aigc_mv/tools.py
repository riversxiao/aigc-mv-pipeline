"""Small shared helpers: ffmpeg lookup, audio I/O, JSON files."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import numpy as np


def ffmpeg_exe() -> str:
    """ffmpeg on PATH, else the static binary shipped by imageio-ffmpeg."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as e:  # pragma: no cover - depends on the machine
        raise RuntimeError(
            "ffmpeg not found. Install ffmpeg or `pip install imageio-ffmpeg`."
        ) from e


def has_ffmpeg() -> bool:
    try:
        ffmpeg_exe()
        return True
    except RuntimeError:
        return False


def run_ffmpeg(args: list[str], quiet: bool = True) -> subprocess.CompletedProcess:
    cmd = [ffmpeg_exe(), "-y", "-hide_banner"]
    if quiet:
        cmd += ["-v", "error"]
    proc = subprocess.run(cmd + args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError("ffmpeg failed:\n" + " ".join(args)[:600] + "\n" + proc.stderr[-2500:])
    return proc


def media_duration(path: Path) -> float:
    """Duration in seconds without ffprobe (parses ffmpeg's banner)."""
    proc = subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-i", str(path)], capture_output=True, text=True
    )
    for line in proc.stderr.splitlines():
        line = line.strip()
        if line.startswith("Duration:"):
            hms = line.split(",")[0].split()[1]
            h, m, s = hms.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise RuntimeError(f"could not read duration of {path}")


def load_audio(path: Path, sr: int = 22050, mono: bool = True) -> tuple[np.ndarray, int]:
    """Decode any audio/video file to float32 via ffmpeg (no soundfile format limits)."""
    ch = "1" if mono else "2"
    proc = subprocess.run(
        [ffmpeg_exe(), "-v", "error", "-i", str(path), "-vn", "-ac", ch, "-ar", str(sr),
         "-f", "f32le", "-"],
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"cannot decode {path}: {proc.stderr.decode(errors='ignore')[-800:]}")
    x = np.frombuffer(proc.stdout, dtype=np.float32).copy()
    if not mono:
        x = x.reshape(-1, 2)
    return x, sr


def save_wav(path: Path, x: np.ndarray, sr: int) -> Path:
    import soundfile as sf

    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), x, sr, subtype="PCM_16")
    return path


def jload(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def jsave(path: Path, data: Any) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(data, "model_dump"):
        data = data.model_dump(mode="json")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def han(s: str) -> str:
    """Only the CJK characters of a string (lyric matching ignores punctuation/spaces)."""
    return "".join(ch for ch in s if "\u4e00" <= ch <= "\u9fff")
