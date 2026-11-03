"""Variety-show format (`format: show`): multi-role cast, show sections, per-line beats, show planner + audit."""

from pathlib import Path

import pytest
import yaml
from PIL import Image

from aigc_mv import cinema
from aigc_mv.board import audit, plan, render_sheet
from aigc_mv.episode import Episode, LyricLine, load_episode
from aigc_mv.timing import analyze, beat_layout, line_beats
from aigc_mv.tools import han

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
    assert any(f == "judges.png" and "评委席" in r for f, r in jt.uploads)
    host_u = next(x for x in board.units if x.kind == "sung" and x.singer == "host")
    assert "说：" in video_prompt(ep, board, timing, host_u, chars).text
    for x in board.units:
        ups = video_prompt(ep, board, timing, x, chars).uploads
        faces = [f for f, _ in ups if f.endswith("_sheet.png")]
        assert len(faces) <= 6
        assert all("锁定定妆图" in r for f, r in ups if f.endswith("_sheet.png"))
        assert not any(f.endswith(("_face.png", "_full.png")) for f, _ in ups)


def test_show_sung_prompts_are_short_and_complete(ep, timing, board):
    """Every sung show prompt keeps the audio policy at both ends, every timed half-line of its visible singer,
    one @图片N per upload naming the right person or plate, the identity-only rule once, and stays short."""
    from aigc_mv import plates
    from aigc_mv.packs import SUNG_PROMPT_WARN
    from aigc_mv.prompts import (AUDIO_COPY_CN, ROLE_CN, SHOW_PLATE_RULE_CN, SHOW_SHEET_RULE_CN, characters,
                                 video_prompt)

    chars = characters(ep)
    lines = {ln.idx: ln for ln in timing.lines}
    sung = [u for u in board.units if u.kind == "sung"]
    assert sung
    total_timed = 0
    for u in sung:
        up = video_prompt(ep, board, timing, u, chars)
        t = up.text
        assert t.startswith(AUDIO_COPY_CN) and t.rstrip().endswith(AUDIO_COPY_CN), u.id
        # units of four or more shots (each with its own timing, staging and reaction) may still go over: the
        # remaining fix there is fewer shots per unit, which `ep prompts` keeps warning about
        if len(board.unit_shots(u)) <= 3:
            assert len(t) < SUNG_PROMPT_WARN, (u.id, len(t))
        n_timed = 0
        for s in board.unit_shots(u):
            if not (s.sung and s.lines and s.singer in s.who):
                continue
            a, b = s.t0 - u.song_t0, s.t1 - u.song_t0
            for i in s.lines:
                for ph in lines[i].phrases:
                    p0, p1 = ph.t0 - u.song_t0, ph.t1 - u.song_t0
                    if p1 <= a + 0.05 or p0 >= b - 0.3:
                        continue
                    assert f"{max(p0, 0):.2f}–" in t and f"「{ph.text}」" in t, (u.id, ph.text)
                    n_timed += 1
        total_timed += n_timed  # a unit whose singer is only heard off screen has no timed lines
        refs = t.split("【参考图】", 1)[1].split("\n", 1)[0]
        for i, (f, _) in enumerate(up.uploads, 1):
            assert f"@图片{i}" in t, (u.id, f)
            if f.endswith("_sheet.png"):
                c = ep.cast[f[: -len("_sheet.png")]]
                assert f"@图片{i}是{c.name_cn}（{ROLE_CN[c.role]}）" in refs, (u.id, f)
            elif f in plates.BY_FILE:
                assert f"@图片{i}是场景图（{plates.BY_FILE[f].title_cn}）" in refs, (u.id, f)
        assert f"@图片{len(up.uploads) + 1}" not in t
        if any(f.endswith("_sheet.png") for f, _ in up.uploads):
            assert refs.count(SHOW_SHEET_RULE_CN) == 1
        if any(f in plates.BY_FILE for f, _ in up.uploads):
            assert refs.count(SHOW_PLATE_RULE_CN) == 1
        assert "@音频1" in t and "—" not in t and not cinema.banned_hits(t)
    assert total_timed >= len(sung) // 2


