"""H3 timing, input integrity and uncertain-submission regressions."""
import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from aigc_mv.h3 import audio_window, frame_count
from aigc_mv import h3_runner
from aigc_mv.h3 import approved_shot_takes


def test_frame_grid_covers_requested_duration_and_rejects_overlong():
    for seconds in [0.8, 3.74, 3.751, 5.0, 8.001, 14.9]:
        frames = frame_count(seconds)
        assert frames % 17 == 5 and frames / 24 >= seconds
    with pytest.raises(ValueError):
        frame_count(16)


def test_target_vocal_clock_survives_padding_and_resampling(tmp_path):
    sr = 48000
    # Source event at 1.2 s must land at 0.5 s after cutting at 1 s + 0.3 s lead.
    x = np.zeros((sr * 3, 2), dtype=np.float32)
    x[round(1.2 * sr):round(1.4 * sr)] = 0.4
    sf.write(tmp_path / "source.wav", x, sr, subtype="PCM_16")
    audio_window(tmp_path / "source.wav", tmp_path / "guide.wav", 1, 2, .3, 90)
    y, new_sr = sf.read(tmp_path / "guide.wav", always_2d=True)
    assert new_sr == 32000 and y.shape == (120000, 2)
    active = np.flatnonzero(np.abs(y[:, 0]) > .2)
    assert abs(active[0] / new_sr - .5) < .001
    assert abs((active[-1] + 1) / new_sr - .7) < .001
    with pytest.raises(ValueError, match="truncate"):
        audio_window(tmp_path / "source.wav", tmp_path / "bad.wav", 0, 3, .3, 73)


def test_bundle_tampering_fails_without_submission(tmp_path):
    (tmp_path / "input").mkdir()
    p = tmp_path / "input" / "ref.png"
    p.write_bytes(b"original")
    (tmp_path / "manifest.json").write_text(json.dumps({
        "files": {"input/ref.png": h3_runner.digest(p)}, "jobs": []}))
    p.write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum"):
        h3_runner.run(tmp_path, tmp_path, tmp_path / "out", "http://unused", dry_run=True)


def test_previous_line_tail_is_silenced_without_moving_target_word(tmp_path):
    sr = 48000
    x = np.zeros((sr * 3, 2), dtype=np.float32)
    x[round(1.02 * sr):round(1.06 * sr)] = .5  # previous lyric tail
    x[round(1.20 * sr):round(1.40 * sr)] = .4  # desired target word
    sf.write(tmp_path / "source.wav", x, sr, subtype="PCM_16")
    audio_window(tmp_path / "source.wav", tmp_path / "guide.wav", 1, 2, .3, 90, [(1.18, 1.42)])
    y, new_sr = sf.read(tmp_path / "guide.wav", always_2d=True)
    assert np.max(np.abs(y[round(.31 * new_sr):round(.38 * new_sr)])) < .001
    active = np.flatnonzero(np.abs(y[:, 0]) > .2)
    assert abs(active[0] / new_sr - .5) < .001


def test_unknown_submission_is_never_automatically_resubmitted(tmp_path, monkeypatch):
    root, comfy, out = tmp_path / "bundle", tmp_path / "comfy", tmp_path / "out"
    for p in [root / "input", comfy, out]:
        p.mkdir(parents=True)
    (root / "graph.json").write_text(json.dumps({"1": {"class_type": "TestNode"}}))
    (root / "manifest.json").write_text(json.dumps({"files": {}, "jobs": [
        {"job_id": "s001_abc", "workflow": "graph.json"}]}))
    (out / "state.json").write_text(json.dumps({"jobs": {"s001_abc": {"status": "submitting"}}}))
    calls = []
    def fake_api(base, route, data=None):
        calls.append(route)
        return {"TestNode": {}}
    monkeypatch.setattr(h3_runner, "api", fake_api)
    with pytest.raises(RuntimeError, match="outcome unknown"):
        h3_runner.run(root, comfy, out, "http://unused")
    assert "/prompt" not in calls


