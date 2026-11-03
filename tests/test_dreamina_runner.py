"""Dreamina runner + bundle: command construction, model selection, credit gates, resume. No network, no real CLI."""

from __future__ import annotations

import json
import re
import wave
import zipfile
from pathlib import Path

import pytest

from aigc_mv import dreamina_runner as dr
from aigc_mv.dreamina_bundle import build_bundle
from fake_dreamina import SEEDANCE_1_FAST, SEEDANCE_2, FakeDreamina

PROMPT_SUNG = ("【音频】视频的声音就是 @音频1 本身。\n\n【参考图】@图片1是诸葛青（选手），@图片2是王也（选手），"
               "@图片3是张楚岚（队友）：只用来认脸。@图片4是场景图（主舞台）：只用来对齐场景。\n\n"
               "【镜头1】@图片1 在 @图片4 的舞台上唱，@图片2 听，@图片3 鼓掌。@音频1 原样保留。")
PROMPT_MOTION = "【音频】@音频1 只是节奏参考。\n\n【参考图】@图片1是场景图（场馆高位全景）：只用来对齐场景。\n\n【镜头1】@图片1 全景推近。"


def _wav(p: Path, secs: float = 1.0) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(b"\x00\x00" * int(8000 * secs))


def _png(p: Path, tag: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + tag.encode())


def make_bundle(root: Path) -> Path:
    for n in ("a_sheet", "b_sheet", "chulan_sheet", "venue", "venue_high"):
        _png(root / "images" / f"{n}.png", n)
    reqs = {
        "u01": {"unit": "u01", "kind": "sung", "duration": 7, "resolution": "720p", "aspect_ratio": "16:9",
                "images": ["images/a_sheet.png", "images/b_sheet.png", "images/chulan_sheet.png", "images/venue.png"],
                "audio": "units/u01/u01_vocal.wav", "first_frame": None, "prompt": PROMPT_SUNG},
        "u02": {"unit": "u02", "kind": "motion", "duration": 5, "resolution": "720p", "aspect_ratio": "16:9",
                "images": ["images/venue_high.png"], "audio": "units/u02/u02_inst.wav", "first_frame": None,
                "prompt": PROMPT_MOTION},
    }
    for u, r in reqs.items():
        d = root / "units" / u
        d.mkdir(parents=True)
        (d / "request.json").write_text(json.dumps(r, ensure_ascii=False), encoding="utf-8")
        _wav(root / r["audio"], r["duration"])
    (root / "manifest.json").write_text(json.dumps({"episode": "ep_test", "take": 1, "units": ["u01", "u02"]}),
                                        encoding="utf-8")
    return root


def run(root: Path, fake: FakeDreamina, *argv: str):
    args = dr.build_parser().parse_args(["--interval", "0"] + list(argv))
    out = []
    r = dr.Runner(root, args, dr.Cli("dreamina-canvas", dry_run=args.dry_run, runner=fake), out=out.append)
    r.cli.log = r.log
    code = r.run()
    return code, out, r


def calls(fake: FakeDreamina, *prefix: str) -> list:
    return [c for c in fake.s["log"] if c[:len(prefix)] == list(prefix)]


# ---------------------------------------------------------------- identities, selection, planning

def test_stable_ids_are_canonical_and_deterministic():
    ids = dr.unit_ids("p", "u01", 1)
    assert ids == dr.unit_ids("p", "u01", 1)
    assert ids != dr.unit_ids("p", "u01", 2)
    assert re.fullmatch(r"node_[0-9a-hjkmnp-tv-z]{10}", ids["node_id"])
    for k in ("update_id", "submit_id"):
        assert re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", ids[k])


