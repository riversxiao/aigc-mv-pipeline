"""OpenRouter image adapter + facetest caps, with the HTTP layer mocked (no network)."""

import base64
import io
import json
from pathlib import Path

import pytest
from PIL import Image

from aigc_mv import facetest
from aigc_mv.episode import Budget
from aigc_mv.providers import openrouter
from aigc_mv.providers.base import ImageRequest, SpendGate, SpendRefused

FAKE_KEY = "test-key-not-real-123"


def _png_b64(color=(200, 10, 10)) -> str:
    buf = io.BytesIO()
    Image.new("RGB", (30, 40), color).save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _ref(tmp: Path) -> Path:
    p = tmp / "canon.jpg"
    Image.new("RGB", (2000, 1500), (0, 0, 120)).save(p, "JPEG")
    return p


class FakeHTTP:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def __call__(self, url, body, headers, timeout):
        self.calls.append((url, body, headers))
        return self.replies.pop(0)


def _ok(cost=0.12, gid="gen-1"):
    return 200, {"id": gid, "data": [{"b64_json": _png_b64(), "media_type": "image/png"}],
                 "usage": {"completion_tokens": 4000, "cost": cost}}


@pytest.fixture
def key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", FAKE_KEY)


def test_request_body_and_saved_png(tmp_path, monkeypatch, key):
    http = FakeHTTP([_ok()])
    monkeypatch.setattr(openrouter, "_post", http)
    prov = openrouter.OpenRouterImage(model="openai/gpt-image-2.5-sunburst")
    out = prov.generate(ImageRequest(name="a_face_cand_1", prompt="p", aspect_ratio="3:4", refs=[_ref(tmp_path)]),
                        tmp_path / "out")
    url, body, headers = http.calls[0]
    assert url == "https://openrouter.ai/api/v1/images"
    assert body["model"] == "openai/gpt-image-2.5-sunburst" and body["n"] == 1 and body["aspect_ratio"] == "3:4"
    part = body["input_references"][0]
    assert part["type"] == "image_url" and part["image_url"]["url"].startswith("data:image/jpeg;base64,")
    ref = Image.open(io.BytesIO(base64.b64decode(part["image_url"]["url"].split(",", 1)[1])))
    assert max(ref.size) <= 1024
    assert headers["Authorization"] == f"Bearer {FAKE_KEY}"
    assert out == [tmp_path / "out" / "a_face_cand_1.png"]
    assert Image.open(out[0]).format == "PNG"
    assert prov.last_cost == 0.12 and prov.last_job.id == "gen-1" and prov.last_job.status == "done"
    assert FAKE_KEY not in repr(prov)