def test_audio_match_or_pilot_approval_cannot_enter_production_edit(tmp_path):
    out = tmp_path / "h3"
    out.mkdir()
    p = out / "candidate.mp4"
    p.write_bytes(b"video")
    base = {"job_id": "test", "file": "h3/candidate.mp4", "sha256": h3_runner.digest(p),
            "visual_status": "unreviewed", "identity_status": "pass", "audio_ncc": 1.0}
    index = out / "shot_takes.json"
    index.write_text(json.dumps({"s001": [base]}))
    assert approved_shot_takes(tmp_path) == {}
    base.update(visual_status="pass", pilot_override={"purpose": "solo test"})
    index.write_text(json.dumps({"s001": [base]}))
    assert approved_shot_takes(tmp_path) == {}
    base["pilot_override"] = {}
    index.write_text(json.dumps({"s001": [base]}))
    assert approved_shot_takes(tmp_path)["s001"]["job_id"] == "test"
    base["mode"] = "pilot"
    index.write_text(json.dumps({"s001": [base]}))
    assert approved_shot_takes(tmp_path) == {}
    base.update(mode="production", production_override={"camera": "locked"})
    index.write_text(json.dumps({"s001": [base]}))
    assert approved_shot_takes(tmp_path)["s001"]["job_id"] == "test"
    p.write_bytes(b"replaced")
    with pytest.raises(ValueError, match="changed"):
        approved_shot_takes(tmp_path)


def test_native_checkpoint_is_recovered_before_any_resampling(tmp_path,monkeypatch):
    root,comfy,out=tmp_path/'bundle',tmp_path/'comfy',tmp_path/'results'
    (root/'input').mkdir(parents=True);(comfy/'output/latents').mkdir(parents=True)
    (comfy/'output/latents/native.pt').write_bytes(b'saved native samples')
    (root/'graph.json').write_text(json.dumps({'1':{'class_type':'TestNode'}}))
    (root/'manifest.json').write_text(json.dumps({'files':{},'jobs':[{'job_id':'s011_x','workflow':'graph.json','checkpoint_name':'native.pt','output_prefix':'existing'}]}))
    calls=[]
    def fake_api(base,route,data=None):
        calls.append(route);return {'TestNode':{}}
    monkeypatch.setattr(h3_runner,'api',fake_api)
    with pytest.raises(RuntimeError,match='recover/decode'):
        h3_runner.run(root,comfy,out,'http://unused')
    assert '/prompt' not in calls


def test_production_environment_and_two_shot_compile_with_distinct_grammar(tmp_path, monkeypatch):
    from types import SimpleNamespace as NS
    from aigc_mv import h3
    from aigc_mv.board import BoardShot

    sf.write(tmp_path / "audio.wav", np.zeros((48000, 2)), 48000, subtype="PCM_16")
    (tmp_path / "frame.png").write_bytes(b"test-keyframe")
    cast = {k: NS(name_en=k, name_cn=k) for k in ("a", "b")}
    ep = NS(title="test", cast=cast, vocals="audio.wav", instrumental="audio.wav", song="audio.wav")
    shots = [BoardShot(id="s001", t0=0, t1=.8, section="test", kind="establish",
                      unit="u01", framing="WS", lens="35", camera="crane_in"),
             BoardShot(id="s002", t0=0, t1=.8, section="test", kind="perform", unit="u02",
                      who=["a", "b"], sung=True, singer="b", lines=[0],
                      framing="2S", lens="50", camera="locked")]
    monkeypatch.setattr(h3, "load_episode", lambda _: ep)
    monkeypatch.setattr(h3, "load_board", lambda _: NS(shot=lambda sid: next(s for s in shots if s.id == sid)))
    monkeypatch.setattr(h3, "load_timing", lambda _: NS(lines=[NS(t0=.1, t1=.7, text="测试")]))
    cfg = {"mode": "production", "lead_frames": 8, "scene_reference": "frame.png", "lock_guide_audio": True,
           "cast": {k: {"portrait": "frame.png", "description": k} for k in cast},
           "keyframes": {s.id: "frame.png" for s in shots},
           "shot_overrides": {"s001": {"look_description": "Persistent low exposure; bronze ring remains unlit.",
                                       "gallery_description": "The gallery remains indistinct in deep shadow.",
                                       "acting_description": ""},
                              "s002": {"action": "A small nod.", "reason": "restrained acting"}}}
    (tmp_path / "assets.json").write_text(json.dumps(cfg))
    ids = ("1", "2", "3", "4", "5", "6", "7", "8", "20", "21", "22", "23",
           "24", "25", "26", "27", "30", "31", "32", "34", "35")
    template = {k: {"class_type": "TestNode", "inputs": {}} for k in ids}
    (tmp_path / "template.json").write_text(json.dumps(template))
    out = tmp_path / "bundle"
    manifest = h3.export_bundle(tmp_path, tmp_path / "assets.json", tmp_path / "template.json",
                                out, [s.id for s in shots], allow_legacy_audio=True)
    environment, sung = manifest["jobs"]
    assert environment["visible_cast"] == []
    assert environment["scene_reference"] and "wide shot" in environment["prompt"]
    assert "crane descends" in environment["prompt"]
    assert "medium close-up" not in environment["prompt"]
    assert "Persistent low exposure; bronze ring remains unlit." in environment["prompt"]
    assert "flattering neutral key" not in environment["prompt"]
    assert "Natural small nods" not in environment["prompt"]
    assert "The gallery remains indistinct in deep shadow." in environment["prompt"]
    graph = json.loads((out / environment["workflow"]).read_text())
    assert graph["20"]["inputs"]["ref_images.ref_image_0"] == ["200", 0]
    assert graph["27"]["inputs"]["latent_image"] == ["39", 0]
    assert graph["39"]["class_type"] == "H3LockGuideAudio"
    assert graph["30"]["inputs"]["av_latent"] == ["37", 0]
    assert "h3_audio_lock.py" in manifest["files"]
    assert "two-shot" in sung["prompt"] and "<Subject 2> alone" in sung["prompt"]
    assert sung["pilot_override"] == {} and sung["production_override"]
    assert sung["clip_in"] == pytest.approx(8 / 24)
    h3_runner.verify_bundle(out)