def test_choose_model_prefers_seedance_multimodal_with_image_and_audio():
    spec = dr.choose_model([SEEDANCE_1_FAST, SEEDANCE_2, {"model": "kling_2", "modes": SEEDANCE_2["modes"]}])
    assert spec["model"] == "seedance_2_0" and spec["mode"] == "m2v"
    assert spec["image_audio_together"] and spec["image_max"] == 9 and spec["audio_max"] == 3 and spec["total_max"] == 12
    assert spec["resolutions"] == ["480P", "720P", "1080P"] and "16:9" in spec["ratios"]
    assert spec["first_frame_mode"] and "seedance_1_0_fast:first_last_frame" in spec["alternatives"]


def test_exclusive_image_audio_falls_back():
    excl = json.loads(json.dumps(SEEDANCE_2))
    excl["modes"][0]["references"]["mutuallyExclusiveTypes"] = ["image", "audio"]
    spec = dr.choose_model([excl])
    assert spec["mode"] == "m2v" and not spec["image_audio_together"]
    sung = dr.plan_unit({"kind": "sung", "duration": 7, "images": ["images/a_sheet.png", "images/venue.png"],
                         "audio": "x.wav", "prompt": PROMPT_SUNG}, spec)
    assert sung["mode"] == "first_last_frame" and not sung["use_audio"] and sung["first_frame"] == "images/venue.png"
    assert any("口型" in n for n in sung["notes"])
    motion = dr.plan_unit({"kind": "motion", "duration": 5, "images": ["images/venue_high.png"], "audio": "y.wav",
                           "prompt": PROMPT_MOTION}, spec)
    assert motion["mode"] == "m2v" and not motion["use_audio"] and motion["keep"] == [1]


def test_too_many_refs_drop_plates_first_and_keep_singer():
    spec = dict(dr.choose_model([SEEDANCE_2]), image_max=4, total_max=5)
    imgs = [f"images/{n}_sheet.png" for n in ("a", "b", "c", "d", "e")] + ["images/venue.png", "images/judges.png"]
    p = dr.plan_unit({"kind": "sung", "duration": 6, "images": imgs, "audio": "a.wav", "prompt": ""}, spec)
    assert p["use_audio"] and p["keep"] == [1, 2, 3, 4]
    assert "图片6（venue）" in p["notes"][0] and "图片7（judges）" in p["notes"][0] and "图片5" in p["notes"][0]


@pytest.mark.parametrize("vals,want,got", [([4, 5, 6, 7, 8], 7, 7), ([5, 10], 7, 10), ([5, 10], 12, 10)])
def test_duration_rounds_up_to_allowed(vals, want, got):
    d, note = dr.pick_duration(want, {"durations": vals})
    assert d == got and (note is not None) == (want > max(vals))


def test_duration_range_and_resolution():
    assert dr.pick_duration(6.5, {"duration_min": 4, "duration_max": 15, "duration_step": 1})[0] == 7
    assert dr.pick_duration(3, {"duration_min": 4, "duration_max": 15, "duration_step": 1})[0] == 4
    assert dr.pick_resolution("720p", {"resolutions": ["480P", "720P"]}) == "720P"
    assert dr.pick_resolution("720p", {"resolutions": ["480P", "1080P"]}) == "480P"  # closest
    assert dr.pick_resolution("720p", {}) == "720P"


def test_build_prompt_binds_placeholders_and_renames_dropped():
    keep = {1: "11111111-1111-4111-8111-111111111111", 2: "22222222-2222-4222-8222-222222222222"}
    p = dr.build_prompt(PROMPT_SUNG, 4, keep, "33333333-3333-4333-8333-333333333333")
    assert "@图片" not in p and "@音频" not in p
    assert p.count("{{res:11111111-1111-4111-8111-111111111111}}") == 2
    assert "{{res:33333333-3333-4333-8333-333333333333}}" in p
    assert "张楚岚（队友）" not in p and "张楚岚 鼓掌" in p          # dropped clause removed, mention by name
    assert "主舞台" not in p.split("【镜头1】")[0] and "在 场景图 的舞台上" in p
    plain = dr.build_prompt(PROMPT_SUNG, 4, keep, None, placeholders=False)
    assert "@图片1" in plain and "原曲" in plain and "{{" not in plain


# ---------------------------------------------------------------- end-to-end with the fake CLI

