"""Variety-show format (`format: show`): multi-role cast, show sections, per-line beats, show planner + audit."""

from pathlib import Path

import pytest
import yaml

from aigc_mv import cinema
from aigc_mv.board import audit, plan, render_sheet
from aigc_mv.episode import Episode, LyricLine, load_episode
from aigc_mv.timing import analyze, beat_layout, line_beats

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "show_mini"
BPM = 92.0


@pytest.fixture(scope="module")
def ep():
    return load_episode(FIXTURE)


@pytest.fixture(scope="module")
def timing(ep):
    return analyze(FIXTURE, ep, mode="grid", bpm=BPM)


@pytest.fixture(scope="module")
def board(ep, timing):
    return plan(ep, timing)


def _raw():
    return yaml.safe_load((FIXTURE / "episode.yaml").read_text(encoding="utf-8"))


def test_show_loads_and_validates(ep):
    assert ep.format == "show"
    assert ep.rappers() == ["a", "b"]
    assert ep.members("judge") == ["judge"]
    assert ep.team("a") == ["ta"] and ep.team("b") == ["tb"]
    assert ep.other("a") == "b" and ep.other("judge") == "a"
    kinds = [v.kind for v in ep.verses]
    assert kinds[0] == "cold_open" and kinds[-1] == "outro" and "reveal" in kinds
    host = ep.verses[1]
    assert ep.singer_of(host, host.lines[1]) == "dj"
    va = ep.verses[5]
    assert ep.mentions_of(va, va.lines[2]) == ["judge"]
    assert ep.mentions_of(va, va.lines[0]) == []  # the rival / the singer never count as mentions
    vb = ep.verses[7]
    assert ep.mentions_of(vb, vb.lines[2]) == ["cameo"]


def test_show_rejects_bad_casts():
    d = _raw()
    d["cast"]["x"] = dict(d["cast"]["a"], name_cn="第三人", side="right")
    with pytest.raises(ValueError, match="exactly two rappers"):
        Episode.model_validate(d)
    d = _raw()
    d["cast"]["b"]["side"] = "left"
    with pytest.raises(ValueError, match="different sides"):
        Episode.model_validate(d)
    d = _raw()
    d["verses"][5]["who"] = "judge"
    with pytest.raises(ValueError, match="sung by a rapper"):
        Episode.model_validate(d)
    d = _raw()
    d["verses"][5]["lines"][0]["mentions"] = ["nobody"]
    with pytest.raises(ValueError, match="mentions"):
        Episode.model_validate(d)


def test_auto_line_beats_and_pause(ep, timing):
    assert line_beats(LyricLine(text="拜托！")) == 2
    assert line_beats(LyricLine(text="一二三四五六七八九十一二三四五六七八九十")) == 8
    assert line_beats(LyricLine(text="我力拔山兮 气盖世无双")) == 4
    assert line_beats(LyricLine(text="逃", beats=3)) == 3
    lay = beat_layout(ep)
    reveal = lay[8]
    (p1, b1), (p2, _) = reveal.lines[1], reveal.lines[2]
    assert p2 - (p1 + b1) == 4  # pause_beats: 4
    beat = 60 / BPM
    short = next(ln for ln in timing.lines if ln.text == "拜托！")
    nxt = timing.lines[short.idx + 1]
    assert abs((nxt.t0 - short.t0) - 2 * beat) < 0.01
    last_two = [ln for ln in timing.lines if ln.verse == 8]
    gap = last_two[2].t0 - last_two[1].t0
    assert abs(gap - (line_beats(ep.verses[8].lines[1]) + 4) * beat) < 0.01


def test_sections_tile_with_instrumental_parts(ep, timing):
    secs = timing.sections
    assert [s.name for s in secs][:2] == ["s01_cold_open", "s02_host"]
    assert len(secs) == len(ep.verses)
    assert secs[0].t0 == 0 and abs(secs[-1].t1 - timing.duration) < 1e-6
    for a, b in zip(secs, secs[1:]):
        assert a.t1 == b.t0 and b.t1 > b.t0
    with_lines = {ln.verse for ln in timing.lines}
    assert 0 not in with_lines  # the cold open is instrumental
    assert {s.kind for s in secs} >= {"cold_open", "host", "entrance", "faceoff", "hook", "verse", "interlude",
                                      "reveal", "outro"}
    for ln in timing.lines:
        sec = secs[ln.verse]
        assert sec.t0 <= ln.t0 and ln.t1 <= sec.t1 + 1e-6
        assert ln.kind == sec.kind