def test_show_refs_plan_and_header(ep, board, tmp_path):
    import shutil

    from aigc_mv.packs import write_refs_doc
    from aigc_mv.prompts import SHEET_TILES, characters, refs_plan

    plan_ = refs_plan(ep, board, characters(ep))
    files = {x["file"] for x in plan_}
    assert {"judges.png", "dj_booth.png", "venue.png", "crowd.png"} <= files
    for k in ep.cast:  # three steps per person: face, five views uploading the face, the assembled sheet
        mine = [x for x in plan_ if x.get("cast") == k]
        assert [x["step"] for x in mine] == [1, 2, 2, 2, 2, 2, 3], k
        assert mine[0]["file"] == f"{k}_face.png"
        step2 = [x for x in mine if x["step"] == 2]
        assert {x["file"] for x in step2} == {f"{k}_{t}.png" for t in ("34", "profile", "half", "expr", "full")}
        for x in step2:
            assert x["uploads"] == [{"file": f"{k}_face.png", "role": x["uploads"][0]["role"]}]
            assert "--oref <定妆正面像链接> --ow 100" in x["en"] and x["cn"].startswith("图1是")
            assert x["optional"] == (x["file"] == f"{k}_expr.png")  # the expression grid is not tiled, so optional
        assert f"{k}_expr.png" not in sheet_tiles(mine) and "可选" in step2[3]["use"]
        sheet = mine[-1]
        assert sheet["file"] == f"{k}_sheet.png" and not sheet["en"] and not sheet["cn"]
        assert sheet["tiles"] == [f"{k}_{t}.png" for t in SHEET_TILES] and "ep sheets" in sheet["use"]
    judge = next(x for x in plan_ if x["file"] == "judge_face.png")
    assert "评委" in judge["use"] and "straight on" in judge["en"]
    assert judge["uploads"] == [] and "--iw" not in judge["en"]  # battle cards have no canon art: text-to-image
    assert cinema.ORIGINAL_FACE_CN in judge["cn"] and cinema.SHOW_LOOK_CN in judge["cn"] and "35mm" not in judge["en"]
    assert "four-panel" not in " ".join(x["en"] for x in plan_) and "四格拼在一张图里" not in " ".join(x["cn"] for x in plan_)
    d = tmp_path / "ep"
    shutil.copytree(FIXTURE, d, ignore=shutil.ignore_patterns("analysis", "board", "units", "edit", "final",
                                                              "audio", "refs", "suno.md"))
    doc = write_refs_doc(d, ep, board).read_text(encoding="utf-8")
    assert "《异人之下》" in doc and "## 上传清单" in doc and "ep sheets" in doc
    assert "第一步" in doc and "第二步" in doc and "第三步" in doc and "—" not in doc
    assert "不发到网上" not in doc and "服务器上" in doc and "即梦本地上传" in doc  # MJ links are hosted: say so
    assert "4 张必做 + 1 张可选" in doc


def sheet_tiles(items: list[dict]) -> list[str]:
    return next(x for x in items if x["step"] == 3)["tiles"]


def test_show_sheets_tile_the_locked_views(ep, tmp_path):
    from PIL import Image

    from aigc_mv.sheets import build_sheets, is_assembled

    from aigc_mv.prompts import SHEET_TILES
    from aigc_mv.sheets import sheet_gaps

    refs = tmp_path / "refs"
    refs.mkdir()
    for t in ("face", "34"):
        Image.new("RGB", (300, 400), (200, 150, 120)).save(refs / f"a_{t}.png")
    res = build_sheets(tmp_path, ep)  # an incomplete set is not passed off as locked
    assert "a" in res.skipped and "a" not in res.written and not (refs / "a_sheet.png").exists()
    assert set(res.missing["a"]) == {"a_profile.png", "a_half.png", "a_full.png"}
    assert "b" not in res.written and "b" in res.missing
    res = build_sheets(tmp_path, ep, partial=True)  # opt-in preview keeps its gaps in the marker
    assert res.written["a"] == ["a_face.png", "a_34.png"]
    assert is_assembled(refs / "a_sheet.png")
    assert sheet_gaps(refs / "a_sheet.png") == ["profile", "half", "full"]
    for t in ("profile", "half", "full"):
        Image.new("RGB", (300, 400 if t != "full" else 600), (90, 90, 90)).save(refs / f"a_{t}.png")
    res = build_sheets(tmp_path, ep)
    assert "a" in res.written and "a" not in res.missing and sheet_gaps(refs / "a_sheet.png") == []
    with Image.open(refs / "a_sheet.png") as im:  # full body left, 2x2 grid right: near 3:2, not 3.6:1 in a row
        assert 1.2 < im.width / im.height < 1.7, im.size
    hand = refs / "b_sheet.png"  # a hand-made sheet is kept unless forced
    Image.new("RGB", (64, 64)).save(hand)
    for t in SHEET_TILES:
        Image.new("RGB", (300, 400)).save(refs / f"b_{t}.png")
    res = build_sheets(tmp_path, ep)
    assert "b" in res.kept and Image.open(hand).width == 64 and sheet_gaps(hand) == []
    res = build_sheets(tmp_path, ep, force=True)
    assert "b" in res.written and Image.open(hand).width > 64