def test_full_run_commands_and_outputs(tmp_path):
    root = make_bundle(tmp_path / "b")
    fake = FakeDreamina()
    code, out, r = run(root, fake)
    assert code == 0, out
    st = json.loads((root / "state.json").read_text(encoding="utf-8"))
    pid = st["project_id"]
    up = calls(fake, "resource", "upload")
    assert len(up) == 7 and all(c[c.index("--project-id") + 1] == pid for c in up)  # 4 + 1 images, 2 audio windows
    assert {c[c.index("--type") + 1] for c in up} == {"image", "audio"}
    cr = calls(fake, "node", "create", "video")
    assert len(cr) == 2
    c1 = cr[0]
    assert c1[c1.index("--mode") + 1] == "m2v" and c1[c1.index("--model") + 1] == "seedance_2_0"
    assert c1[c1.index("--ratio") + 1] == "16:9" and c1[c1.index("--resolution") + 1] == "720P"
    assert c1[c1.index("--duration") + 1] == "7" and c1.count("--ref") == 5
    assert "{{res:" in c1[c1.index("--prompt") + 1]
    for c in calls(fake, "node", "confirm"):
        node = c[c.index("--node-id") + 1]
        assert int(c[c.index("--credit-ceiling") + 1]) == int(fake.s["nodes"][node]["duration"] * 10)
    runs = calls(fake, "node", "run")
    assert len(runs) == 2 and all("--submit-id" in c and "--credit-token" in c for c in runs)
    waits = calls(fake, "operation", "wait")
    assert all(c[c.index("--timeout") + 1] == "0" and c[c.index("--project-id") + 1] == pid for c in waits)
    dl = calls(fake, "resource", "download")
    assert [c[c.index("-o") + 1].endswith(f"takes/{u}/take-1.mp4") for c, u in zip(dl, ("u01", "u02"))] == [True, True]
    assert (root / "takes" / "u01" / "take-1.mp4").read_bytes()[4:8] == b"ftyp"
    res = json.loads((root / "results.json").read_text(encoding="utf-8"))
    assert [x["status"] for x in res["units"]] == ["downloaded", "downloaded"]
    assert res["units"][0]["quote"] == 70 and res["units"][0]["submit_id"] == st["units"]["u01/take-1"]["submit_id"]
    with zipfile.ZipFile(root / "takes.zip") as z:
        assert set(z.namelist()) == {"takes/u01/take-1.mp4", "takes/u02/take-1.mp4", "results.json"}
    blob = (root / "state.json").read_text(encoding="utf-8") + "".join(
        p.read_text(encoding="utf-8") for p in (root / "logs").glob("*.log"))
    assert "tok-" not in blob                                     # credit tokens are never persisted
    assert any("总报价 120 积分" in o for o in out)


def test_rerun_waits_on_same_submit_id_without_new_run(tmp_path):
    root = make_bundle(tmp_path / "b")
    state = {}
    code, out, _ = run(root, FakeDreamina(state, polls_to_finish=99), "--max-wait", "0")
    st = json.loads((root / "state.json").read_text(encoding="utf-8"))
    assert {v["status"] for v in st["units"].values()} == {"submitted"}
    fake2 = FakeDreamina(state, polls_to_finish=1)
    n_before = len(calls(fake2, "node", "run"))
    code, out, _ = run(root, fake2)
    assert code == 0
    assert len(calls(fake2, "node", "run")) == n_before == 2      # no new run on resume
    assert all(v == 1 for v in state["runs"].values())
    assert len(calls(fake2, "node", "create", "video")) == 2       # nodes not saved twice
    assert all(v == 1 for v in state["uploads"].values())          # uploads not repeated
    st = json.loads((root / "state.json").read_text(encoding="utf-8"))
    assert {v["status"] for v in st["units"].values()} == {"downloaded"}


