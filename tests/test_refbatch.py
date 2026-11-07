"""refbatch: caps with concurrency, per-item candidate counts, prompts from refs_plan, locking rules (no network)."""

import json
import threading
import time
from pathlib import Path

import pytest
from PIL import Image

from aigc_mv import refbatch as rb
from aigc_mv.episode import Budget
from aigc_mv.providers.base import Job, SpendGate


class FakeProvider:
    name = "fake"
    model = "fake-model"

    def __init__(self, cost=0.06, fail_on=(), sleep=0.0, calls=None):
        self.cost, self.fail_on, self.sleep = cost, fail_on, sleep
        self.calls = calls if calls is not None else []
        self.last_job, self.last_cost = None, None

    def generate(self, req, dst):
        self.calls.append(req)
        time.sleep(self.sleep)
        if req.name in self.fail_on:
            err = RuntimeError("declined by safety")
            err.job = Job(id="x", status="declined")
            self.last_cost = 0.0
            raise err
        dst.mkdir(parents=True, exist_ok=True)
        p = dst / f"{req.name}.png"
        Image.new("RGB", (30, 40), (9, 9, 9)).save(p)
        self.last_job, self.last_cost = Job(id=req.name, status="done"), self.cost
        return [p]


def _items(k=3, n=None):
    return [rb.Item(f"p{i}.png", f"plate {i}", "prompt", "16:9", [], "plates", n) for i in range(k)]


def test_run_batch_caps_hold_with_workers(tmp_path):
    gate = SpendGate(tmp_path, Budget(cap_usd=100))
    calls = []
    lock = threading.Lock()

    def make():
        with lock:
            return FakeProvider(cost=0.06, sleep=0.01, calls=calls)

    res = rb.run_batch(tmp_path, gate, make, _items(5), n=4, cap_usd=0.5, max_images=100, est_usd=0.1, workers=4,
                       log=lambda *_: None)
    spent, images = gate.tag_totals(rb.TAG)
    # every call reserved 0.10 before it started and costs at most that, so the real total never passes the cap
    assert spent <= 0.5 and 5 <= images <= 8
    assert res.stopped and "run cap" in res.stopped
    # item order is kept: the first plate got its candidates first
    assert len(rb.candidates(tmp_path, "p0")) == 4


def test_run_batch_max_images_and_item_n(tmp_path):
    gate = SpendGate(tmp_path, Budget(cap_usd=100))
    items = _items(2, n=2) + _items(1)
    items[-1].file = "q.png"
    res = rb.run_batch(tmp_path, gate, lambda: FakeProvider(), items, n=4, cap_usd=10, max_images=100,
                       log=lambda *_: None)
    assert len(res.made) == 2 + 2 + 4
    assert [p.name for p in rb.candidates(tmp_path, "q")] == [f"q_cand_{i}.png" for i in (1, 2, 3, 4)]
    res = rb.run_batch(tmp_path, gate, lambda: FakeProvider(), _items(1), n=4, cap_usd=10, max_images=9,
                       log=lambda *_: None)
    assert gate.tag_totals(rb.TAG)[1] == 9 and "image limit" in res.stopped
    # numbering continues after existing candidates
    assert rb.candidates(tmp_path, "p0")[-1].name == "p0_cand_3.png"


def test_declined_is_logged_unbilled_and_run_continues(tmp_path):
    gate = SpendGate(tmp_path, Budget(cap_usd=100))
    res = rb.run_batch(tmp_path, gate, lambda: FakeProvider(fail_on=("p0_cand_1",)), _items(1), n=2, cap_usd=10,
                       max_images=10, log=lambda *_: None)
    assert res.failed[0][1] == "declined" and len(res.made) == 1
    spent, images = gate.tag_totals(rb.TAG)
    assert images == 1 and spent == pytest.approx(0.06)


