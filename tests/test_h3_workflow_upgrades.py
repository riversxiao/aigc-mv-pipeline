"""Tests for H3 dual-track routing, 6-layer biomechanical choreography, new canon/lore cards, and Battle-HUD overlays."""

import json
import shutil
from pathlib import Path

import numpy as np

from aigc_mv import cinema
from aigc_mv.board import plan
from aigc_mv.canon import load_character
from aigc_mv.episode import load_episode
from aigc_mv.lore import load_lore, render_lyric_brief
from aigc_mv.overlays import Sheet
from aigc_mv.packs import write_packs
from aigc_mv.timing import analyze

REPO = Path(__file__).resolve().parents[1]
KNOWLEDGE = REPO / "knowledge"
SHOW_MINI = Path(__file__).resolve().parent / "fixtures" / "show_mini"


def test_ep03_character_cards_clean_and_accurate():
    expected_bangumi = {
        "lu_jin": [103755],
        "lu_linglong": [42214],
        "li_muxuan": [],
        "zuo_ruotong": [],
    }
    for cid, bgm_ids in expected_bangumi.items():
        c = load_character(cid, KNOWLEDGE)
        assert [r.id for r in c.canon_refs] == bgm_ids, cid
        blob = " ".join(
            [
                c.identity,
                c.identity_short,
                c.identity_cn,
                c.wardrobe_default,
                c.wardrobe_cn,
                c.props_cn,
                c.signature_cn,
                c.signature_en,
                c.canon_look_cn,
            ]
        )
        assert not cinema.banned_hits(blob), (cid, cinema.banned_hits(blob))
        assert "\u2014" not in blob + c.notes, cid
        assert "young" not in (c.identity + " " + c.identity_short).lower(), cid
        assert c.forbidden, cid

    ll = load_character("lu_linglong", KNOWLEDGE)
    assert "粉" in ll.identity_cn and "鹤氅" in ll.wardrobe_cn
    assert any("black hair" in f.lower() for f in ll.forbidden)
    assert "黑发" in ll.notes

    lmx = load_character("li_muxuan", KNOWLEDGE)
    assert "倒转八方" in lmx.props_cn or "破" in lmx.wardrobe_cn

    zrt = load_character("zuo_ruotong", KNOWLEDGE)
    assert "白" in zrt.wardrobe_cn and "三一门" in (zrt.notes + zrt.signature_cn)


def test_ep03_lore_cards_load_and_render_brief():
    for lid, keyword in (("nisheng_sanchong", "逆生三重"), ("tongtianlu", "通天箓")):
        lore = load_lore(lid, KNOWLEDGE)
        assert keyword in lore.classic_title
        assert lore.lyric_seeds and lore.scene_beats
        assert any("政治" in a for a in lore.avoid)
        brief = render_lyric_brief(lid, KNOWLEDGE)
        assert keyword in brief
        assert not cinema.banned_hits(" ".join(lore.lyric_seeds + lore.scene_beats))


def test_select_h3_route_and_biomech_rotation():
    r_sung = cinema.select_h3_route("sung", ["rapper_solo"])
    assert r_sung.mode == "ref2va_pose"
    assert r_sung.control_type == "pose_no_face"
    assert r_sung.control_strength == 0.72
    assert r_sung.end_percent == 0.84
    assert r_sung.lock_guide_audio is True

    r_motion = cinema.select_h3_route("motion", ["instrument_stage"])
    assert r_motion.mode == "ref2va_depth"
    assert r_motion.control_type == "depth"
    assert r_motion.control_strength == 0.68
    assert r_motion.end_percent == 0.82
    assert r_motion.lock_guide_audio is False

    r_morph = cinema.select_h3_route("motion", ["morph_transition"])
    assert r_morph.mode == "fl2va_morph"
    assert r_morph.control_type == "dual_keyframe"

    # Consecutive gesture phases rotate deterministically so free hands do not freeze
    assert cinema.gesture_phase_cn("mid", 0) != cinema.gesture_phase_cn("mid", 1)
    assert not cinema.banned_hits(cinema.BIOMECH_SUNG_CN)
    for stg_id in ("barrier_interact", "instrument_stage", "morph_transition"):
        assert stg_id in cinema.SHOW_STAGINGS
        stg = cinema.SHOW_STAGINGS[stg_id]
        assert not cinema.banned_hits(stg.cn + " " + stg.en)


def test_write_packs_emits_h3_routing_and_biomech_prompt(tmp_path: Path):
    ep_dir = tmp_path / "ep"
    ep_dir.mkdir()
    shutil.copy(SHOW_MINI / "episode.yaml", ep_dir / "episode.yaml")
    ep = load_episode(ep_dir)
    timing = analyze(ep_dir, ep, mode="grid", bpm=92.0)
    board = plan(ep, timing)

    summary = write_packs(ep_dir, ep, board, timing, KNOWLEDGE)
    assert summary
    sung_units = [s for s in summary if s["kind"] == "sung"]
    motion_units = [s for s in summary if s["kind"] == "motion"]
    assert sung_units and motion_units
    assert all(s["h3_mode"] == "ref2va_pose" for s in sung_units)
    assert any(s["h3_mode"] == "ref2va_depth" for s in motion_units)

    u_sung = sung_units[0]["unit"]
    req = json.loads((ep_dir / "units" / u_sung / "request.json").read_text(encoding="utf-8"))
    assert req["h3_routing"]["mode"] == "ref2va_pose"
    assert req["h3_routing"]["control_strength"] == 0.72
    ptxt = (ep_dir / "units" / u_sung / "prompt.txt").read_text(encoding="utf-8")
    assert "【H3路由】" in ptxt
    assert "【肢体动态】" in ptxt
    assert not cinema.banned_hits(ptxt)


def test_battle_hud_overlays_and_karaoke_wipe():
    sh = Sheet(640, 360, style="battle_hud")
    im_static = sh.lyric("三重修在心里面 白炁冲霄", note="《一人之下》三一门逆生三重", seed=7)
    assert im_static.mode == "RGBA" and im_static.size == (640, 360)
    assert im_static.getbbox() is not None

    im_early = sh.lyric_karaoke("三重修在心里面 白炁冲霄", progress=0.10, singer="陆玲珑", note="三一门")
    im_late = sh.lyric_karaoke("三重修在心里面 白炁冲霄", progress=0.85, singer="陆玲珑", note="三一门")
    assert im_early.getbbox() is not None and im_late.getbbox() is not None
    # Progressive gold wipe + 0.85 punchword pop produces distinct pixel values across progress
    diff = np.abs(np.asarray(im_late, dtype=np.int16) - np.asarray(im_early, dtype=np.int16)).sum()
    assert diff > 1000

    badge = sh.seal_badge("陆瑾", faction="三一门", right=False)
    assert badge.mode == "RGBA" and badge.getbbox() is not None