def test_missing_key_errors_without_leak(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY is not set"):
        openrouter.OpenRouterImage()


def test_declined_is_classified_and_key_not_in_error(tmp_path, monkeypatch, key):
    monkeypatch.setattr(openrouter, "_post", FakeHTTP([(400, {"error": {"message": "rejected by the safety system"}})]))
    prov = openrouter.OpenRouterImage()
    with pytest.raises(openrouter.OpenRouterError) as ei:
        prov.generate(ImageRequest(name="x", prompt="p"), tmp_path)
    assert ei.value.job.status == "declined" and FAKE_KEY not in str(ei.value)


def _specs(tmp_path):
    ref = _ref(tmp_path)
    return [facetest.FaceSpec("a", "诸葛青", "pa", ref), facetest.FaceSpec("b", "王也", "pb", ref)]


def test_run_ledger_and_caps(tmp_path, monkeypatch, key):
    http = FakeHTTP([_ok(0.2, f"gen-{i}") for i in range(10)])
    monkeypatch.setattr(openrouter, "_post", http)
    gate = SpendGate(tmp_path, Budget(cap_usd=100))
    prov = openrouter.OpenRouterImage()
    res = facetest.run_facetest(tmp_path, gate, prov, _specs(tmp_path), n=4, cap_usd=100, max_images=3,
                                est_usd=0.3, log=lambda *_: None)
    assert len(http.calls) == 3 and res.images == 3 and "image limit" in res.stopped
    names = sorted(p.name for p in (tmp_path / "refs" / "candidates").glob("*.png"))
    assert names == ["a_face_cand_1.png", "a_face_cand_2.png", "b_face_cand_1.png"]
    recs = [json.loads(ln) for ln in (tmp_path / "ledger.jsonl").read_text().splitlines()]
    assert [r["real_usd"] for r in recs] == [0.2, 0.2, 0.2]
    assert all(r["provider"] == "openrouter" and r["kind"] == "image" and r["tag"] == facetest.TAG for r in recs)
    assert FAKE_KEY not in (tmp_path / "ledger.jsonl").read_text()
    # a second run shares the caps from the ledger and refuses before calling
    res2 = facetest.run_facetest(tmp_path, gate, prov, _specs(tmp_path), n=1, cap_usd=100, max_images=3,
                                 log=lambda *_: None)
    assert len(http.calls) == 3 and res2.stopped
    assert not (tmp_path / "refs" / "a_face.png").exists()


def test_cap_refuses_next_call_and_failures_are_recorded(tmp_path, monkeypatch, key):
    http = FakeHTTP([(502, {"error": {"message": "upstream error"}}), _ok(0.5), _ok(0.5)])
    monkeypatch.setattr(openrouter, "_post", http)
    gate = SpendGate(tmp_path, Budget(cap_usd=100))
    res = facetest.run_facetest(tmp_path, gate, openrouter.OpenRouterImage(), _specs(tmp_path), n=4, cap_usd=1.0,
                                max_images=8, est_usd=0.3, log=lambda *_: None)
    # failed (not billed) + 0.5 + 0.5 = 1.0 spent; next call (1.0 + 0.3 > 1.0) refused
    assert len(http.calls) == 3 and "run cap" in res.stopped and res.spent_usd == pytest.approx(1.0)
    assert res.failed and res.failed[0][1] == "failed"
    recs = [json.loads(ln) for ln in (tmp_path / "ledger.jsonl").read_text().splitlines()]
    assert [r["status"] for r in recs] == ["failed", "done", "done"]
    sheet = facetest.contact_sheet(tmp_path, _specs(tmp_path))
    assert sheet.name == "face_candidates_sheet.png" and Image.open(sheet).width > 0


def _recs(tmp_path):
    return [json.loads(ln) for ln in (tmp_path / "ledger.jsonl").read_text().splitlines()]


def test_timeout_is_counted_at_estimate(tmp_path, monkeypatch, key):
    def boom(*_a, **_k):
        raise TimeoutError("timed out")

    monkeypatch.setattr(openrouter, "_post", boom)
    gate = SpendGate(tmp_path, Budget(cap_usd=100))
    res = facetest.run_facetest(tmp_path, gate, openrouter.OpenRouterImage(), _specs(tmp_path), n=4, cap_usd=1.0,
                                max_images=8, est_usd=0.3, log=lambda *_: None)
    # unknown outcome -> fail closed: 0.3 each, so after 3 calls (0.9) the next one (1.2 > 1.0) is refused
    assert len(res.failed) == 3 and "run cap" in res.stopped
    assert res.spent_usd == pytest.approx(0.9) and res.images == 3
    recs = _recs(tmp_path)
    assert all(r["status"] == "failed" and r["real_usd"] is None and r["est_usd"] == 0.3 and r["units"] == 1
               for r in recs)
    assert gate.spent() == pytest.approx(0.9)


def test_bad_image_on_200_keeps_billed_cost(tmp_path, monkeypatch, key):
    bad = (200, {"data": [{"b64_json": "!!not-base64!!"}], "usage": {"cost": 0.07}})
    monkeypatch.setattr(openrouter, "_post", FakeHTTP([bad]))
    gate = SpendGate(tmp_path, Budget(cap_usd=100))
    res = facetest.run_facetest(tmp_path, gate, openrouter.OpenRouterImage(), _specs(tmp_path)[:1], n=1,
                                cap_usd=3, max_images=8, est_usd=0.3, log=lambda *_: None)
    assert res.failed and not res.made
    (r,) = _recs(tmp_path)
    assert r["status"] == "failed" and r["real_usd"] == pytest.approx(0.07) and r["units"] == 1
    assert res.spent_usd == pytest.approx(0.07) and res.images == 1


def test_missing_cost_counts_estimate(tmp_path, monkeypatch, key):
    no_cost = (200, {"data": [{"b64_json": _png_b64()}], "usage": {}})
    monkeypatch.setattr(openrouter, "_post", FakeHTTP([no_cost]))
    gate = SpendGate(tmp_path, Budget(cap_usd=100))
    res = facetest.run_facetest(tmp_path, gate, openrouter.OpenRouterImage(), _specs(tmp_path)[:1], n=1,
                                cap_usd=3, max_images=8, est_usd=0.3, log=lambda *_: None)
    assert len(res.made) == 1 and res.made[0][2] is None
    (r,) = _recs(tmp_path)
    assert r["status"] == "done" and r["real_usd"] is None
    assert res.spent_usd == pytest.approx(0.3) and res.images == 1


def test_episode_cap_refuses(tmp_path):
    gate = SpendGate(tmp_path, Budget(cap_usd=1.0))
    (tmp_path / "ledger.jsonl").write_text(json.dumps({"est_usd": 0.5, "real_usd": 0.9, "status": "done"}) + "\n")
    with pytest.raises(SpendRefused, match="episode cap"):
        gate.check_image(0.2, 3, 8, 0, 0)


def test_frozen_budget_refuses(tmp_path):
    gate = SpendGate(tmp_path, Budget(frozen=True))
    with pytest.raises(SpendRefused, match="frozen"):
        gate.check_image(0.1, 3, 8, 0, 0)


def test_adapt_prompt_strips_mj_params():
    p = facetest.adapt_prompt("<原作图链接> front portrait of the character in the image prompt, a man --iw 1.5 "
                              "--ar 3:4 --no cgi, anime")
    assert "--" not in p and "<原作图链接>" not in p and "first input image" in p
    assert "异人之下" in p and "火影有嘻哈" in p and "Avoid: cgi, anime." in p
