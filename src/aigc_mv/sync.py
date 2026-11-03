"""Measure each take against the audio window it was generated from.

Seedance copies the reference audio into its soundtrack and the mouth follows THAT soundtrack. So the take's
own audio tells us where its lips are: cross-correlate its envelope with the window we sent →
`lag` (how late the take runs), then slide 1 s windows to find where it stops matching (re-sung / drifted).

    song_time = unit.song_t0 + clip_time − lag

Every take gets its own lag (measured −0.4 … +0.8 s in production); never assume a constant.
Motion takes (no vocal) are placed at lag 0. The director's eye still has the final word (`ep pick`).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from pydantic import BaseModel, Field

from aigc_mv.tools import load_audio

FPS = 100  # envelope frames per second


class TakeSync(BaseModel):
    take: str
    lag: float = 0.0
    ncc: float = 0.0
    copy_: bool = Field(False, alias="copy")
    synced: list[tuple[float, float]] = Field(default_factory=list, description="Clip-time spans in sync")
    diverge_at: float | None = None
    duration: float = 0.0

    model_config = {"populate_by_name": True}


class UnitTakes(BaseModel):
    unit: str
    takes: list[TakeSync] = Field(default_factory=list)
    pick: str | None = None
    usable: tuple[float, float] | None = Field(None, description="Clip-time window chosen by the director")
    notes: str = ""


def envelope(x: np.ndarray, sr: int) -> np.ndarray:
    hop = sr // FPS
    n = len(x) // hop
    if n < 2:
        return np.zeros(2)
    fr = x[: n * hop].reshape(n, hop)
    e = np.log1p(50 * np.sqrt((fr**2).mean(1)))
    on = np.maximum(np.diff(e, prepend=e[0]), 0)
    env = 0.5 * e / (e.max() + 1e-9) + on / (on.max() + 1e-9)
    return env - env.mean()


def _ncc(a: np.ndarray, b: np.ndarray) -> float:
    a = a - a.mean()
    b = b - b.mean()
    d = np.sqrt((a**2).sum() * (b**2).sum())
    return float((a * b).sum() / d) if d > 0 else 0.0


def measure(ref_wav: Path, take: Path, max_lag: float = 1.0, win: float = 1.0, thr: float = 0.35) -> TakeSync:
    sr = 16000
    r, _ = load_audio(ref_wav, sr=sr)
    t, _ = load_audio(take, sr=sr)
    er, et = envelope(r, sr), envelope(t, sr)
    L = int(max_lag * FPS)
    best, best_lag = -1.0, 0
    for k in range(-L, L + 1):
        # take[i + k] ~ ref[i]
        if k >= 0:
            a, b = er[: len(et) - k], et[k:]
        else:
            a, b = er[-k:], et[: len(et) + k]
        m = min(len(a), len(b))
        if m < FPS:
            continue
        c = _ncc(a[:m], b[:m])
        if c > best:
            best, best_lag = c, k
    lag = best_lag / FPS
    # sliding check at that lag (clip time)
    w = int(win * FPS)
    hop = w // 4
    spans: list[list[float]] = []
    diverge = None
    active_ref = np.abs(er) > 0.05
    for i in range(0, max(1, len(et) - w), hop):
        j = i - best_lag
        if j < 0 or j + w > len(er):
            continue
        if active_ref[j:j + w].mean() < 0.2:  # silence in the window: neutral
            continue
        c = _ncc(er[j:j + w], et[i:i + w])
        t0, t1 = i / FPS, (i + w) / FPS
        if c >= thr:
            if spans and t0 <= spans[-1][1] + 0.3:
                spans[-1][1] = t1
            else:
                spans.append([t0, t1])
        elif diverge is None and spans:
            diverge = round(t0, 2)
    dur = len(t) / sr
    return TakeSync(take=take.name, lag=round(lag, 3), ncc=round(best, 3), copy=best > 0.2,
                    synced=[(round(a, 2), round(b, 2)) for a, b in spans if b - a >= 0.5],
                    diverge_at=diverge, duration=round(dur, 3))


def takes_dir(project_dir: Path, unit: str) -> Path:
    return Path(project_dir) / "units" / unit / "takes"


def load_unit_takes(project_dir: Path, unit: str) -> UnitTakes:
    p = Path(project_dir) / "units" / unit / "takes.json"
    if p.is_file():
        return UnitTakes.model_validate_json(p.read_text(encoding="utf-8"))
    return UnitTakes(unit=unit)


def save_unit_takes(project_dir: Path, ut: UnitTakes) -> Path:
    p = Path(project_dir) / "units" / ut.unit / "takes.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(ut.model_dump_json(indent=2, by_alias=True) + "\n", encoding="utf-8")
    return p