def test_plan_show_tiles_and_passes_audit(ep, timing, board):
    shots = board.shots
    assert board.grammar == "show"
    assert shots[0].t0 == 0 and abs(shots[-1].t1 - timing.duration) < 1e-6
    for a, b in zip(shots, shots[1:]):
        assert abs(a.t1 - b.t0) < 1e-6
    res = audit(ep, board, timing)
    assert res.ok, res.errors
    for s in shots:
        if s.sung:
            assert s.dur >= 0.8 - 1e-6, s.id
        assert s.staging in cinema.SHOW_STAGINGS
        assert s.location == "venue"
    assert {"host", "hook", "entrance", "blackout", "react", "perform"} <= {s.kind for s in shots}
    sheet = render_sheet(ep, board, timing, res)
    assert "| 调度 |" in sheet and "（身后：" in sheet


def test_every_mention_cuts_to_that_member(ep, timing, board):
    n = 0
    for ln in timing.lines:
        v = ep.verses[ln.verse]
        for m in ep.mentions_of(v, v.lines[ln.line]):
            n += 1
            assert any(s.kind == "react" and m in s.who and s.t0 < ln.t1 and s.t1 > ln.t0 for s in board.shots), \
                (ln.text, m)
    assert n >= 2


def test_show_grammar_rules(ep, timing, board):
    shots = board.shots
    assert sum(1 for s in shots if s.staging == "blackout_spot") == 1
    mean = sum(s.dur for s in shots) / len(shots)
    assert 2.5 <= mean <= 4.5, mean
    calm = sum(1 for s in shots if s.camera in cinema.CALM_MOVES) / len(shots)
    assert calm >= 0.7, calm
    perf = [s for s in shots if s.kind == "perform" and s.singer in ep.rappers()
            and s.framing in ("CU", "MCU", "MS", "OTS") and s.staging != "spot_cu"]
    assert perf and all(s.background == ep.team(s.singer) for s in perf)
    # each rapper verse has a rival reaction and a judge reaction
    for sec in timing.sections:
        if sec.kind != "verse":
            continue
        rival = ep.other(sec.who)
        inside = [s for s in shots if s.section == sec.name and s.kind == "react"]
        assert any(rival in s.who for s in inside), sec.name
        assert any(ep.cast[w].role == "judge" for s in inside for w in s.who), sec.name
    for sid, st in cinema.SHOW_STAGINGS.items():
        assert sum(1 for s in shots if s.staging == sid) <= st.max_per_film
    assert sum(1 for s in shots if s.camera == "snap_zoom") <= 3


# --------------------------------------------------------------------------- downstream stages (FEAT-003)


def test_idol_realism_and_luotian_look_are_clean():
    for text in (cinema.realism_cn("idol_show"), cinema.realism_cn("idol_show", sung=True),
                 cinema.realism_en("idol_show"), cinema.negative_en("idol_show"), cinema.ORIGINAL_FACE_CN,
                 cinema.LOOKS["luotian_show"].cn, cinema.LOOKS["luotian_show"].en):
        assert not cinema.banned_hits(text), (text, cinema.banned_hits(text))
    assert cinema.ORIGINAL_FACE_CN in cinema.realism_cn("idol_show")
    assert cinema.realism_cn("gritty") == cinema.REALISM_CN
    assert cinema.negative_en("gritty") == cinema.NO_EN


def test_show_sung_prompt(ep, timing, board):
    from aigc_mv.prompts import AUDIO_COPY_CN, characters, sides_cn, video_prompt

    chars = characters(ep)
    u = next(x for x in board.units if x.kind == "sung" and x.singer == "a"
             and any(s.background for s in board.unit_shots(x)))
    up = video_prompt(ep, board, timing, u, chars)
    t = up.text
    assert t.startswith(AUDIO_COPY_CN) and t.rstrip().endswith(AUDIO_COPY_CN)
    s0 = board.unit_shots(u)[0]
    assert cinema.SHOW_STAGINGS[s0.staging].cn in t
    assert "范增站在项羽身后，虚化在背景里，不抢画面" in t
    assert sides_cn(ep) in t
    assert "秒「" in t
    assert cinema.realism_cn("idol_show", sung=True) in t
    assert ep.show_name + "现场" in t and "说唱对决里正面开火" not in t
    assert not cinema.banned_hits(t)
    # judge reaction by seat, spoken host lines
    judge_u = next(x for x in board.units if any(s.staging == "judge_react" for s in board.unit_shots(x)))
    jt = video_prompt(ep, board, timing, judge_u, chars)
    assert "老夫子坐在评委席中间的王座，" in jt.text
    assert ("judges.png", "是评委席（三张王座）的样子") in jt.uploads
    host_u = next(x for x in board.units if x.kind == "sung" and x.singer == "host")
    assert "说：" in video_prompt(ep, board, timing, host_u, chars).text
    for x in board.units:
        faces = [f for f, _ in video_prompt(ep, board, timing, x, chars).uploads if f.endswith("_sheet.png")]
        assert len(faces) <= 6