def test_show_partial_sheet_still_flagged_missing(ep, board, timing, tmp_path):
    """A sheet made with --partial must not clear the missing-refs line of the units that upload it."""
    import shutil

    from PIL import Image

    from aigc_mv.packs import write_packs
    from aigc_mv.sheets import build_sheets

    d = tmp_path / "p"
    shutil.copytree(FIXTURE, d, ignore=shutil.ignore_patterns("analysis", "board", "units", "edit", "final",
                                                              "audio", "refs", "suno.md"))
    refs = d / "refs"
    refs.mkdir()
    Image.new("RGB", (300, 400)).save(refs / "a_face.png")
    build_sheets(d, ep, partial=True)
    assert (refs / "a_sheet.png").is_file()
    write_packs(d, ep, board, timing)
    texts = [p.read_text(encoding="utf-8") for p in sorted((d / "units").glob("*/prompt.txt"))]
    with_a = [t for t in texts if "a_sheet" in t.split("【提示词】")[0]]
    assert with_a and all("a_sheet.png（不完整" in t for t in with_a)


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


# --------------------------------------------------------------------------- review fixes (v1)


def _shifted(timing, dt):
    t = timing.model_copy(deep=True)
    for ln in t.lines:
        ln.t0, ln.t1 = round(ln.t0 + dt, 3), round(ln.t1 + dt, 3)
        ln.chars = [round(c + dt, 3) for c in ln.chars]
        for p in ln.phrases:
            p.t0, p.t1 = round(p.t0 + dt, 3), round(p.t1 + dt, 3)
    return t


@pytest.mark.parametrize("dt", [-1.3, 1.3, 2.6])
def test_show_sections_follow_drifting_lines(ep, timing, dt):
    """Lines off the beat layout (ASR on a real take): sections still hold their own lines, audit warns otherwise."""
    from aigc_mv.timing import sections_from_lines

    t = _shifted(timing, dt)
    secs = sections_from_lines(ep, t.lines, t.duration, t.grid)
    assert secs[0].t0 == 0 and abs(secs[-1].t1 - t.duration) < 1e-6
    for a, b in zip(secs, secs[1:]):
        assert a.t1 == b.t0 and b.t0 >= a.t0
    for ln in t.lines:
        assert secs[ln.verse].t0 <= ln.t0 and ln.t1 <= secs[ln.verse].t1 + 0.3, (ln.text, dt)
    stale = t.model_copy(update={"sections": timing.sections})  # layout sections on drifted lines
    res = audit(ep, plan(ep, stale), stale)
    assert any(w.startswith("section:") for w in res.warnings)
    fixed = t.model_copy(update={"sections": secs})
    assert not any(w.startswith("section:") for w in audit(ep, plan(ep, fixed), fixed).warnings)


def test_entrance_cuts_on_the_announced_name(ep, board, timing):
    ent = [s for s in board.shots if s.kind == "entrance"]
    assert [s.staging for s in ent] == ["split_entrance", "cu_team_bg", "cu_team_bg"]
    assert [s.who for s in ent[1:]] == [["a"], ["b"]]  # 霸王 is announced before 沛公
    ln = next(x for x in timing.lines if x.kind == "entrance")
    t_b = ln.chars[len("左边霸王右边")] - 0.08
    assert ent[2].t0 >= t_b - 0.11


def test_entrance_fallback_is_flagged(ep, board, timing):
    """A lyric edit that drops the rapper names from the entrance must not leave the audit silent."""
    assert not any(w.startswith("entrance:") for w in audit(ep, board, timing).warnings)
    t = timing.model_copy(deep=True)
    for ln in t.lines:
        if ln.kind == "entrance":
            ln.text = "嘿" * len(han(ln.text))
    res = audit(ep, plan(ep, t), t)
    hits = [w for w in res.warnings if w.startswith("entrance:")]
    assert len(hits) == 2 and all("falls back" in w for w in hits), hits
    # names still sung, but the CUs land far from them: flagged as off the announcement
    moved = board.model_copy(deep=True)
    for s in moved.shots:
        if s.kind == "entrance" and s.staging == "cu_team_bg":
            s.t0 += 0.5 if s.who == ["b"] else 0
    assert any(w.startswith("entrance:") and "> 0.3 s off" in w for w in audit(ep, moved, timing).warnings)


def test_lower_thirds_stay_inside_their_shot(ep, timing, board, tmp_path):
    from aigc_mv.edit import _show_layers
    from aigc_mv.overlays import Sheet

    layers: list = []
    _show_layers(ep, board, timing, Sheet(854, 480), tmp_path, layers)
    lts = [x for x in layers if x[0].startswith("lt_")]
    assert lts
    for png, t0, t1, _ in lts:
        k = png[3:-4]
        assert any(k in s.who and s.t0 <= t0 and t1 <= s.t1 for s in board.shots), (k, t0, t1)
    spans = sorted((t0, t1) for _, t0, t1, _ in lts)
    for (_, a1), (b0, _) in zip(spans, spans[1:]):
        assert b0 >= a1  # never stacked


