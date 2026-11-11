"""Tests for `rea-video` benchmark auditing and targeted H3 repair routing (`aigc_mv.rea_audit`)."""

import json
from pathlib import Path

from typer.testing import CliRunner

from aigc_mv.cli import app
from aigc_mv.rea_audit import (
    HUOYING_BENCHMARK,
    audit_breakdown,
    extract_metrics,
    load_rea_breakdown,
    recommend_h3_repair,
    render_rea_audit_md,
)


def _passing_breakdown() -> dict:
    return {
        "source": {"path": "ep03_mv_v6_master.mp4"},
        "summary": {
            "duration": 180.0,
            "shots": 60,
            "production_mix": [
                {"label": "ai_video", "ratio": 0.96},
                {"label": "still_motion", "ratio": 0.02},
                {"label": "code_render", "ratio": 0.02},
            ],
            "transitions": {"cut": 58, "jump": 1},
            "aspects": ["camera", "framing"],
        },
        "aspects": {
            "camera": {"support_shares": {"moving": 0.52, "handheld": 0.45, "fixed": 0.03}},
            "framing": {"shot_sizes": {"CU": 0.34, "MCU": 0.31, "MS": 0.22, "WS": 0.13}},
        },
        "per_clip_audio": {
            "shot_001": {"has_speech": True, "vocal_ratio": 0.72},
            "shot_002": {"has_speech": False, "vocal_ratio": 0.05},
        },
        "shots": [
            {
                "id": "shot_001",
                "index": 1,
                "start": 0.0,
                "end": 3.0,
                "duration": 3.0,
                "base": {"label": "ai_video"},
                "aspects": {"camera": {"measured": {"motion": "moving"}}},
            },
            {
                "id": "shot_060",
                "index": 2,
                "start": 177.0,
                "end": 180.0,
                "duration": 3.0,
                "base": {"label": "code_render"},
                "aspects": {"camera": {"measured": {"motion": "static"}}},
            },
        ],
    }


def _failing_v4_like_breakdown() -> dict:
    return {
        "source": {"path": "ep03_mv_v4_draft.mp4"},
        "summary": {
            "duration": 180.0,
            "shots": 60,
            "production_mix": [
                {"label": "ai_video", "ratio": 0.84},
                {"label": "still_motion", "ratio": 0.14},
                {"label": "avatar", "ratio": 0.02},
            ],
            "transitions": {"cut": 55, "jump": 4},
        },
        "aspects": {
            "camera": {"support_shares": {"moving": 0.48, "handheld": 0.25, "fixed": 0.27}},
            "framing": {"shot_sizes": {"MCU": 0.68, "MS": 0.32}},
        },
        "per_clip_audio": {
            "shot_010": {"has_speech": True, "vocal_ratio": 0.80},
            "shot_021": {"has_speech": False, "vocal_ratio": 0.0},
            "shot_030": {"has_speech": True, "vocal_ratio": 0.65},
        },
        "shots": [
            {
                "id": "shot_010",
                "index": 1,
                "start": 33.0,
                "end": 36.2,
                "duration": 3.2,
                "base": {"label": "ai_video"},
                "aspects": {"camera": {"measured": {"motion": "static"}}},
            },
            {
                "id": "shot_021",
                "index": 2,
                "start": 63.0,
                "end": 66.5,
                "duration": 3.5,
                "base": {"label": "still_motion"},
                "aspects": {"camera": {"measured": {"motion": "planar_zoom_pan"}}},
            },
            {
                "id": "shot_030",
                "index": 3,
                "start": 90.0,
                "end": 93.0,
                "duration": 3.0,
                "transition_in": "jump",
                "base": {"label": "ai_video"},
                "aspects": {"camera": {"measured": {"motion": "handheld"}}},
            },
        ],
    }


