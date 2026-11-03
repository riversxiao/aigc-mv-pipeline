"""ASR alignment on a real take (no model): synthetic `heard` character lists stand in for faster-whisper."""

import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from aigc_mv import timing as tm
from aigc_mv.episode import load_episode
from aigc_mv.timing import (TimedLine, Timing, align_asr, analyze, clean_words, dp_match, fuzzy_key,
                            match_chars, sections_from_lines, show_sections)
from aigc_mv.timing_report import timing_report, worst_lines
from aigc_mv.tools import han, has_ffmpeg

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "show_mini"
BPM = 92.0


@pytest.fixture(scope="module")
def ep():
    return load_episode(FIXTURE)


@pytest.fixture(scope="module")
def grid_t(ep):
    return analyze(FIXTURE, ep, mode="grid", bpm=BPM)


def _heard(t: Timing, skip=(), only=None, jitter=0.0) -> list[tuple]:
    """What an ideal recogniser would hear: every character of every line at its grid time."""
    out = []
    for ln in t.lines:
        if ln.idx in skip or (only is not None and ln.idx not in only):
            continue
        for c, x in zip(han(ln.text), ln.chars):
            out.append((c, round(x + jitter, 3), round(x + jitter + 0.15, 3)))
    return out


def _idx(t: Timing, text: str) -> int:
    return next(ln.idx for ln in t.lines if ln.text == text)


def test_dp_match_keeps_a_repeated_phrase_in_its_own_line():
    """L1 奇门对奇门 was not sung, L2 was sung differently, L3 repeats L1 and runs into L4. difflib (longest block
    first, ties to the earliest) hangs the only sung 奇门对奇门 on L1, 8 characters before the L4 run it belongs to;
    the DP keeps it on L3, next to its neighbour."""
    sheet = list("奇门对奇门" + "啊啊啊" + "奇门对奇门" + "今晚一起来唱歌吧朋友们")
    heard = list("哦" + "奇门对奇门" + "嗯" + "今晚一起来唱歌吧朋友们")
    old = match_chars(sheet, [(c, float(i)) for i, c in enumerate(heard)])
    assert old[0] is not None and old[8] is None, "difflib cross-matches L1 onto L3's audio (the bug)"
    m = dp_match([fuzzy_key(c) for c in sheet], [fuzzy_key(c) for c in heard])
    assert m[:8] == [None] * 8
    assert m[8:13] == [1, 2, 3, 4, 5] and m[13:] == list(range(7, 18))


def test_fuzzy_pinyin_counts_rap_mergers():
    assert fuzzy_key("青") == fuzzy_key("亲") == fuzzy_key("情")  # qing / qin
    assert fuzzy_key("诸") == fuzzy_key("祝")  # zhu
    assert fuzzy_key("是") == fuzzy_key("四")  # shi / si folded


def test_clean_words_drops_split_hallucinations():
    words = [["今晚", 1.0, 1.4, 0.9], ["字", 9.0, 9.1, 0.2], ["幕", 9.1, 9.2, 0.2], ["志", 9.2, 9.3, 0.2],
             ["愿", 9.3, 9.4, 0.2], ["者", 9.4, 9.5, 0.2], ["啦", 3.0, 3.0, 0.1], ["啦", 3.0, 3.0, 0.1],
             ["啦", 3.0, 3.0, 0.1], ["好", 4.0, 4.2, 0.9]]
    assert [w[0] for w in clean_words(words)] == ["今晚", "好"]


def test_skipped_line_is_flagged_and_stays_in_its_section(ep, grid_t):
    k = _idx(grid_t, "破釜沉舟 我从来不回头望")
    lines = align_asr(ep, grid_t.grid, {"vocals": _heard(grid_t, skip={k})})
    ln = lines[k]
    assert ln.conf == 0 and {"possibly_skipped", "interpolated"} <= set(ln.flags) and ln.source == ""
    assert lines[k - 1].chars[-1] < ln.t0 and ln.chars[-1] < lines[k + 1].t0
    # the later 破釜沉舟 (verse b) keeps its own audio
    vb = _idx(grid_t, "你那句破釜沉舟 我听着都替你心酸")
    assert lines[vb].conf == 1 and abs(lines[vb].t0 - grid_t.lines[vb].t0) < 0.05
    secs = sections_from_lines(ep, lines, grid_t.duration, grid_t.grid, layout=False)
    assert secs[ln.verse].t0 <= ln.t0 and ln.t1 <= secs[ln.verse].t1


