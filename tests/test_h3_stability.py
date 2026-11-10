"""Run-to-run stability: one pinned render profile, recorded seeds per take, explicit take choice."""
import json

import pytest

from test_directing import ready_plan, template  # actual images, stems, timing and a ready plan
from test_shared_assets import series, write_json  # noqa: F401  (pytest fixture)
from aigc_mv import h3
from aigc_mv.directing import REVIEW_CRITERIA
from aigc_mv.shared_assets import file_hash
from aigc_mv.shot_review import record_review


def _cfg(series):
    return json.loads(series.assets.read_text())


def test_template_must_match_the_pinned_profile(series):
    ready_plan(series)
    path = template(series)
    cfg = _cfg(series)
    assert h3.render_profile(cfg, path)["template_sha256"] == file_hash(path)
    cfg["model_profile"]["template_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="not the model_profile template"):
        h3.render_profile(cfg, path)
    cfg["model_profile"].pop("template_sha256")
    with pytest.raises(ValueError, match="needs model_profile.template_sha256"):
        h3.render_profile(cfg, path)
    cfg["schema_version"] = 3  # older configs keep working unpinned
    assert h3.render_profile(cfg, path)["steps"] == h3.DEFAULT_STEPS


def test_profile_fixes_steps_and_lora_strengths(series):
    ready_plan(series)
    path = template(series)
    cfg = _cfg(series)
    cfg["model_profile"].update(steps=14, lora_strengths={"2": 0.75, "3": 0.5})
    profile = h3.render_profile(cfg, path)
    assert profile["steps"] == 14 and profile["lora_strengths"] == {"2": 0.75, "3": 0.5}
    assert h3.render_profile(cfg, path, 14)["steps"] == 14
    with pytest.raises(ValueError, match="fixes steps=14"):
        h3.render_profile(cfg, path, 8)
    cfg["model_profile"]["lora_strengths"] = {"9": 0.5}
    with pytest.raises(ValueError, match="lora_strengths"):
        h3.render_profile(cfg, path)
    cfg["model_profile"]["lora_strengths"] = {"2": 5}
    with pytest.raises(ValueError, match="lora_strengths"):
        h3.render_profile(cfg, path)


def test_lora_strengths_reach_the_graph_and_the_job_identity(series):
    ready_plan(series)
    path = template(series)
    first = h3.export_bundle(series.ep, series.assets, path, series.root / "plain", ["s001"])
    graph = json.loads((series.root / "plain" / first["jobs"][0]["workflow"]).read_text())
    assert graph["2"]["inputs"]["strength_model"] == 0.0 and graph["3"]["inputs"]["strength_model"] == 0.0
    cfg = _cfg(series)
    cfg["model_profile"]["lora_strengths"] = {"2": 0.75}
    write_json(series.assets, cfg)
    second = h3.export_bundle(series.ep, series.assets, path, series.root / "lora", ["s001"])
    graph = json.loads((series.root / "lora" / second["jobs"][0]["workflow"]).read_text())
    assert graph["2"]["inputs"]["strength_model"] == 0.75
    assert second["jobs"][0]["job_id"] != first["jobs"][0]["job_id"]


def test_seed_is_deterministic_per_take_and_never_collides():
    cfg = {"seed_base": 1000}
    assert h3.shot_seed(cfg, "s012") == 1012  # take 1 keeps the historical formula
    assert h3.shot_seed(cfg, "s012", 2) == 1012 + h3.TAKE_SEED_STRIDE
    seeds = {h3.shot_seed(cfg, f"s{n:03d}", t) for n in range(1, 400) for t in (1, 2, 3)}
    assert len(seeds) == 399 * 3
    for bad in (0, 100, 1.5, True):
        with pytest.raises(ValueError, match="take"):
            h3.shot_seed(cfg, "s001", bad)


def test_rerun_reproduces_a_take_and_next_take_is_a_recorded_reroll(series):
    ready_plan(series)
    path = template(series)
    one = h3.export_bundle(series.ep, series.assets, path, series.root / "t1", ["s001"])["jobs"][0]
    again = h3.export_bundle(series.ep, series.assets, path, series.root / "t1b", ["s001"], take=1)["jobs"][0]
    two = h3.export_bundle(series.ep, series.assets, path, series.root / "t2", ["s001"], take=2)
    assert again["job_id"] == one["job_id"] and again["seed"] == one["seed"]
    job = two["jobs"][0]
    assert job["take"] == 2 and job["seed"] == one["seed"] + h3.TAKE_SEED_STRIDE
    assert job["job_id"] != one["job_id"]
    assert two["render_profile"]["take"] == 2 and two["render_profile"]["steps"] == h3.DEFAULT_STEPS


def test_camera_text_names_the_singer_by_subject_label(series):
    board_file = series.ep / "board/board.json"
    board = json.loads(board_file.read_text())
    board["shots"][0]["camera"] = "whip_in"
    write_json(board_file, board)
    ready_plan(series)
    path = template(series)
    prompt = h3.export_bundle(series.ep, series.assets, path, series.root / "cam", ["s001"])["jobs"][0]["prompt"]
    assert "settles on <Subject 1>'s face" in prompt
    assert "王也" not in prompt.split("[Shot 1]", 1)[1].split(".", 1)[0]


def _approved(series, job_id, name):
    video = series.ep / "h3" / name
    video.parent.mkdir(exist_ok=True)
    video.write_bytes(b"reviewed video " + job_id.encode())
    take = {"job_id": job_id, "file": f"h3/{name}", "sha256": file_hash(video), "mode": "production",
            "pilot_override": {}, "visual_status": "unreviewed", "identity_status": "unreviewed", "sung": True,
            "song_t0": 0, "song_t1": .8, "review_contract": {"version": 1, "criteria": REVIEW_CRITERIA}}
    return take


def _keep(series, job_id, sha):
    review = {"job_id": job_id, "video_sha256": sha, "verdict": "keep",
              "checks": {k: {"status": "pass", "evidence": "Checked at 0.5s and 2.0s"} for k in REVIEW_CRITERIA}}
    path = series.root / f"review_{job_id}.json"
    write_json(path, review)
    record_review(series.ep, "s001", job_id, path)


def test_several_approved_takes_need_an_explicit_selection(series):
    first, second = _approved(series, "job1", "a.mp4"), _approved(series, "job2", "b.mp4")
    pending = _approved(series, "job3", "c.mp4")
    write_json(series.ep / "h3/shot_takes.json", {"s001": [first, second, pending]})
    _keep(series, "job1", first["sha256"])
    assert h3.approved_shot_takes(series.ep)["s001"]["job_id"] == "job1"
    _keep(series, "job2", second["sha256"])
    with pytest.raises(ValueError, match="2 approved H3 takes"):
        h3.approved_shot_takes(series.ep)
    with pytest.raises(ValueError, match="not an approved"):
        h3.select_shot_take(series.ep, "s001", "job3")
    h3.select_shot_take(series.ep, "s001", "job1")
    assert h3.approved_shot_takes(series.ep)["s001"]["job_id"] == "job1"
    h3.select_shot_take(series.ep, "s001", "job2")  # re-selecting moves the single pick
    assert h3.approved_shot_takes(series.ep)["s001"]["job_id"] == "job2"
    data = json.loads((series.ep / "h3/shot_takes.json").read_text())
    assert [bool(r.get("selected")) for r in data["s001"]] == [False, True, False]


def test_h3_only_cut_lists_shots_without_an_approved_take(series):
    from aigc_mv.board import load_board

    first = _approved(series, "job1", "a.mp4")
    write_json(series.ep / "h3/shot_takes.json", {"s001": [first]})
    board = load_board(series.ep)
    assert h3.missing_h3_shots(series.ep, board) == ["s001", "s002"]
    _keep(series, "job1", first["sha256"])
    assert h3.missing_h3_shots(series.ep, board) == ["s002"]


def test_complete_job_without_video_fails_with_a_clear_message(series, tmp_path):
    bundle, results = tmp_path / "bundle", tmp_path / "results"
    write_json(bundle / "manifest.json", {"jobs": [{"job_id": "j1", "shot": "s001"}], "files": {}})
    write_json(results / "state.json", {"jobs": {"j1": {"status": "complete", "files": []}}})
    with pytest.raises(ValueError, match="no _raw.mp4"):
        h3.ingest_shot_results(series.ep, bundle, results)
