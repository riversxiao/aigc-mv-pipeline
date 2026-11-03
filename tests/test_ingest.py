"""ep ingest-takes: copy Dreamina takes (folder / zip / wrapper folder), sync, auto pick, retake list, render."""

import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from typer.testing import CliRunner

from aigc_mv.board import plan
from aigc_mv.cli_ep import app
from aigc_mv.edit import _pick_take, take_fit
from aigc_mv.episode import load_episode
from aigc_mv.sync import load_unit_takes, save_unit_takes
from aigc_mv.timing import analyze
from aigc_mv.tools import ffmpeg_exe, has_ffmpeg, jsave, video_size
from aigc_mv.windows import write_windows

from test_episode_pipeline import BPM, EXAMPLE, _synth

pytestmark = pytest.mark.skipif(not has_ffmpeg(), reason="ffmpeg not available")
runner = CliRunner()


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    d = tmp_path_factory.mktemp("base") / "ep"
    shutil.copytree(EXAMPLE, d)
    ep = load_episode(d)
    t = analyze(d, ep, mode="grid", bpm=BPM)
    _synth(d, t)
    b = plan(ep, t)
    jsave(d / "analysis" / "timing.json", t)
    jsave(d / "board" / "board.json", b)
    write_windows(d, ep, t, b)
    return d, b


@pytest.fixture()
def ep(base, tmp_path):
    d = tmp_path / "ep"
    shutil.copytree(base[0], d)
    return d, base[1]