def test_line_only_in_fallback_stem_gets_that_source(ep, grid_t):
    hook = {ln.idx for ln in grid_t.lines if ln.kind in ("hook", "interlude")}
    heard = {"vocals": _heard(grid_t, skip=hook), "song": _heard(grid_t, jitter=0.01), "instrumental": []}
    lines = align_asr(ep, grid_t.grid, heard)
    for ln in lines:
        if ln.idx in hook:
            assert ln.source == "song" and ln.conf == 1, ln.text
            assert abs(ln.t0 - grid_t.lines[ln.idx].t0 - 0.01) < 0.05
        else:
            assert ln.source == "vocals" and ln.conf == 1, ln.text
    assert all(not ln.flags for ln in lines), [(ln.text, ln.flags) for ln in lines if ln.flags]


def test_fallback_only_searches_between_the_neighbours(ep, grid_t):
    """The repeated hook line 啦啦啦 谁是第一 is missing from the lead stem; the mix holds only the LAST one. The first
    occurrence must not borrow the last one's audio (it is outside its neighbours' window)."""
    first = _idx(grid_t, "啦啦啦 谁是第一")
    last = max(ln.idx for ln in grid_t.lines if ln.text == "啦啦啦 谁是第一")
    lines = align_asr(ep, grid_t.grid, {"vocals": _heard(grid_t, skip={first, last}),
                                        "song": _heard(grid_t, only={last})})
    assert lines[last].source == "song" and lines[last].conf == 1
    assert lines[first].conf == 0 and "possibly_skipped" in lines[first].flags
    assert lines[first].t0 < lines[first + 1].t0


def test_confidence_and_flags(ep, grid_t):
    k = _idx(grid_t, "你说你力气大 力气能当饭吃吗")
    heard = _heard(grid_t)
    ln = grid_t.lines[k]
    n = len(han(ln.text))
    # the singer swaps two words: 2 characters not heard, replaced by others
    drop = {ln.chars[3], ln.chars[4]}
    heard = [h if h[1] not in drop else ("嗯", h[1], h[2]) for h in heard]
    lines = align_asr(ep, grid_t.grid, {"vocals": heard})
    assert lines[k].conf == pytest.approx((n - 2) / n, abs=1e-3) and "low_conf" not in lines[k].flags
    # most of a line sung differently: low confidence and flagged, the words still sit in their slot
    k2 = _idx(grid_t, "我手下有人 你身边就剩一匹马")
    ln2 = grid_t.lines[k2]
    keep = set(ln2.chars[:4])
    heard2 = [h if h[1] not in set(ln2.chars) - keep else ("嗯", h[1], h[2]) for h in _heard(grid_t)]
    lines = align_asr(ep, grid_t.grid, {"vocals": heard2})
    assert lines[k2].conf == pytest.approx(4 / len(han(ln2.text)), abs=1e-3)
    assert {"low_conf", "sung_differently"} <= set(lines[k2].flags)
    assert abs(lines[k2].t0 - ln2.t0) < 0.05


def test_starts_are_monotonic_with_noise(ep, grid_t):
    heard = _heard(grid_t)
    rng = np.random.default_rng(1)
    noise = [(c, float(x), float(x) + 0.1) for c, x in zip("的你我是了", rng.uniform(0, grid_t.duration, 5))]
    heard = sorted(heard + noise, key=lambda h: h[1])
    lines = align_asr(ep, grid_t.grid, {"vocals": heard})
    t0 = [ln.t0 for ln in lines]
    assert all(b > a for a, b in zip(t0, t0[1:]))
    for ln in lines:
        assert all(b > a for a, b in zip(ln.chars, ln.chars[1:]))
        assert ln.t1 > ln.chars[-1]
    for a, b in zip(lines, lines[1:]):
        assert a.t1 <= b.t0