def test_audio_lock_preserves_video_and_freezes_only_the_guide_clock(monkeypatch):
    import importlib.util
    import sys
    from types import ModuleType, SimpleNamespace as NS

    class Tensor(np.ndarray):
        def clone(self): return self.copy().view(Tensor)
        def movedim(self, a, b): return np.moveaxis(self, a, b).view(Tensor)
        def to(self, **kwargs): return self
    def tensor(a): return np.asarray(a,dtype=np.float32).view(Tensor)
    class Nested:
        is_nested=True
        def __init__(self, values): self.tensors=values
    fake_torch=NS(ones_like=lambda x:tensor(np.ones_like(x)), zeros_like=lambda x:tensor(np.zeros_like(x)),
                  nn=NS(functional=NS(pad=lambda x,p:tensor(np.pad(x,[(0,0)]*(x.ndim-1)+[(p[0],p[1])])))))
    comfy=ModuleType('comfy');nested=ModuleType('comfy.nested_tensor');nested.NestedTensor=Nested
    monkeypatch.setitem(sys.modules,'torch',fake_torch)
    monkeypatch.setitem(sys.modules,'comfy',comfy)
    monkeypatch.setitem(sys.modules,'comfy.nested_tensor',nested)
    source=Path(__file__).parents[1]/'src/aigc_mv/h3_audio_lock.py'
    spec=importlib.util.spec_from_file_location('h3_audio_lock_test',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    video=tensor(np.arange(48).reshape(1,24,2,1,1));target=tensor(np.zeros((1,32,2,5)))
    guide=tensor(np.ones((1,32,2,3))*7)
    vae=NS(audio_sample_rate=32000,encode=lambda _:guide)
    audio={'sample_rate':32000,'waveform':tensor(np.ones((1,2,3200)))}
    original={'samples':Nested((video,target))}
    out,=module.H3LockGuideAudio().lock_audio(original,vae,audio)
    assert out['samples'].tensors[0] is video
    assert np.all(out['samples'].tensors[1][...,:3]==7)
    assert np.all(out['samples'].tensors[1][...,3:]==0)
    assert np.all(out['noise_mask'].tensors[0]==1)
    assert np.all(out['noise_mask'].tensors[1]==0)
    assert 'noise_mask' not in original
    with pytest.raises(ValueError,match='sample rate'):
        module.H3LockGuideAudio().lock_audio(original,vae,{**audio,'sample_rate':48000})