def test_audit_passing_v6_profile():
    bd = _passing_breakdown()
    rep = audit_breakdown(bd, HUOYING_BENCHMARK, motion_by_shot={"shot_001": 0.84, "shot_060": 0.01})
    assert rep.passed is True
    assert rep.gaps == []
    assert rep.metrics.still_motion_ratio == 0.02
    assert rep.metrics.moving_camera_ratio == 0.97
    assert rep.metrics.distinct_shot_sizes == 4
    # Final short endcard (`shot_060`) is exempted from redo candidates
    assert rep.redo_candidates == []


def test_audit_failing_profile_emits_targeted_h3_repairs():
    bd = _failing_v4_like_breakdown()
    flows = {"shot_010": 0.009, "shot_021": 0.04, "shot_030": 0.65}
    rep = audit_breakdown(bd, HUOYING_BENCHMARK, motion_by_shot=flows)
    assert rep.passed is False
    assert any("静图推拉" in g for g in rep.gaps)
    assert any("移动+手持" in g for g in rep.gaps)
    assert any("跳切过多" in g for g in rep.gaps)
    assert any("景别变化单一" in g for g in rep.gaps)
    assert any("低动态疑似静帧" in g for g in rep.gaps)

    by_id = {c.shot_id: c for c in rep.redo_candidates}
    # Sung frozen shot -> ref2va_pose 0.72@0.84
    assert by_id["shot_010"].recommended_mode == "ref2va_pose"
    assert by_id["shot_010"].control_strength == 0.72
    assert by_id["shot_010"].end_percent == 0.84

    # Non-vocal still_motion cutaway -> ref2va_depth 0.68@0.82
    assert by_id["shot_021"].recommended_mode == "ref2va_depth"
    assert by_id["shot_021"].control_strength == 0.68
    assert by_id["shot_021"].end_percent == 0.82

    # Clean motion shot with hard jump cut -> editorial trim/cutaway
    assert by_id["shot_030"].recommended_mode == "trim_or_cutaway"

    md = render_rea_audit_md(rep, extract_metrics(_passing_breakdown()))
    assert "NEEDS_REDO" in md
    assert "ref2va_pose" in md
    assert "ref2va_depth" in md
    assert "参考片实测" in md


def test_load_rea_breakdown_accepts_dir_or_file(tmp_path: Path):
    d = tmp_path / "rea_v6"
    d.mkdir()
    bd_file = d / "breakdown.json"
    bd_file.write_text(json.dumps(_passing_breakdown()), encoding="utf-8")
    assert load_rea_breakdown(d)["summary"]["shots"] == 60
    assert load_rea_breakdown(bd_file)["summary"]["shots"] == 60


def test_cli_ep_rea_audit_pass_and_strict_fail(tmp_path: Path):
    runner = CliRunner()
    pass_dir = tmp_path / "pass_rea"
    pass_dir.mkdir()
    (pass_dir / "breakdown.json").write_text(json.dumps(_passing_breakdown()), encoding="utf-8")

    r_ok = runner.invoke(app, ["ep", "rea-audit", str(pass_dir), "--strict"])
    assert r_ok.exit_code == 0, r_ok.output
    assert "rea-audit: PASS" in r_ok.output
    assert (pass_dir / "rea_audit.md").is_file()
    assert (pass_dir / "rea_audit.json").is_file()

    fail_dir = tmp_path / "fail_rea"
    fail_dir.mkdir()
    (fail_dir / "breakdown.json").write_text(json.dumps(_failing_v4_like_breakdown()), encoding="utf-8")
    r_fail = runner.invoke(app, ["ep", "rea-audit", str(fail_dir), "--ref-rea", str(pass_dir), "--strict"])
    assert r_fail.exit_code == 1
    assert "rea-audit: NEEDS_REDO" in r_fail.output


def test_recommend_h3_repair_avatar_forces_ref2va_pose():
    bd = {"per_clip_audio": {}}
    shot = {"id": "shot_007", "index": 7, "start": 12.0, "end": 15.0, "duration": 3.0, "base": {"label": "avatar"}}
    c = recommend_h3_repair(shot, bd, ["rea-video 判定为 avatar"], flow_px=0.05)
    assert c.recommended_mode == "ref2va_pose"
    assert c.control_type == "pose"