def _mp4(out: Path, dur: float, audio: Path | None = None, delay: float = 0.0, size="64x36", fps=24,
         color="gray") -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    args = [ffmpeg_exe(), "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c={color}:s={size}:r={fps}:d={dur}"]
    if audio is not None:
        args += ["-i", str(audio), "-af", f"adelay={int(delay * 1000)}:all=1,apad", "-c:a", "aac"]
    args += ["-t", str(dur), "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(out)]
    subprocess.run(args, check=True, capture_output=True)
    return out


def _units(b):
    sung = [u for u in b.units if u.kind == "sung"]
    motion = [u for u in b.units if u.kind == "motion"]
    return sung, motion


def _window(d: Path, u) -> Path:
    return d / "units" / u.id / (f"{u.id}_vocal.wav" if u.audio == "vocal" else f"{u.id}_inst.wav")


def _noise(d: Path, dur: float) -> Path:
    p = d / "noise.wav"
    sf.write(p, 0.2 * np.random.default_rng(1).standard_normal(int(dur * 16000)).astype(np.float32), 16000)
    return p


def test_zip_with_wrapper_folder_syncs_picks_and_lists_retakes(ep, tmp_path):
    d, b = ep
    sung, motion = _units(b)
    good, bad, eye, failed, manual = sung[0], sung[1], sung[2], sung[3], sung[4]
    m = motion[0]
    src = tmp_path / "ret" / "dreamina_bundle" / "takes"
    _mp4(src / good.id / "take-1.mp4", good.duration, _window(d, good), delay=0.2)
    _mp4(src / bad.id / "take-1.mp4", bad.duration, _noise(tmp_path, bad.duration))
    _mp4(src / eye.id / "take-1.mp4", eye.duration)  # first_last_frame: no soundtrack copy
    _mp4(src / m.id / "take-1.mp4", m.duration - 1.0)  # too short
    results = {"episode": "x", "take": 1, "model": "seedance-x", "project_id": "p", "web_url": "https://canvas",
               "units": [
                   {"unit": good.id, "take": 1, "status": "downloaded", "file": f"takes/{good.id}/take-1.mp4",
                    "mode": "m2v", "model": "seedance-x", "notes": []},
                   {"unit": bad.id, "take": 1, "status": "downloaded", "file": f"takes/{bad.id}/take-1.mp4",
                    "mode": "m2v"},
                   {"unit": eye.id, "take": 1, "status": "downloaded", "file": f"takes/{eye.id}/take-1.mp4",
                    "mode": "first_last_frame", "notes": ["lip sync by eye"]},
                   {"unit": m.id, "take": 1, "status": "downloaded", "file": f"takes/{m.id}/take-1.mp4",
                    "mode": "m2v"},
                   {"unit": failed.id, "take": 1, "status": "rejected", "error": "moderation"},
                   {"unit": manual.id, "take": 1, "status": "manual_download"},
               ]}
    (src.parent / "results.json").write_text(json.dumps(results), encoding="utf-8")
    (src / "u99").mkdir()
    (src / "u99" / "take-1.mp4").write_bytes((src / good.id / "take-1.mp4").read_bytes())
    z = tmp_path / "takes.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_STORED) as zf:
        for p in sorted((tmp_path / "ret").rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(tmp_path / "ret").as_posix())
        zf.writestr("__MACOSX/dreamina_bundle/takes/._x.mp4", b"junk")

    r = runner.invoke(app, ["ingest-takes", str(d), str(z)])
    assert r.exit_code == 0, r.output
    assert "u99" in r.output and "不认识的单元" in r.output
    for u in (good, bad, eye, m):
        assert (d / "units" / u.id / "takes" / "take-1.mp4").is_file()
    assert not (d / "units" / "u99").exists()

    g = load_unit_takes(d, good.id)
    assert g.pick == "take-1.mp4" and g.auto
    assert g.takes[0].copy_ and abs(g.takes[0].lag - 0.2) <= 0.03 and g.takes[0].synced
    assert load_unit_takes(d, m.id).pick == "take-1.mp4"

    rt = json.loads((d / "units" / "retakes.json").read_text(encoding="utf-8"))
    redo = {x["unit"]: x["reasons"] for x in rt["retake"]}
    assert good.id not in redo
    assert redo[bad.id] == ["lip_not_verified"]
    assert redo[m.id] == ["too_short"]
    assert redo[failed.id] == ["no_take", "rejected"]
    assert eye.id not in redo and [x["unit"] for x in rt["by_eye"]] == [eye.id]
    assert [x["unit"] for x in rt["manual_download"]] == [manual.id]
    assert manual.id not in redo
    missing = {u.id for u in b.units} - {good.id, bad.id, eye.id, m.id, manual.id}
    assert missing <= set(redo)
    assert rt["take"] == 2
    assert rt["command"] == (f"aigc-mv ep dreamina-bundle {d} --units {','.join(x['unit'] for x in rt['retake'])} "
                             "--take 2")
    md = (d / "units" / "retakes.md").read_text(encoding="utf-8")
    assert "重拍" in md and "肉眼" in md and "手动下载" in md
    log = json.loads((d / "units" / "ingest.json").read_text(encoding="utf-8"))
    assert log[eye.id]["take-1.mp4"]["mode"] == "first_last_frame"
    assert log[failed.id]["_last_status"]["status"] == "rejected"


def test_dir_ingest_never_overwrites_and_keeps_user_pick(ep, tmp_path):
    d, b = ep
    u = _units(b)[0][0]
    a = _mp4(tmp_path / "a" / "takes" / u.id / "take-1.mp4", u.duration, _noise(tmp_path, u.duration))
    r = runner.invoke(app, ["ingest-takes", str(d), str(tmp_path / "a")])
    assert r.exit_code == 0, r.output
    dst = d / "units" / u.id / "takes"
    orig = (dst / "take-1.mp4").read_bytes()
    assert orig == a.read_bytes()

    # the same file again: nothing new
    r = runner.invoke(app, ["ingest-takes", str(d), str(tmp_path / "a")])
    assert "已有相同文件" in r.output and sorted(p.name for p in dst.glob("*.mp4")) == ["take-1.mp4"]

    # a different take-1 and a take-2 (bundle folder layout without takes/, unit folder at the root)
    _mp4(tmp_path / "b" / u.id / "take-1.mp4", u.duration, _noise(tmp_path, u.duration), color="blue")
    _mp4(tmp_path / "b" / u.id / "take-2.mp4", u.duration, _window(d, u), delay=0.0, color="red")
    ut = load_unit_takes(d, u.id)
    ut.pick, ut.auto, ut.notes = "take-1.mp4", False, "我喜欢这条"
    save_unit_takes(d, ut)
    r = runner.invoke(app, ["ingest-takes", str(d), str(tmp_path / "b")])
    assert r.exit_code == 0, r.output
    assert (dst / "take-1.mp4").read_bytes() == orig
    assert sorted(p.name for p in dst.glob("*.mp4")) == ["take-1.mp4", "take-1.v2.mp4", "take-2.mp4"]
    ut = load_unit_takes(d, u.id)
    assert len(ut.takes) == 3 and ut.pick == "take-1.mp4" and not ut.auto and ut.notes == "我喜欢这条"
    assert "保留你手动选的" in r.output

    r = runner.invoke(app, ["pick", str(d), "--auto", "--force"])
    assert r.exit_code == 0, r.output
    ut = load_unit_takes(d, u.id)
    assert ut.auto and ut.pick == "take-2.mp4", [(t.take, t.lag, t.ncc) for t in ut.takes]

    r = runner.invoke(app, ["pick", str(d), u.id, "take-1"])
    assert r.exit_code == 0 and not load_unit_takes(d, u.id).auto
    rt = json.loads((d / "units" / "retakes.json").read_text(encoding="utf-8"))
    assert rt["take"] == 3  # next take number after take-2


def test_bad_source_and_non_mp4(ep, tmp_path):
    d, b = ep
    u = b.units[0]
    r = runner.invoke(app, ["ingest-takes", str(d), str(tmp_path / "nope")])
    assert r.exit_code == 1
    (tmp_path / "c" / "takes" / u.id).mkdir(parents=True)
    (tmp_path / "c" / "takes" / u.id / "take-1.mp4").write_bytes(b"<html>login</html>")
    r = runner.invoke(app, ["ingest-takes", str(d), str(tmp_path / "c")])
    assert r.exit_code == 0 and "不是 mp4" in r.output
    assert not list((d / "units" / u.id / "takes").glob("*.mp4"))


def test_take_fit_and_missing_files():
    assert "crop=1920:1080" in take_fit((1280, 720), 1920, 1080)
    assert "crop=1920:1080" in take_fit((1248, 704), 1920, 1080)
    assert "pad=1920:1080" in take_fit((720, 720), 1920, 1080)
    assert "pad=1920:1080" in take_fit(None, 1920, 1080)


def test_render_mixes_odd_sized_take_with_placeholders(ep, tmp_path):
    from aigc_mv.edit import render
    from aigc_mv.sync import TakeSync, UnitTakes

    d, b = ep
    epi = load_episode(d)
    from aigc_mv.timing import load_timing

    t = load_timing(d)
    u = b.units[0]
    save_unit_takes(d, UnitTakes(unit="ghost", takes=[TakeSync(take="take-1.mp4", duration=5)]))
    assert _pick_take(d, "ghost") == (None, None)  # measured but the file is gone: placeholder
    _mp4(d / "units" / u.id / "takes" / "take-1.mp4", u.duration, size="96x96", fps=30)
    save_unit_takes(d, UnitTakes(unit=u.id, takes=[TakeSync(take="take-1.mp4", duration=u.duration)],
                                 pick="take-1.mp4"))
    end = min(b.duration, u.song_t0 + u.duration + 1.0)
    out = render(d, epi, b, t, resolution="480p", test=(0.0, end), look=False, overlays=False)
    assert out.is_file() and video_size(out) == (854, 480)
    edl = json.loads((d / "edit" / "edl.json").read_text(encoding="utf-8"))
    srcs = {e["source"] for e in edl["entries"]}
    assert "take" in srcs and srcs - {"take"}