def test_previz_labels_sit_above_the_head(ep, board):
    from aigc_mv.previz import FIG, _Plate

    s = next(x for x in board.shots if x.framing == "CU" and x.background)
    p = _Plate(ep, s, (1920, 1080))
    p.figure(s.who[0], 0.5, "CU")
    p.crew(s.background, 0.5, "CU")
    r, hy = FIG["CU"]
    assert p.labels and all(y < hy * 1080 for _, y, _, _, _ in p.labels)
    assert all(y < 0.5 * 1080 for _, y, _, _, _ in p.labels)  # never in the subtitle / name card band


def test_previz_outranks_generic_refs(ep, board, tmp_path):
    from PIL import Image

    from aigc_mv.edit import build_edl

    (tmp_path / "refs").mkdir()
    for f in ["venue.png", "a_sheet.png", "b_sheet.png", f"plate_{board.shots[3].id}.png"]:
        Image.new("RGB", (64, 36)).save(tmp_path / "refs" / f)
    on = build_edl(tmp_path, ep, board, (854, 480), previz=True).entries
    assert [e.source for e in on].count("plate") == 1 and on[3].file == f"refs/plate_{board.shots[3].id}.png"
    assert all(e.source == "previz" for i, e in enumerate(on) if i != 3)
    off = build_edl(tmp_path, ep, board, (854, 480), previz=False).entries
    assert all(e.source == "plate" for e in off)  # without previz the stills still stand in


def test_previz_beat_follows_the_timing(ep, timing, tmp_path):
    from aigc_mv.edit import previz_beat

    p = previz_beat(tmp_path, ep, timing)
    first = p.read_bytes()
    assert previz_beat(tmp_path, ep, timing).read_bytes() == first  # unchanged timing: reused
    moved = _shifted(timing, 0.5)
    assert previz_beat(tmp_path, ep, moved).read_bytes() != first  # re-analyzed: rebuilt


def test_battle_sheet_keeps_its_columns(tmp_path):
    import shutil

    src = Path(__file__).resolve().parents[1] / "projects" / "xiangyu_vs_liubang"
    d = tmp_path / "ep"
    d.mkdir()
    shutil.copy(src / "episode.yaml", d / "episode.yaml")
    e = load_episode(d)
    t = analyze(d, e, mode="grid", bpm=92)
    b = plan(e, t)
    sheet = render_sheet(e, b, t, audit(e, b, t))
    example = (Path(__file__).resolve().parents[1] / "docs" / "examples" / "项羽vs刘邦_分镜表.md").read_text(
        encoding="utf-8")
    header = next(x for x in sheet.splitlines() if x.startswith("| 镜头"))
    assert header == next(x for x in example.splitlines() if x.startswith("| 镜头"))
    assert "调度" not in sheet and "空镜" not in sheet


def test_show_sheet_has_no_em_dash(ep, timing, board):
    assert "—" not in render_sheet(ep, board, timing, audit(ep, board, timing))


# --------------------------------------------------------------------------- the demo episode (罗天大醮有嘻哈 第一期)

DEMO = Path(__file__).resolve().parents[1] / "projects" / "wangye_vs_zhugeqing"
KNOWLEDGE = Path(__file__).resolve().parents[1] / "knowledge" / "characters"


@pytest.fixture(scope="module")
def demo(tmp_path_factory):
    import shutil

    d = tmp_path_factory.mktemp("demo") / "ep"
    d.mkdir()
    shutil.copy(DEMO / "episode.yaml", d / "episode.yaml")
    e = load_episode(d)
    t = analyze(d, e, mode="grid", bpm=e.bpm_hint)
    return e, t, plan(e, t)


def test_demo_cast_and_cards():
    from aigc_mv.schemas import Character

    e = load_episode(DEMO)
    assert e.format == "show" and e.realism == "idol_show" and e.look == "luotian_show"
    assert "AI生成" in e.disclaimer and "仅供娱乐" in e.disclaimer and "同人二创" in e.disclaimer
    assert len(e.cast) == 15
    assert [e.cast[k].character for k in e.rappers()] == ["zhuge_qing", "wang_ye"]
    for k, c in e.cast.items():
        p = KNOWLEDGE / f"{c.character}.yaml"
        assert p.is_file(), p
        card = Character.model_validate(yaml.safe_load(p.read_text(encoding="utf-8")))
        assert card.age and card.age >= 20, (k, card.age)
        assert card.identity_cn and str(card.age) in card.identity_cn
        assert "面部原创" in card.notes and "《异人之下》" in card.notes
        text = " ".join([card.identity, card.identity_short, card.identity_cn, card.wardrobe_cn, card.props_cn])
        assert not cinema.banned_hits(text), (k, cinema.banned_hits(text))
        assert not cinema.banned_hits(c.listen_cn), k