def test_show_refs_plan_and_header(ep, board, tmp_path):
    import shutil

    from aigc_mv.packs import write_refs_doc
    from aigc_mv.prompts import characters, refs_plan

    plan_ = refs_plan(ep, board, characters(ep))
    files = {x["file"] for x in plan_}
    assert {f"{k}_sheet.png" for k in ep.cast} <= files
    assert {"judges.png", "dj_booth.png", "venue.png", "crowd.png"} <= files
    judge = next(x for x in plan_ if x["file"] == "judge_sheet.png")
    assert "评委" in judge["use"] and "straight on" in judge["en"]
    assert cinema.ORIGINAL_FACE_CN in judge["cn"] and "35mm" not in judge["en"]
    d = tmp_path / "ep"
    shutil.copytree(FIXTURE, d, ignore=shutil.ignore_patterns("analysis", "board", "units", "edit", "final",
                                                              "audio", "refs", "suno.md"))
    doc = write_refs_doc(d, ep, board).read_text(encoding="utf-8")
    assert "《异人之下》" in doc


def test_show_suno_passes(ep):
    from aigc_mv.prompts import characters, suno_passes, suno_sheets

    passes = suno_passes(ep)
    assert len(passes) == 3
    sheet = suno_sheets(ep, characters(ep))
    assert sheet.count("Styles:") == len(passes)
    assert "[Chorus: 唱曲人]" in sheet and "[Spoken Word: 说书人]" in sheet
    assert "[Verse: 项羽]" in sheet and "[Break: silence]" in sheet and "[Interlude" in sheet
    assert "[Outro" in sheet and sheet.count("Extend：") == 2 and "TTS" in sheet


def test_synth_beat(timing, tmp_path):
    import numpy as np
    import soundfile as sf

    from aigc_mv.previz import synth_beat

    p = synth_beat(timing, tmp_path / "beat.wav")
    x, sr = sf.read(p)
    assert sr == 44100 and x.ndim == 2 and x.shape[1] == 2
    assert abs(len(x) / sr - timing.duration) <= 0.05
    mono = np.abs(x).mean(1)
    beat = 60 / timing.grid.bpm
    w = int(0.04 * sr)

    def energy(ts):
        return float(np.mean([mono[int(t * sr): int(t * sr) + w].mean() for t in ts if t * sr + w < len(mono)]))

    on = energy(timing.grid.beats[:64])
    off = energy([b + beat * 0.3 for b in timing.grid.beats[:64]])
    assert on > 1.5 * off, (on, off)


def test_shot_plates_for_every_staging(ep, timing, board):
    from aigc_mv.previz import shot_plate

    seen = {}
    for s in board.shots:
        seen.setdefault(s.staging, s)
    assert len(seen) >= 15
    for s in seen.values():
        im = shot_plate(ep, s, (320, 180), timing)
        assert im.size == (320, 180) and im.mode == "RGB"


needs_ffmpeg = pytest.mark.skipif(not __import__("aigc_mv.tools", fromlist=["has_ffmpeg"]).has_ffmpeg(),
                                  reason="ffmpeg not available")


@needs_ffmpeg
def test_show_previz_render_excerpt(tmp_path):
    import json
    import shutil
    import subprocess

    from aigc_mv.edit import render
    from aigc_mv.tools import ffmpeg_exe

    d = tmp_path / "ep"
    shutil.copytree(FIXTURE, d, ignore=shutil.ignore_patterns("analysis", "board", "units", "edit", "final",
                                                              "audio", "refs", "suno.md"))
    e = load_episode(d)
    t = analyze(d, e, mode="grid", bpm=BPM)
    b = plan(e, t)
    out = render(d, e, b, t, resolution="480p", test=(0.0, 8.0))
    assert out.is_file() and out.stat().st_size > 10_000
    assert (d / "audio" / "previz_beat.wav").is_file()
    assert not (d / "refs").exists() or not any((d / "refs").glob("*.png"))
    edl = json.loads((d / "edit" / "edl.json").read_text(encoding="utf-8"))
    assert any(x["source"] == "previz" for x in edl["entries"])
    probe = subprocess.run([ffmpeg_exe(), "-i", str(out)], capture_output=True, text=True).stderr
    assert "Audio:" in probe