def test_stray_far_match_is_not_trusted(ep, grid_t):
    """A line whose words were not sung but whose 你 / 的 appear somewhere: no run of 2, so it counts as unheard."""
    k = _idx(grid_t, "老夫子你说 他到底慌不慌")
    ln = grid_t.lines[k]
    heard = [h for h in _heard(grid_t) if h[1] not in set(ln.chars)]
    heard.append(("你", round(ln.chars[3], 3), round(ln.chars[3] + 0.1, 3)))  # one lone 你 at its slot
    lines = align_asr(ep, grid_t.grid, {"vocals": sorted(heard, key=lambda h: h[1])})
    assert lines[k].conf == 0 and "possibly_skipped" in lines[k].flags


def test_sections_from_real_lines_when_song_is_shorter(ep, grid_t):
    """A real take ~20 % faster than the synthetic layout: sections come from the lines, instrumental ones too."""
    f = 0.8
    lines = [ln.model_copy(update={"t0": round(ln.t0 * f, 3), "t1": round(ln.t1 * f, 3),
                                   "chars": [round(c * f, 3) for c in ln.chars]}) for ln in grid_t.lines]
    dur = round(grid_t.duration * f, 3)
    grid = tm.synthetic_grid(dur, BPM)
    with pytest.raises(ValueError):
        tm._beat_time(grid, tm.beat_layout(ep)[-1].end)  # the layout does not fit this song
    secs = show_sections(ep, lines, dur, grid, layout=False)
    assert len(secs) == len(ep.verses) and secs[0].t0 == 0 and secs[-1].t1 == pytest.approx(dur)
    for a, b in zip(secs, secs[1:]):
        assert a.t1 == b.t0 and b.t0 > a.t0
    for ln in lines:
        s = secs[ln.verse]
        assert s.t0 <= ln.t0 and ln.t1 <= s.t1, (ln.text, s)
    # a sung section starts at most one beat before its first line
    for vi, s in enumerate(secs[1:], 1):
        own = [ln for ln in lines if ln.verse == vi]
        if own:
            assert own[0].t0 - s.t0 <= grid.beat + 1e-6
    # cold open (no lines) runs from 0 to just before the first host line
    assert ep.verses[0].kind == "cold_open" and secs[0].t1 <= lines[0].t0
    # grid alignment keeps the layout-based sections (unchanged behaviour)
    assert [s.t0 for s in sections_from_lines(ep, grid_t.lines, grid_t.duration, grid_t.grid)] == \
        [s.t0 for s in grid_t.sections]


def test_onset_snapping():
    fps = 100.0
    db = np.full(500, -60.0)
    db[130:200] = -15.0  # a syllable at 1.30 s after silence
    db[300:400] = -15.0
    db[290:300] = -40.0  # 100 ms dip, then the next syllable at 3.00
    env = (db, fps)
    assert tm._onset(1.10, env, 0.5) == pytest.approx(1.30)  # whisper early, in silence: forward
    assert tm._onset(1.50, env, 0.5) == pytest.approx(1.30)  # whisper late: back to the onset
    assert tm._onset(1.50, env, 1.45) == pytest.approx(1.50)  # never before lo (previous line's syllable)
    assert tm._onset(3.10, env, 2.5) == pytest.approx(3.00)
    # first word stretched back over a pause (heard span 2.50-3.20): starts after the pause
    db2 = db.copy()
    db2[240:260] = -15.0
    assert tm._onset(2.40, (db2, fps), 2.0, end=3.2) == pytest.approx(3.00)
    assert tm._onset(1.30, env, 0.5, end=None) == pytest.approx(1.30)


def test_old_timing_json_still_loads(grid_t):
    d = json.loads(grid_t.model_dump_json())
    for ln in d["lines"]:
        for k in ("conf", "source", "flags", "heard"):
            ln.pop(k)
    t = Timing.model_validate(d)
    assert t.lines[0].conf == 1.0 and t.lines[0].flags == [] and t.lines[0].source == ""
    assert isinstance(t.lines[0], TimedLine)