def test_demo_board(demo):
    e, t, b = demo
    assert 200 <= t.duration <= 240
    res = audit(e, b, t)
    assert res.ok, res.errors
    assert 3.0 <= res.stats["mean_shot_s"] <= 3.8
    assert sum(1 for s in b.shots if s.staging == "blackout_spot") == 1
    for ln in t.lines:  # every mention gets a reaction
        v = e.verses[ln.verse]
        for m in e.mentions_of(v, v.lines[ln.line]):
            assert any(s.kind == "react" and m in s.who and s.t0 < ln.t1 and s.t1 > ln.t0 for s in b.shots), ln.text
    # entrance: when the host says a rapper's name, that rapper's CU (with the name card) is on screen
    for k in e.rappers():
        c = e.cast[k]
        ln = next(x for x in t.lines if x.kind == "entrance" and c.name_cn in x.text)
        t_name = ln.chars[len(han(ln.text[:ln.text.find(c.name_cn)]))]
        s = next(x for x in b.shots if x.t0 <= t_name < x.t1)
        assert s.kind == "entrance" and s.who == [k], (k, s.id, s.who)
    on_screen = {w for s in b.shots for w in s.who}
    for k in e.members("judge", "cameo", "host", "dj", "hook"):
        assert k in on_screen, k
    # the loser sings first and shorter, the winner second and longer
    verses = [sec for sec, v in zip(t.sections, e.verses) if v.kind == "verse"]
    whos = [v.who for v in e.verses if v.kind == "verse"]
    assert whos == ["a", "b"]
    la, lb = (s.t1 - s.t0 for s in verses)
    assert lb > 1.3 * la


def test_demo_prompts_are_clean(demo):
    from aigc_mv.prompts import characters, refs_plan, video_prompt

    e, t, b = demo
    chars = characters(e)
    for u in b.units:
        text = video_prompt(e, b, t, u, chars).text
        assert not cinema.banned_hits(text), (u.id, cinema.banned_hits(text))
    for x in refs_plan(e, b, chars):
        assert not cinema.banned_hits(x["cn"] + " " + x["en"]), x["file"]


def test_demo_refs_start_from_canon_art(demo):
    from aigc_mv.prompts import characters, refs_plan

    e, t, b = demo
    plan_ = refs_plan(e, b, characters(e))
    by = {x["file"]: x for x in plan_}
    a = by["a_face.png"]  # canon: image-to-image from the official art, Midjourney image prompt (not --oref)
    assert a["step"] == 1 and a["uploads"][0]["path"].endswith("refs/canon/zhuge_qing.jpg")
    assert a["cn"].startswith("把图1里的动漫角色拍成真人综艺定妆照") and "不照抄画风" in a["cn"]
    assert a["en"].startswith("<原作图链接> ") and "--iw 1.5" in a["en"] and "--oref" not in a["en"]
    assert "bgm.tv/character/61836" in a["canon_url"] and "绿色玉坠" in a["cn"]
    for k in ("menren", "daotong", "zhanglao"):  # originals: text-to-image
        f = by[f"{k}_face.png"]
        assert f["uploads"] == [] and "<原作图链接>" not in f["en"] and "原创角色" in f["cn"]
    canon = [k for k in e.cast if by[f"{k}_face.png"]["uploads"]]
    assert len(canon) == 12
    assert "银色有线话筒" in by["b_half.png"]["cn"] and "银色有线话筒" not in by["tianshi_half.png"]["cn"]
    for x in plan_:
        assert "火影" not in x["cn"] + x["en"] and "—" not in x["cn"] + x["en"], x["file"]


def test_battle_refs_keep_one_text_sheet():
    from aigc_mv.prompts import characters, refs_plan

    src = Path(__file__).resolve().parents[1] / "projects" / "xiangyu_vs_liubang"
    e = load_episode(src)
    t = analyze(src, e, mode="grid", bpm=92)
    plan_ = refs_plan(e, plan(e, t), characters(e))
    people = [x for x in plan_ if x["file"].endswith("_sheet.png")]
    assert [x["file"] for x in people] == [f"{k}_sheet.png" for k in e.cast]
    assert all("a three-quarter view, a profile" in x["en"] and "step" not in x and x["cn"] for x in people)
    assert not any(x["file"].endswith("_face.png") for x in plan_)