def _plan(tmp: Path) -> Path:
    refs = tmp / "refs"
    (refs / "canon").mkdir(parents=True)
    Image.new("RGB", (8, 8)).save(refs / "canon" / "old.jpg")
    plan = [
        {"file": "venue.png", "plate": True, "title": "舞台正面", "aspect": "16:9", "uploads": [], "gpt": "V."},
        {"file": "crowd.png", "plate": True, "title": "观众席", "aspect": "16:9", "gpt": "C.",
         "uploads": [{"file": "venue.png", "role": "x"}]},
        {"cast": "j", "step": 1, "kind": "face", "file": "j_face.png", "mj_params": "--iw 1.5 --ar 3:4",
         "en": "<原作图链接> portrait of the character in the image prompt, a Chinese man who looks about 90, white "
               "beard --iw 1.5 --ar 3:4 --no anime, text",
         "uploads": [{"path": "refs/canon/old.jpg"}]},
        {"cast": "o", "step": 1, "kind": "face", "file": "o_face.png", "mj_params": "--ar 3:4",
         "en": "portrait, a 28-year-old Chinese man --ar 3:4 --style raw --no anime", "uploads": []},
        {"cast": "o", "step": 2, "kind": "full", "file": "o_full.png", "mj_params": "--oref <x> --ow 100 --ar 2:3",
         "en": "full body, the same person as the omni reference, a 28-year-old Chinese man --oref <x> --ar 2:3 --no cgi",
         "uploads": [{"file": "o_face.png"}]},
        {"cast": "o", "step": 2, "kind": "half", "file": "o_half.png", "mj_params": "--ar 3:4",
         "en": "waist-up shot in the full stage wardrobe, the same person as the omni reference --ar 3:4",
         "uploads": [{"file": "o_face.png"}]},
        {"cast": "j", "step": 2, "kind": "half", "file": "j_half.png", "mj_params": "--ar 3:4",
         "en": "waist-up shot, holding a silver corded microphone below the mouth, the same person as the omni "
               "reference --ar 3:4", "uploads": [{"file": "j_face.png"}]},
    ]
    (refs / "refs_plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    return refs


class _Cast:
    def __init__(self, name):
        self.name_cn = name


class _Ep:
    cast = {"j": _Cast("老天师"), "o": _Cast("门人")}


def test_items_from_plan(tmp_path):
    refs = _plan(tmp_path)
    with pytest.raises(FileNotFoundError, match="venue.png"):
        rb.plate_items(tmp_path, ["crowd.png"])
    Image.new("RGB", (8, 8)).save(refs / "venue.png")
    it = rb.plate_items(tmp_path, ["crowd.png"])[0]
    assert it.refs == [refs / "venue.png"] and it.aspect == "16:9"

    j, o = rb.step1_items(tmp_path, _Ep(), ["j", "o"])
    assert j.refs == [refs / "canon" / "old.jpg"] and "elderly, about 90" in j.prompt and "twenties" not in j.prompt
    assert o.refs == [] and "--" not in o.prompt and "about 28" in o.prompt and "Avoid: anime" in o.prompt

    with pytest.raises(FileNotFoundError, match="o_face.png"):
        rb.step2_items(tmp_path, _Ep(), ["o"], ["full"])
    Image.new("RGB", (8, 8)).save(refs / "o_face.png")
    full = rb.step2_items(tmp_path, _Ep(), ["o"], ["full"])[0]
    assert full.aspect == "2:3" and full.refs == [refs / "o_face.png"]
    assert "omni" not in full.prompt and "first input image" in full.prompt and "--" not in full.prompt

    # the half view only mentions a mic hand when the plan gives that person a mic
    half = rb.step2_items(tmp_path, _Ep(), ["o"], ["half"])[0]
    assert "microphone hand" not in half.prompt and "Both hands have five natural fingers" in half.prompt
    Image.new("RGB", (8, 8)).save(refs / "j_face.png")
    mic = rb.step2_items(tmp_path, _Ep(), ["j"], ["half"])[0]
    assert "The microphone hand has five natural fingers" in mic.prompt and "No microphone" not in mic.prompt


def test_lock_rules(tmp_path):
    cands = tmp_path / "refs" / "candidates"
    cands.mkdir(parents=True)
    for i in (1, 2):
        Image.new("RGB", (8, 8), (i, 0, 0)).save(cands / f"venue_cand_{i}.png")
    (tmp_path / "refs" / "x.png").write_bytes(b"hand made")
    Image.new("RGB", (8, 8)).save(cands / "x_cand_1.png")
    with pytest.raises(FileExistsError):
        rb.lock(tmp_path, "x.png", 1, "r")  # not made by lock
    rb.lock(tmp_path, "venue.png", 1, "user likes it", by="user")
    with pytest.raises(FileExistsError, match="user picked"):
        rb.lock(tmp_path, "venue.png", 2, "agent thinks")
    rb.lock(tmp_path, "venue.png", 2, "user changed mind", by="user")
    assert rb.load_picks(tmp_path)["venue.png"]["cand"] == 2
    assert Image.open(tmp_path / "refs" / "venue.png").getpixel((0, 0))[0] == 2


def test_contact_sheet_marks_pick(tmp_path):
    cands = tmp_path / "refs" / "candidates"
    cands.mkdir(parents=True)
    for i in (1, 2):
        Image.new("RGB", (30, 40), (200, 200, 200)).save(cands / f"venue_cand_{i}.png")
    rb.lock(tmp_path, "venue.png", 2, "r")
    rows = rb.item_rows(tmp_path, [rb.Item("venue.png", "舞台", "", "16:9")])
    assert [c[2] for c in rows[0][1]] == [False, True]
    out = rb.contact_sheet(rows, tmp_path / "s.jpg", tile_h=60, title="场景图")
    assert out.is_file() and Image.open(out).format == "JPEG"


def test_card_age():
    assert rb.card_age("a 24-year-old Chinese man") == 24
    assert rb.card_age("a Chinese man who looks about 88, tall at 187 cm") == 88
    assert rb.card_age("a Chinese woman who looks 25, slim") == 25
    assert rb.card_age("tall at 187 cm") is None
