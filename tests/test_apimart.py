"""APIMart GPT-Image-2.5 adapter with the HTTP layer mocked (no network), plus run_batch ledger handling."""

import io
import json
from pathlib import Path

import pytest
from PIL import Image

from aigc_mv import refbatch as rb
from aigc_mv.episode import Budget
from aigc_mv.providers import apimart
from aigc_mv.providers.base import ImageRequest, SpendGate

FAKE_KEY = "test-key-not-real-456"
BASE = "https://api.apimart.ai"


def _png(size=(48, 64)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (10, 120, 10)).save(buf, "PNG")
    return buf.getvalue()


def _ref(tmp: Path, name="venue.png") -> Path:
    p = tmp / name
    Image.new("RGB", (2000, 1125), (120, 0, 0)).save(p, "PNG")
    return p


def _j(obj) -> bytes:
    return json.dumps(obj).encode()


class FakeHTTP:
    """Routes by (method, url prefix); each route has a list of replies, the last one repeats."""

    def __init__(self, routes):
        self.routes = {k: list(v) for k, v in routes.items()}
        self.calls = []

    def __call__(self, method, url, headers, data, timeout):
        self.calls.append((method, url, headers, data))
        for (m, prefix), replies in self.routes.items():
            if m == method and url.startswith(prefix):
                r = replies.pop(0) if len(replies) > 1 else replies[0]
                if isinstance(r, Exception):
                    raise r
                return r
        raise AssertionError(f"unexpected call {method} {url}")


def _routes(task_replies, upload=(200, _j({"url": "https://upload.apimart.ai/f/image/ref.jpg"})),
            submit=(200, _j({"code": 200, "data": [{"status": "submitted", "task_id": "task_1"}]}))):
    return {("POST", f"{BASE}/v1/uploads/images"): [upload],
            ("POST", f"{BASE}/v1/images/generations"): [submit],
            ("GET", f"{BASE}/v1/tasks/"): task_replies,
            ("GET", "https://upload.apimart.ai/f/image/out"): [(200, _png())]}


def _done(cost=0.041):
    return 200, _j({"code": 200, "data": {"id": "task_1", "status": "completed", "cost": cost, "progress": 100,
                                          "result": {"images": [{"url": ["https://upload.apimart.ai/f/image/out_0.png"],
                                                                 "expires_at": 1}]}}})


def _status(st):
    return 200, _j({"code": 200, "data": {"id": "task_1", "status": st, "progress": 10}})


@pytest.fixture(autouse=True)
def key(monkeypatch):
    monkeypatch.setenv("APIMART_API_KEY", FAKE_KEY)
    apimart.ApiMartImage._uploads.clear()


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


def _prov(**kw):
    c = Clock()
    return apimart.ApiMartImage(sleep=c.sleep, clock=c, **kw), c


def test_upload_submit_poll_download(tmp_path, monkeypatch):
    http = FakeHTTP(_routes([_status("submitted"), _status("processing"), _done()]))
    monkeypatch.setattr(apimart, "_request", http)
    prov, _ = _prov()
    out = prov.generate(ImageRequest("venue_high_cand_1", "p", "16:9", [_ref(tmp_path)]), tmp_path / "c")
    assert [p.name for p in out] == ["venue_high_cand_1.png"] and Image.open(out[0]).size == (48, 64)
    up = http.calls[0]
    assert up[1].endswith("/v1/uploads/images") and b'name="file"' in up[3] and b"image/jpeg" in up[3]
    assert up[2]["Authorization"] == f"Bearer {FAKE_KEY}"
    body = json.loads(http.calls[1][3])
    assert body == {"model": "gpt-image-2.5-sunburst", "prompt": "p", "size": "16:9", "resolution": "1k",
                    "quality": "high", "n": 1, "output_format": "png",
                    "image_urls": ["https://upload.apimart.ai/f/image/ref.jpg"]}
    assert sum(1 for c in http.calls if "/v1/tasks/task_1" in c[1]) == 3
    assert prov.last_cost == pytest.approx(0.041) and prov.last_job.status == "done" and prov.last_job.id == "task_1"
    assert FAKE_KEY not in repr(prov)


def test_upload_is_cached_and_downscaled(tmp_path, monkeypatch):
    http = FakeHTTP(_routes([_done()]))
    monkeypatch.setattr(apimart, "_request", http)
    ref = _ref(tmp_path)
    prov, _ = _prov()
    prov.generate(ImageRequest("x_cand_1", "p", "16:9", [ref]), tmp_path)
    prov.generate(ImageRequest("x_cand_2", "p", "16:9", [ref]), tmp_path)
    ups = [c for c in http.calls if c[1].endswith("/uploads/images")]
    assert len(ups) == 1
    jpg = ups[0][3].split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n--", 1)[0]
    assert max(Image.open(io.BytesIO(jpg)).size) == 1024


def test_text_to_image_has_no_image_urls(tmp_path, monkeypatch):
    http = FakeHTTP(_routes([_done()]))
    monkeypatch.setattr(apimart, "_request", http)
    prov, _ = _prov()
    prov.generate(ImageRequest("chulan_face_cand_1", "p", "3:4"), tmp_path)
    body = json.loads(next(c for c in http.calls if c[1].endswith("/generations"))[3])
    assert "image_urls" not in body and body["size"] == "3:4"
    assert not any(c[1].endswith("/uploads/images") for c in http.calls)


