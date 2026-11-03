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