def test_lost_run_response_is_observed_not_resubmitted(tmp_path):
    root = make_bundle(tmp_path / "b")
    fake = FakeDreamina(lose_run_response=True)
    code, out, r = run(root, fake, "--units", "u02")
    assert code == 0
    assert len(calls(fake, "node", "run")) == 1
    assert r.rec("u02")["status"] == "downloaded"


def test_cap_and_balance_stop_before_any_spend(tmp_path):
    root = make_bundle(tmp_path / "b")
    fake = FakeDreamina()
    code, out, _ = run(root, fake, "--credit-cap", "100")
    assert code == 5 and not calls(fake, "node", "confirm") and not calls(fake, "node", "run")
    assert any("超过上限" in o for o in out)
    fake2 = FakeDreamina(credits="50")
    code, out, _ = run(make_bundle(tmp_path / "c"), fake2)
    assert code == 5 and not calls(fake2, "node", "run") and any("可用积分" in o for o in out)


def test_cap_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DREAMINA_CREDIT_CAP", "60")
    fake = FakeDreamina()
    code, _, _ = run(make_bundle(tmp_path / "b"), fake)
    assert code == 5 and not calls(fake, "node", "run")


def test_not_logged_in_stops_without_writes(tmp_path):
    fake = FakeDreamina(logged_in=False)
    code, out, _ = run(make_bundle(tmp_path / "b"), fake)
    assert code == 2 and not calls(fake, "resource", "upload") and not calls(fake, "canvas", "create")
    assert any("auth login" in o for o in out)


def test_download_fallback_logs_canvas_url(tmp_path):
    root = make_bundle(tmp_path / "b")
    fake = FakeDreamina(download_works=False)
    code, out, r = run(root, fake)
    res = json.loads((root / "results.json").read_text(encoding="utf-8"))
    assert {x["status"] for x in res["units"]} == {"manual_download"}
    assert res["web_url"].startswith("https://example.invalid/canvas/")
    assert any(res["web_url"] in o for o in out) and any("7 天" in o for o in out)
    assert not (root / "takes.zip").exists()


def test_failed_unit_suggests_retake(tmp_path):
    root = make_bundle(tmp_path / "b")
    code, out, r = run(root, FakeDreamina(fail_units={"u01"}))
    assert code == 1 and r.rec("u01")["status"] == "failed" and r.rec("u02")["status"] == "downloaded"
    assert any("--units u01 --take 2" in o for o in out)
    fake = FakeDreamina()
    code, out, r = run(root, fake, "--units", "u01", "--take", "2")
    assert code == 0 and r.rec("u01")["status"] == "downloaded" and (root / "takes/u01/take-2.mp4").is_file()
    st = json.loads((root / "state.json").read_text(encoding="utf-8"))
    assert st["units"]["u01/take-1"]["submit_id"] != st["units"]["u01/take-2"]["submit_id"]


def test_dry_run_only_reads(tmp_path):
    root = make_bundle(tmp_path / "b")
    fake = FakeDreamina()
    code, out, r = run(root, fake, "--dry-run")
    assert code == 0 and not (root / "state.json").exists()
    executed = {" ".join(c[:2]) for c in fake.s["log"]}
    assert executed <= {"version", "auth status", "auth account", "model find", "model list", "model seedance_2_0",
                        "node create"}
    assert all("--dry-run" in c for c in calls(fake, "node", "create"))
    assert "node run" in (root / "logs" / "u01.log").read_text(encoding="utf-8")


def test_find_cli_env_override(tmp_path, monkeypatch):
    exe = tmp_path / "dc"
    exe.write_text("#!/bin/sh\n")
    monkeypatch.setenv("DREAMINA_CANVAS", str(exe))
    assert dr.find_cli() == str(exe)


# ---------------------------------------------------------------- ep dreamina-bundle