# --------------------------------------------------------------------------- arena plates


DARK_STAGINGS = {"blackout_spot", "empty_stage_ws", "head_down_cu", "spot_cu"}


def _env(ups):
    from aigc_mv import plates

    return [f for f, _ in ups if f in plates.BY_FILE]


def test_every_staging_maps_to_a_planned_plate(demo):
    from aigc_mv import plates
    from aigc_mv.prompts import characters, refs_plan

    e, t, b = demo
    assert set(cinema.SHOW_STAGINGS) <= set(plates.STAGING_PLATE)
    files = {x["file"] for x in refs_plan(e, b, characters(e))}
    for s in b.shots:
        assert plates.plate_for(e, s.staging).file in files, (s.id, s.staging)
    by = {x["file"]: x for x in refs_plan(e, b, characters(e)) if x.get("plate")}
    assert set(by) == {p.file for p in plates.PLATES}  # this cast has judges, DJ, hooks and cameos
    for x in by.values():
        assert x["cn"] and x["en"] and x["gpt"] and "--ar 16:9" in x["en"] and "--" not in x["gpt"]
        assert x["shots"], x["file"]
        assert "—" not in x["cn"] + x["en"] + x["gpt"] and "火影" not in x["cn"] + x["en"] + x["gpt"]
        assert not cinema.banned_hits(x["cn"] + " " + x["en"] + " " + x["gpt"]), x["file"]
        if x["crowd"] == "dark":
            assert "empty seats" not in x["en"] and "没有空座位" not in x["cn"]
        else:
            assert "empty seats" in x["en"]
        if x["crowd"] == "full":
            assert "没有空座位" in x["cn"] and "每个人长得都不一样" in x["cn"]
    for k in e.members("cameo"):  # cameos are never baked into a plate: their seats are left empty
        assert plates.cameo_seat_cn(e.cast[k].position_cn) + "留一个空座位" in by["cameo_seats.png"]["cn"]
        assert e.cast[k].name_cn not in by["cameo_seats.png"]["cn"]
    assert by["cameo_seats.png"]["uploads"][0]["file"] == "venue_high.png"
    assert by["venue.png"]["uploads"] == []
    # first frames sit in their environment plate
    for x in refs_plan(e, b, characters(e)):
        if x["file"].startswith("plate_u"):
            assert x["uploads"][0]["file"] == x["env_plate"] and x["cn"].startswith("图1是场景图 ")


def test_unit_uploads_one_sheet_per_person_then_plates(demo):
    from aigc_mv import plates
    from aigc_mv.prompts import MAX_UPLOADS, characters, video_prompt

    e, t, b = demo
    chars = characters(e)
    for u in b.units:
        shots = b.unit_shots(u)
        ups = video_prompt(e, b, t, u, chars).uploads
        files = [f for f, _ in ups]
        env = _env(ups)
        sheets = [f for f in files if f.endswith("_sheet.png")]
        assert len(files) <= MAX_UPLOADS, u.id
        assert len(sheets) == len(set(sheets)), u.id
        assert files == sheets + env, u.id  # people first, then plates
        assert 1 <= len(env) <= plates.MAX_UNIT_PLATES, u.id
        mine = {plates.plate_for(e, s.staging).file for s in shots}
        assert set(env) <= mine, u.id
        stg = {s.staging for s in shots}
        if stg & {"crowd_ws", "high_ws", "mic_to_crowd"}:
            assert {"crowd.png", "venue_high.png", "crowd_reverse.png"} & set(env), u.id
        if stg & DARK_STAGINGS:
            assert "venue_dark.png" in env and not {"crowd.png", "crowd_reverse.png"} & set(env), u.id
        if stg <= DARK_STAGINGS:
            assert env == ["venue_dark.png"], u.id
        if "judge_react" in stg:  # the judge's own plate beats venue.png even when venue has more screen time
            assert "judges.png" in env, u.id
        if stg <= {"dj_booth", "dj_cu"}:
            assert env == ["dj_booth.png"], u.id


def test_cameo_units_upload_sheet_and_seats(demo):
    from aigc_mv import plates
    from aigc_mv.prompts import characters, video_prompt

    e, t, b = demo
    chars = characters(e)
    seen = 0
    for u in b.units:
        for s in b.unit_shots(u):
            if s.staging != "cameo_react":
                continue
            seen += 1
            up = video_prompt(e, b, t, u, chars)
            files = [f for f, _ in up.uploads]
            k = s.who[0]
            assert f"{k}_sheet.png" in files and "cameo_seats.png" in files, u.id
            n = files.index("cameo_seats.png") + 1
            seat = plates.cameo_seats(e)[k]
            assert seat == plates.cameo_seat_cn(e.cast[k].position_cn)  # distinct positions keep their wording
            assert f"{e.cast[k].name_cn}坐在{seat}（@图片{n} 里留空的那个座位）" in up.text, u.id
            assert e.cast[k].position_cn in seat
    assert seen >= 2


