"""Audio windows sent with each generation unit.

Sung units get the lead-vocal stem cut at the unit's song time to EXACTLY the request length
(claudia.gallery's winning method: Suno's own stem, lay the song back over afterwards). Words that belong to
lines outside the unit are gated out so the window never starts or ends inside a word (those get re-sung).
Motion units get the instrumental for rhythm only.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from aigc_mv.board import Board, Unit
from aigc_mv.episode import Episode
from aigc_mv.timing import Timing
from aigc_mv.tools import load_audio, save_wav

SR = 44100
RAMP = 0.015
RELEASE_MAX = 0.40
RMS_TARGET_DB = -16.0
PEAK_DB = -1.0


def _ramp_gate(n: int, keep: list[tuple[int, int]], sr: int) -> np.ndarray:
    g = np.zeros(n, dtype=np.float32)
    r = max(1, int(RAMP * sr))
    for a, b in keep:
        a, b = max(0, a), min(n, b)
        if b <= a:
            continue
        g[a:b] = 1.0
        up = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, min(r, b - a)))
        g[a:a + len(up)] = up
        g[b - len(up):b] = up[::-1]
    return g


def normalise(x: np.ndarray) -> np.ndarray:
    active = x[np.abs(x) > 1e-4]
    if len(active) == 0:
        return x
    rms = float(np.sqrt(np.mean(active**2)))
    y = x * (10 ** (RMS_TARGET_DB / 20) / max(rms, 1e-6))
    peak = float(np.max(np.abs(y)))
    lim = 10 ** (PEAK_DB / 20)
    if peak > lim:
        y = y * (lim / peak)
    return y.astype(np.float32)


def unit_lines(board: Board, u: Unit) -> list[int]:
    return sorted({i for s in board.unit_shots(u) for i in s.lines})


def vocal_window(src: Path, timing: Timing, board: Board, u: Unit) -> np.ndarray:
    x, sr = load_audio(src, sr=SR)
    a = int(round(u.song_t0 * sr))
    n = int(u.duration * sr)
    seg = np.zeros(n, dtype=np.float32)
    part = x[max(0, a): a + n]
    seg[: len(part)] = part
    idx = unit_lines(board, u)
    lines = [ln for ln in timing.lines if ln.idx in idx]
    later = [ln for ln in timing.lines if ln.idx > max(idx)] if idx else []
    keep = []
    for ln in lines:
        k0 = ln.t0 - 0.05 - u.song_t0
        nxt_start = later[0].t0 if later and ln.idx == max(idx) else None
        k1 = ln.t1 + RELEASE_MAX - u.song_t0
        if nxt_start is not None:
            k1 = min(k1, nxt_start - 0.05 - u.song_t0)
        keep.append((int(max(0.0, k0) * sr), int(min(u.duration, k1) * sr)))
    return normalise(seg * _ramp_gate(n, keep, sr))


def plain_window(src: Path, u: Unit) -> np.ndarray:
    x, sr = load_audio(src, sr=SR)
    a = int(round(u.song_t0 * sr))
    n = int(u.duration * sr)
    seg = np.zeros(n, dtype=np.float32)
    part = x[max(0, a): a + n]
    seg[: len(part)] = part
    return normalise(seg * _ramp_gate(n, [(0, n)], sr))


def write_windows(project_dir: Path, ep: Episode, timing: Timing, board: Board) -> list[Path]:
    project_dir = Path(project_dir)
    vocals = project_dir / ep.vocals if ep.vocals else None
    inst = project_dir / ep.instrumental if ep.instrumental else None
    song = project_dir / ep.song
    out = []
    for u in board.units:
        d = project_dir / "units" / u.id
        if u.audio == "vocal":
            src = vocals if vocals and vocals.is_file() else song
            if not src.is_file():
                raise FileNotFoundError(f"no vocal stem or song for {u.id}: {src}")
            out.append(save_wav(d / f"{u.id}_vocal.wav", vocal_window(src, timing, board, u), SR))
        elif u.audio == "instrumental":
            src = inst if inst and inst.is_file() else song
            if not src.is_file():
                continue
            out.append(save_wav(d / f"{u.id}_inst.wav", plain_window(src, u), SR))
    return out