def test_submit_http_error_is_unbilled_with_job(tmp_path, monkeypatch):
    http = FakeHTTP(_routes([_done()], submit=(402, _j({"error": {"code": 402, "message": "Insufficient balance"}}))))
    monkeypatch.setattr(apimart, "_request", http)
    prov, _ = _prov()
    with pytest.raises(apimart.ApiMartError) as e:
        prov.generate(ImageRequest("x", "p"), tmp_path)
    assert e.value.job.status == "failed" and prov.last_cost == 0.0 and "402" in str(e.value)
    assert FAKE_KEY not in str(e.value)


def test_upload_error_is_unbilled(tmp_path, monkeypatch):
    http = FakeHTTP(_routes([_done()], upload=(413, _j({"error": {"message": "file too large"}}))))
    monkeypatch.setattr(apimart, "_request", http)
    prov, _ = _prov()
    with pytest.raises(apimart.ApiMartError) as e:
        prov.generate(ImageRequest("x", "p", refs=[_ref(tmp_path)]), tmp_path)
    assert e.value.job is not None and prov.last_cost == 0.0
    assert not any(c[1].endswith("/generations") for c in http.calls)


def test_failed_task_is_refunded_and_declines_are_named(tmp_path, monkeypatch):
    failed = 200, _j({"data": {"id": "task_1", "status": "failed",
                               "error": {"message": "Request rejected by the safety system"}}})
    http = FakeHTTP(_routes([_status("processing"), failed]))
    monkeypatch.setattr(apimart, "_request", http)
    prov, _ = _prov()
    with pytest.raises(apimart.ApiMartError) as e:
        prov.generate(ImageRequest("x", "p"), tmp_path)
    assert e.value.job.status == "declined" and e.value.job.id == "task_1" and prov.last_cost == 0.0


def test_poll_timeout_fails_closed(tmp_path, monkeypatch):
    http = FakeHTTP(_routes([_status("processing")]))
    monkeypatch.setattr(apimart, "_request", http)
    prov, clock = _prov(task_timeout=30, poll_s=3)
    with pytest.raises(TimeoutError) as e:
        prov.generate(ImageRequest("x", "p"), tmp_path)
    assert not hasattr(e.value, "job") and prov.last_cost is None
    assert 30 <= clock.t <= 33


def test_transient_poll_errors_retry_then_complete(tmp_path, monkeypatch):
    http = FakeHTTP(_routes([(502, b"bad gateway"), TimeoutError("read timed out"), _done(cost=0.05)]))
    monkeypatch.setattr(apimart, "_request", http)
    prov, _ = _prov()
    assert prov.generate(ImageRequest("x", "p"), tmp_path) and prov.last_cost == pytest.approx(0.05)


def test_poll_client_error_fails_closed(tmp_path, monkeypatch):
    http = FakeHTTP(_routes([(400, _j({"error": {"message": "Invalid task ID"}}))]))
    monkeypatch.setattr(apimart, "_request", http)
    prov, _ = _prov()
    with pytest.raises(RuntimeError) as e:
        prov.generate(ImageRequest("x", "p"), tmp_path)
    assert not isinstance(e.value, apimart.ApiMartError)


def test_download_failure_keeps_reported_cost(tmp_path, monkeypatch):
    routes = _routes([_done(cost=0.04)])
    routes[("GET", "https://upload.apimart.ai/f/image/out")] = [(404, b"gone")]
    monkeypatch.setattr(apimart, "_request", FakeHTTP(routes))
    prov, _ = _prov()
    with pytest.raises(RuntimeError):
        prov.generate(ImageRequest("x", "p"), tmp_path)
    assert prov.last_cost == pytest.approx(0.04)


def test_cost_from_tokens_when_no_cost_field():
    data = {"usage": {"output_tokens": 1204, "input_tokens": 1300,
                      "input_tokens_details": {"image_tokens": 1000, "text_tokens": 300}}}
    assert apimart.cost_from(data) == pytest.approx((1204 * 30 + 1000 * 8 + 300 * 5) / 1e6)
    assert apimart.cost_from({"status": "completed"}) is None


def test_missing_key(monkeypatch):
    monkeypatch.delenv("APIMART_API_KEY")
    with pytest.raises(RuntimeError, match="APIMART_API_KEY"):
        apimart.ApiMartImage()


def test_run_batch_ledger_with_apimart_tag(tmp_path, monkeypatch):
    failed = 200, _j({"data": {"id": "task_1", "status": "failed", "error": {"message": "upstream error"}}})
    http = FakeHTTP(_routes([_done(cost=0.04), failed, _status("processing")]))
    monkeypatch.setattr(apimart, "_request", http)
    gate = SpendGate(tmp_path, Budget(cap_usd=100))
    gate.record("openrouter", "m", "image", 1, 0.12, apimart.Job(id="old", status="done"), real_usd=2.9, tag=rb.TAG)
    items = [rb.Item("venue_high.png", "高位", "p", "16:9", [])]
    c = Clock()
    res = rb.run_batch(tmp_path, gate, lambda: apimart.ApiMartImage(sleep=c.sleep, clock=c, task_timeout=9),
                       items, n=3, cap_usd=4.0, max_images=10, est_usd=0.08, tag="refs-batch-apimart", log=lambda *_: 0)
    recs = gate.entries("refs-batch-apimart")
    assert [r["status"] for r in recs] == ["done", "failed", "failed"]
    assert [r["units"] for r in recs] == [1, 0, 1]
    assert recs[0]["real_usd"] == pytest.approx(0.04) and recs[1]["real_usd"] == 0.0 and recs[2]["real_usd"] is None
    assert res.spent_usd == pytest.approx(0.04 + 0.08) and res.images == 2
    assert gate.tag_totals(rb.TAG) == (2.9, 1)  # the OpenRouter series is not counted against this run's cap
    assert all(FAKE_KEY not in ln for ln in gate.ledger.read_text().splitlines())