def test_crowd_density_and_blackout_in_unit_prompts(demo):
    from aigc_mv.prompts import characters, video_prompt

    e, t, b = demo
    chars = characters(e)
    for u in b.units:
        stg = {s.staging for s in b.unit_shots(u)}
        text = video_prompt(e, b, t, u, chars).text
        assert "【观众】" in text, u.id
        if stg & {"crowd_ws", "high_ws", "mic_to_crowd", "cameo_react"}:
            assert "没有空座位" in text and "不要空看台" in text, u.id
        if stg <= DARK_STAGINGS:
            assert "不要把观众照亮" in text and "不要空看台" not in text, u.id
        for i, (f, _) in enumerate(video_prompt(e, b, t, u, chars).uploads, 1):
            if f.endswith(".png") and not f.endswith("_sheet.png"):
                assert f"背景照 @图片{i}。" in text, (u.id, f)


def test_upload_cap_drops_background_people_first(demo, monkeypatch):
    from aigc_mv import prompts

    e, t, b = demo
    u = next(x for x in b.units if any(s.background for s in b.unit_shots(x))
             and len(prompts._show_people(b.unit_shots(x))[0]) >= 1)
    fg, bg = prompts._show_people(b.unit_shots(u))
    full, _ = prompts.show_unit_uploads(e, b, u)
    n_env = len(_env(full))
    monkeypatch.setattr(prompts, "MAX_UPLOADS", len(fg) + n_env)
    ups, warn = prompts.show_unit_uploads(e, b, u)
    files = [f for f, _ in ups]
    assert files == [f"{w}_sheet.png" for w in fg] + _env(full)
    assert all(f"{w}_sheet.png" not in files for w in bg)
    assert any("background" in w for w in warn)
    monkeypatch.setattr(prompts, "MAX_UPLOADS", len(fg) + 1)
    ups, warn = prompts.show_unit_uploads(e, b, u)
    assert len(ups) == len(fg) + 1 and len(_env(ups)) == 1


def test_plate_cost_is_arithmetic_only(demo, tmp_path, monkeypatch):
    import socket
    import urllib.request

    from aigc_mv import plates
    from aigc_mv.packs import write_refs_doc

    def no_net(*a, **k):
        raise AssertionError("network used")

    monkeypatch.setattr(socket.socket, "connect", no_net)
    monkeypatch.setattr(urllib.request, "urlopen", no_net)
    c = plates.cost_estimate(["a.png", "b.png", "c.png"], candidates=4, per_image=0.06, upper=0.12)
    assert c["images"] == 12 and c["total"] == 0.72 and c["total_upper"] == 1.44
    assert [r["usd"] for r in c["rows"]] == [0.24] * 3 and sum(r["usd"] for r in c["rows"]) == pytest.approx(c["total"])
    led = tmp_path / "ledger.jsonl"
    led.write_text('{"provider": "openrouter", "kind": "image", "real_usd": 0.054984}\n'
                   '{"provider": "openrouter", "kind": "image", "real_usd": 0.059802}\n'
                   '{"provider": "dreamina", "kind": "video", "real_usd": 3.0}\nnot json\n', encoding="utf-8")
    before = led.read_bytes()
    assert plates.ledger_image_usd(led) == [0.054984, 0.059802]
    assert plates.per_image_from_ledger(led) == 0.06 and plates.per_image_from_ledger(tmp_path / "none") == 0.06
    assert led.read_bytes() == before
    e, t, b = demo
    d = tmp_path / "ep"
    d.mkdir()
    doc = write_refs_doc(d, e, b).read_text(encoding="utf-8")
    assert "## 场景图 / 背景板" in doc and "| 合计 | 36 | $2.16 | $4.32 |" in doc and "—" not in doc
    assert "cameo_seats.png" in doc and "venue_dark.png" in doc and "没有调用任何接口" in doc


def test_show_sheet_names_the_plate(demo):
    e, t, b = demo
    md = render_sheet(e, b, t, audit(e, b, t))
    assert "| 调度 | 场景图 |" in md
    s = next(x for x in b.shots if x.staging == "blackout_spot")
    assert next(r for r in md.splitlines() if r.startswith(f"| {s.id} |")).count("| venue_dark |") == 1