def _episode(ep: Path) -> Path:
    for n in ("a_sheet", "venue", "a_face"):
        _png(ep / "refs" / f"{n}.png", n)
    _png(ep / "refs" / "canon" / "zhuge_qing.jpg", "canon")
    u = ep / "units" / "u01"
    _png(u / "图片1_a_sheet.png", "a_sheet-small")
    _png(u / "图片2_venue.png", "venue-small")
    _wav(u / "u01_vocal.wav", 2)
    req = {"unit": "u01", "kind": "sung", "duration": 6, "resolution": "720p", "aspect_ratio": "16:9",
           "images": ["units/u01/图片1_a_sheet.png", "units/u01/图片2_venue.png"], "audio": "units/u01/u01_vocal.wav",
           "first_frame": None, "prompt": PROMPT_SUNG}
    (u / "request.json").write_text(json.dumps(req, ensure_ascii=False), encoding="utf-8")
    (u / "prompt.txt").write_text("【提示词】\n" + PROMPT_SUNG, encoding="utf-8")
    u2 = ep / "units" / "u02"
    _png(u2 / "图片1_a_sheet.png", "a_sheet-small")
    _wav(u2 / "u02_inst.wav", 1)
    (u2 / "request.json").write_text(json.dumps(dict(req, unit="u02", kind="motion", images=["units/u02/图片1_a_sheet.png"],
                                                     audio="units/u02/u02_inst.wav")), encoding="utf-8")
    (ep / "units" / "summary.json").write_text(json.dumps([{"unit": "u01"}, {"unit": "u02"}]), encoding="utf-8")
    return ep


def test_bundle_rewrites_paths_dedups_and_excludes_canon(tmp_path):
    ep = _episode(tmp_path / "ep")
    r = build_bundle(ep, tmp_path / "out" / "dreamina_bundle")
    out = r["out"]
    assert r["images"] == 2 and sorted(p.name for p in (out / "images").iterdir()) == ["a_sheet.png", "venue.png"]
    req = json.loads((out / "units" / "u01" / "request.json").read_text(encoding="utf-8"))
    assert req["images"] == ["images/a_sheet.png", "images/venue.png"] and req["audio"] == "units/u01/u01_vocal.wav"
    assert all((out / p).is_file() for p in req["images"] + [req["audio"]])
    assert (out / "units" / "u01" / "prompt.txt").is_file() and (out / "run_dreamina.py").is_file()
    assert (out / "run_dreamina.py").read_bytes() == Path(dr.__file__).read_bytes()
    readme = (out / "README.md").read_text(encoding="utf-8")
    assert "python3 run_dreamina.py" in readme and "Google Drive" in readme and "7 天" in readme and "—" not in readme
    man = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert man["units"] == ["u01", "u02"] and man["take"] == 1 and man["episode"] == "ep"
    assert not any("canon" in f for f in man["files"])
    assert r["zip"] and zipfile.ZipFile(r["zip"]).namelist()[0].startswith("dreamina_bundle/")
    r2 = build_bundle(ep, tmp_path / "retake", units=["u02"], take=2, make_zip=False)
    m2 = json.loads((r2["out"] / "manifest.json").read_text(encoding="utf-8"))
    assert m2["units"] == ["u02"] and m2["take"] == 2 and r2["zip"] is None


def test_bundle_refuses_canon_art_and_previous_run(tmp_path):
    ep = _episode(tmp_path / "ep")
    (ep / "units" / "u01" / "图片1_a_sheet.png").write_bytes((ep / "refs" / "canon" / "zhuge_qing.jpg").read_bytes())
    with pytest.raises(ValueError, match="canon"):
        build_bundle(ep, tmp_path / "o1")
    ep2 = _episode(tmp_path / "ep2")
    o = tmp_path / "o2"
    o.mkdir()
    (o / "state.json").write_text("{}")
    with pytest.raises(FileExistsError):
        build_bundle(ep2, o)


def test_bundle_runs_end_to_end_with_fake_cli(tmp_path):
    ep = _episode(tmp_path / "ep")
    out = build_bundle(ep, tmp_path / "bundle", make_zip=False)["out"]
    fake = FakeDreamina()
    code, msgs, r = run(out, fake)
    assert code == 0 and (out / "takes" / "u01" / "take-1.mp4").is_file() and (out / "takes.zip").is_file()
