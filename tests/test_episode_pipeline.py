"""End-to-end checks of the episode pipeline on a synthetic song (no models, no network for core steps)."""

import shutil
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from aigc_mv import cinema
from aigc_mv.board import SUNG_MAX, UNIT_MAX, UNIT_MIN, audit, plan
from aigc_mv.episode import load_episode
from aigc_mv.prompts import AUDIO_COPY_CN, characters, refs_plan, suno_sheets, video_prompt
from aigc_mv.sync import measure
from aigc_mv.timing import analyze, beat_grid, interpolate, match_chars
from aigc_mv.tools import has_ffmpeg, jsave
from aigc_mv.windows import write_windows

REPO = Path(__file__).resolve().parents[1]
EXAMPLE = REPO / "projects" / "xiangyu_vs_liubang"
BPM = 92.0

needs_ffmpeg = pytest.mark.skipif(not has_ffmpeg(), reason="ffmpeg not available")


def _synth(ep_dir: Path, timing) -> None:
    sr, dur = 44100, timing.duration
    n = int(dur * sr)
    song, voc = np.zeros(n, np.float32), np.zeros(n, np.float32)
    rng = np.random.default_rng(0)
    for i, b in enumerate(np.arange(0.0, dur, 60 / BPM)):
        a, L = int(b * sr), int(0.08 * sr)
        f = 55 if i % 4 == 0 else 120
        song[a:a + L] += (0.9 if i % 4 == 0 else 0.35) * np.sin(2 * np.pi * f * np.arange(L) / sr)[: n - a] * np.exp(-np.linspace(0, 8, L))[: n - a]
    for ln in timing.lines:
        for c in ln.chars:
            a, L = int(c * sr), int(0.16 * sr)
            voc[a:a + L] += 0.3 * np.sin(2 * np.pi * (220 + 60 * rng.random()) * np.arange(L) / sr) * np.hanning(L)
    (ep_dir / "audio").mkdir(exist_ok=True)
    sf.write(ep_dir / "audio" / "vocals.wav", voc, sr)
    sf.write(ep_dir / "audio" / "instrumental.wav", song, sr)
    sf.write(ep_dir / "audio" / "song.wav", song + voc, sr)


@pytest.fixture()
def ep_dir(tmp_path):
    d = tmp_path / "ep"
    shutil.copytree(EXAMPLE, d)
    return d


def test_episode_loads_and_validates():
    ep = load_episode(EXAMPLE)
    assert {c.side for c in ep.cast.values()} == {"left", "right"}
    assert all(ln.note for _, _, _, ln in ep.all_lines()), "every line carries a source note"


def test_synthetic_board_passes_audit():
    ep = load_episode(EXAMPLE)
    t = analyze(EXAMPLE, ep, mode="grid", bpm=BPM)
    assert len(t.lines) == 16
    b = plan(ep, t)
    res = audit(ep, b, t)
    assert res.ok, res.errors
    # tiling and unit limits
    assert b.shots[0].t0 == 0 and abs(b.shots[-1].t1 - t.duration) < 0.05
    for u in b.units:
        assert UNIT_MIN <= u.duration <= UNIT_MAX
        if u.kind == "sung":
            assert u.duration <= SUNG_MAX
    kinds = {s.kind for s in b.shots}
    assert {"establish", "perform", "react", "cutaway", "crowd", "outro"} <= kinds
    # camera variety: never the same non-locked move twice in a row
    for a, c in zip(b.shots, b.shots[1:]):
        assert not (a.camera == c.camera and a.camera != "locked")


def test_sung_prompt_has_timed_halves_and_policy():
    ep = load_episode(EXAMPLE)
    t = analyze(EXAMPLE, ep, mode="grid", bpm=BPM)
    b = plan(ep, t)
    chars = characters(ep)
    u = next(x for x in b.units if x.kind == "sung")
    up = video_prompt(ep, b, t, u, chars)
    assert up.text.startswith(AUDIO_COPY_CN) and up.text.rstrip().endswith(AUDIO_COPY_CN)
    first = t.lines[b.unit_shots(u)[0].lines[0]]
    assert f"「{first.phrases[0].text}」" in up.text
    assert "秒「" in up.text
    assert chars["a"].identity_cn.strip()[:10] in up.text
    assert not cinema.banned_hits(up.text)


def test_refs_plan_and_suno():
    ep = load_episode(EXAMPLE)
    t = analyze(EXAMPLE, ep, mode="grid", bpm=BPM)
    b = plan(ep, t)
    chars = characters(ep)
    files = {x["file"] for x in refs_plan(ep, b, chars)}
    assert {"a_sheet.png", "b_sheet.png", "venue.png", "crowd.png"} <= files
    assert any(f.startswith("plate_u") for f in files)
    sheet = suno_sheets(ep, chars)
    assert "[Verse 1: Xiang Yu]" in sheet and "Extend" in sheet


def test_pinyin_matching_interpolates():
    sheet = list("力拔山兮气盖世")
    heard = [("力", 1.0), ("把", 1.2), ("山", 1.4), ("气", 1.8), ("盖", 2.0), ("世", 2.2)]
    t = interpolate(match_chars(sheet, heard))
    assert len(t) == len(sheet)
    assert all(b > a for a, b in zip(t, t[1:]))


@needs_ffmpeg
def test_beat_grid_windows_sync(ep_dir):
    ep = load_episode(ep_dir)
    t = analyze(ep_dir, ep, mode="grid", bpm=BPM)
    _synth(ep_dir, t)
    g = beat_grid(ep_dir / "audio" / "song.wav")
    assert abs(g.bpm - BPM) < 0.5
    period = 60 / BPM
    err = [abs(b / period - round(b / period)) * period for b in g.beats[2:40]]
    assert np.median(err) < 0.02
    t = analyze(ep_dir, ep, mode="grid")
    b = plan(ep, t)
    jsave(ep_dir / "analysis" / "timing.json", t)
    jsave(ep_dir / "board" / "board.json", b)
    wavs = write_windows(ep_dir, ep, t, b)
    u = next(x for x in b.units if x.kind == "sung")
    w = ep_dir / "units" / u.id / f"{u.id}_vocal.wav"
    assert w in wavs
    x, sr = sf.read(w)
    assert abs(len(x) / sr - u.duration) < 0.01
    assert np.abs(x[: int(0.25 * sr)]).max() < 1e-3, "lead silence before the first word"
    # a fake take whose soundtrack runs 0.2 s late
    take = ep_dir / "units" / u.id / "late.wav"
    sf.write(take, np.concatenate([np.zeros(int(0.2 * sr)), x])[: len(x)], sr)
    ts = measure(w, take)
    assert ts.copy_ and abs(ts.lag - 0.2) <= 0.02


@needs_ffmpeg
def test_render_animatic_excerpt(ep_dir):
    from PIL import Image

    from aigc_mv.edit import render

    ep = load_episode(ep_dir)
    t = analyze(ep_dir, ep, mode="grid", bpm=BPM)
    b = plan(ep, t)
    (ep_dir / "refs").mkdir(exist_ok=True)
    Image.new("RGB", (640, 360), (90, 60, 40)).save(ep_dir / "refs" / "venue.png")
    out = render(ep_dir, ep, b, t, resolution="480p", test=(0.0, 4.0))
    assert out.is_file() and out.stat().st_size > 10_000