def test_role_plate_beats_venue_under_the_cap(demo):
    """A unit with a long stage shot, a judge reaction and a cameo reaction: cameo_seats.png is a must, and the
    judge on screen keeps judges.png ahead of venue.png (which has more screen time)."""
    from types import SimpleNamespace as NS

    from aigc_mv import plates

    e, _, _ = demo
    judge = e.members("judge")[0]
    cameo = e.members("cameo")[0]
    shots = [NS(staging="point_lens", t0=0.0, t1=5.0, who=["a"]),
             NS(staging="judge_react", t0=5.0, t1=6.0, who=[judge]),
             NS(staging="cameo_react", t0=6.0, t1=7.0, who=[cameo])]
    kept, dropped = plates.pick_unit_plates(e, shots)
    assert [p.file for p in kept] == ["cameo_seats.png", "judges.png"]
    assert [p.file for p in dropped] == ["venue.png"]
    # without the judge on screen (an empty-throne insert) screen time decides again
    shots[1] = NS(staging="judge_react", t0=5.0, t1=6.0, who=[])
    assert [p.file for p in plates.pick_unit_plates(e, shots)[0]] == ["cameo_seats.png", "venue.png"]


def test_cost_upper_bound_follows_the_ledger_price(demo, tmp_path):
    from aigc_mv import plates
    from aigc_mv.packs import write_refs_doc

    c = plates.cost_estimate(["a.png", "b.png"], candidates=4, per_image=0.13)
    assert c["upper"] == pytest.approx(0.26) and c["total"] == 1.04 and c["total_upper"] == 2.08
    assert plates.cost_estimate(["a.png"], per_image=0.13, upper=0.12)["upper"] == 0.13  # never below the estimate
    d = tmp_path / "ep"
    d.mkdir()
    (d / "ledger.jsonl").write_text('{"provider": "openrouter", "kind": "image", "real_usd": 0.0712}\n'
                                    '{"provider": "openrouter", "kind": "image", "real_usd": 0.1251}\n',
                                    encoding="utf-8")
    e, _, b = demo
    doc = write_refs_doc(d, e, b).read_text(encoding="utf-8")
    assert "实际每张 $0.071 到 $0.125" in doc and "$0.055" not in doc
    assert "按每张 $0.13 算" in doc and "保守上限按每张 $0.26" in doc
    assert "| 合计 | 36 | $4.68 | $9.36 |" in doc


def test_cameos_sharing_a_position_get_distinct_seats(demo):
    from aigc_mv import plates
    from aigc_mv.prompts import characters, video_prompt

    e0, t, b = demo
    e = e0.model_copy(deep=True)
    k1, k2 = e.members("cameo")[:2]
    e.cast[k2].position_cn = e.cast[k1].position_cn
    seats = plates.cameo_seats(e)
    assert seats[k1] == plates.cameo_seat_cn(e.cast[k1].position_cn) and seats[k1] != seats[k2]
    assert plates._row_of(seats[k1]) == plates._row_of(seats[k2])
    cn = plates.plate_prompts(e, plates.BY_FILE["cameo_seats.png"])["cn"]
    assert f"{seats[k1]}留一个空座位" in cn and f"{seats[k2]}留一个空座位" in cn
    en = plates.plate_prompts(e, plates.BY_FILE["cameo_seats.png"])["en"]
    assert plates._seat_en(seats[k1]) != plates._seat_en(seats[k2]) and plates._seat_en(seats[k2]) in en
    chars = characters(e)
    for u in b.units:
        shots = b.unit_shots(u)
        for s in shots:
            if s.staging == "cameo_react" and s.who[0] in (k1, k2):
                text = video_prompt(e, b, t, u, chars).text
                assert f"{e.cast[s.who[0]].name_cn}坐在{seats[s.who[0]]}" in text, u.id
    # more cameos than seats in one row: refuse instead of stacking them
    for i in range(len(plates.SEATS_CN) + 1):
        e.cast[f"extra{i}"] = e.cast[k1].model_copy()
    with pytest.raises(ValueError, match="no free seat"):
        plates.cameo_seats(e)


def test_shot_plate_uses_locked_venue_plate(ep, timing, board, tmp_path):
    from aigc_mv.previz import shot_plate

    s = next(x for x in board.shots if x.staging == "two_shot")
    drawn = shot_plate(ep, s, (320, 180), timing, refs=tmp_path)  # no plate in refs/: drawn arena
    Image.new("RGB", (1536, 864), (0, 200, 0)).save(tmp_path / "venue.png")
    real = shot_plate(ep, s, (320, 180), timing, refs=tmp_path)
    corner = real.getpixel((310, 170))
    assert corner[1] > 100 and corner[1] > corner[0] and real.size == (320, 180)
    assert drawn.getpixel((310, 170))[1] < 100