def test_timing_report_lists_sections_lines_and_checks(ep, grid_t):
    k = _idx(grid_t, "破釜沉舟 我从来不回头望")
    lines = align_asr(ep, grid_t.grid, {"vocals": _heard(grid_t, skip={k})})
    secs = sections_from_lines(ep, lines, grid_t.duration, grid_t.grid, layout=False)
    t = grid_t.model_copy(update={"lines": lines, "sections": secs, "mode": "asr"})
    assert worst_lines(t)[0].idx == k
    md = timing_report(ep, t, files={"vocals": "audio/vocals.wav"}, notes="## 人工核对\n\n- 测试")
    assert "## 段落" in md and "## 逐句时间" in md and "## 建议先听一下核对" in md
    assert "可能没唱" in md and "破釜沉舟 我从来不回头望" in md and md.rstrip().endswith("- 测试")
    assert md.count("\n| ") >= len(lines) + len(secs)
    assert "\u2014" not in md


needs_ffmpeg = pytest.mark.skipif(not has_ffmpeg(), reason="ffmpeg not available")


@needs_ffmpeg
def test_analyze_asr_from_the_cli(tmp_path, monkeypatch, ep, grid_t):
    """`ep analyze --mode asr` end to end with a fake recogniser: per-stem cache, fallback, report."""
    from typer.testing import CliRunner

    import soundfile as sf

    from aigc_mv.cli_ep import app

    d = tmp_path / "show"
    shutil.copytree(FIXTURE, d, ignore=shutil.ignore_patterns("analysis", "board", "units", "edit", "final",
                                                               "audio", "refs"))
    sr = 16000
    n = int(grid_t.duration * sr)
    voc = np.zeros(n, np.float32)
    for ln in grid_t.lines:
        for c in ln.chars:
            a, L = int(c * sr), int(0.16 * sr)
            voc[a:a + L] += 0.3 * np.sin(2 * np.pi * 220 * np.arange(L) / sr)[: n - a] * np.hanning(L)[: n - a]
    beat = np.zeros(n, np.float32)
    for b in np.arange(0.0, grid_t.duration, 60 / BPM):
        a, L = int(b * sr), int(0.06 * sr)
        beat[a:a + L] += 0.5 * np.sin(2 * np.pi * 60 * np.arange(L) / sr)[: n - a]
    (d / "audio").mkdir()
    sf.write(d / "audio" / "vocals.wav", voc, sr)
    sf.write(d / "audio" / "instrumental.wav", beat, sr)
    sf.write(d / "audio" / "song.wav", voc + beat, sr)
    hook = {ln.idx for ln in grid_t.lines if ln.kind == "hook"}
    calls = []

    def fake(audio, prompt=""):
        calls.append(Path(audio).name)
        if Path(audio).name == "instrumental.wav":
            return [["字幕志愿者", 1.0, 2.0, 0.1]]
        hs = _heard(grid_t, skip=hook if Path(audio).name == "vocals.wav" else ())
        return [[c, t0, t1, 0.9] for c, t0, t1 in hs]

    monkeypatch.setattr(tm, "_transcribe_words", fake)
    r = CliRunner().invoke(app, ["analyze", str(d), "--mode", "asr"])
    assert r.exit_code == 0, r.output
    t = Timing.model_validate_json((d / "analysis" / "timing.json").read_text(encoding="utf-8"))
    assert t.mode == "asr" and len(t.lines) == len(grid_t.lines)
    assert {ln.source for ln in t.lines if ln.idx in hook} == {"song"}
    assert all(ln.conf == 1 for ln in t.lines)
    for ln in t.lines:
        s = t.sections[ln.verse]
        assert s.t0 <= ln.t0 and ln.t1 <= s.t1 + 0.3 and "outside_section" not in ln.flags
    assert (d / "analysis" / "timing_report.md").is_file()
    assert sorted(calls) == ["instrumental.wav", "song.wav", "vocals.wav"]
    # second run: served from the per-stem caches, no recogniser call
    r = CliRunner().invoke(app, ["analyze", str(d), "--mode", "asr"])
    assert r.exit_code == 0 and len(calls) == 3
    r = CliRunner().invoke(app, ["timing-report", str(d), "--out", str(tmp_path / "r.md")])
    assert r.exit_code == 0 and "## 逐句时间" in (tmp_path / "r.md").read_text(encoding="utf-8")
