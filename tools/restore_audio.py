#!/usr/bin/env python3
"""Rejoin projects/wangye_vs_zhugeqing/audio_flac/*.flac.partNN and decode to audio/{song,vocals,instrumental}.wav.

Run from the code repo root (inside its .venv), after copying the package's projects/ folder in:
    python tools/restore_audio.py projects/wangye_vs_zhugeqing
Decodes to 48 kHz stereo 16-bit PCM, bit-identical to the originals. Verifies the joined FLAC sha256 first.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

from aigc_mv.tools import ffmpeg_exe

ep = Path(sys.argv[1] if len(sys.argv) > 1 else "projects/wangye_vs_zhugeqing")
src, dst = ep / "audio_flac", ep / "audio"
dst.mkdir(exist_ok=True)
want = dict(line.split()[::-1] for line in (src / "whole_flac.sha256").read_text().splitlines() if line.strip())
for name in ("song", "vocals", "instrumental"):
    parts = sorted(src.glob(f"{name}.flac.part*"))
    if not parts:
        sys.exit(f"missing parts for {name} in {src}")
    joined = src / f"{name}.flac"
    with joined.open("wb") as f:
        for p in parts:
            f.write(p.read_bytes())
    got = hashlib.sha256(joined.read_bytes()).hexdigest()
    if got != want[f"{name}.flac"]:
        sys.exit(f"{name}.flac sha256 mismatch: {got}")
    subprocess.run([ffmpeg_exe(), "-v", "error", "-y", "-i", str(joined), "-ar", "48000", "-ac", "2",
                    "-c:a", "pcm_s16le", str(dst / f"{name}.wav")], check=True)
    joined.unlink()
    print("ok", dst / f"{name}.wav")
