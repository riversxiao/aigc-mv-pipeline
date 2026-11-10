"""APIMart image adapter for GPT-Image-2.5 (asynchronous tasks).

Docs: https://docs.apimart.ai/en/api-reference/images/gpt-image-2.5/generation (+ uploads/images, tasks/status)
- reference images must be public URLs: each local ref is downscaled to <= REF_MAX_PX, uploaded once with
  POST /v1/uploads/images (multipart field `file`, reply {"url": ...}, kept 72 h) and cached per process;
- submit POST /v1/images/generations {"model", "prompt", "size": "3:4", "resolution": "1k", "quality", "n": 1,
  "output_format": "png", "image_urls": [...]}; reply {"data": [{"task_id"}]};
- poll GET /v1/tasks/<id> every POLL_S until "completed" / "failed"; images in data.result.images[].url[] are
  temporary, so they are downloaded at once; the task reply carries the real charge in data.cost (USD).

Billing and failure rules (the ledger fails closed):
- an HTTP error on upload or submit means nothing was generated: ApiMartError with .job, last_cost=0.0;
- a task that ends "failed" is refunded by APIMart: ApiMartError with .job, last_cost=0.0;
- anything after an accepted submit that leaves the outcome unknown (poll timeout, transport error, poll HTTP
  error, a completed task whose image cannot be downloaded) raises a plain exception with no .job, so the caller
  counts it as possibly billed; last_cost is the reported data.cost when it was read, else None.

The key is read from APIMART_API_KEY only. It is never logged, stored, or put into an exception message.
"""

from __future__ import annotations

import io
import json
import os
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from PIL import Image

from aigc_mv.providers.base import ImageProvider, ImageRequest, Job

BASE_URL = "https://api.apimart.ai"
DEFAULT_MODEL = "gpt-image-2.5-sunburst"
REF_MAX_PX = 1024
POLL_S = 3.0
TASK_TIMEOUT_S = 300.0
EST_USD = 0.08  # per-image reservation against a cap (about 2x the documented 1k high output price)
# documented per-1M-token prices, used only when a reply has token counts but no cost
PRICE_PER_M = {"output": 30.0, "image_input": 8.0, "text_input": 5.0}
_DECLINE_WORDS = ("moderation", "safety", "content policy", "policy", "refus", "rejected", "not allowed",
                  "sensitive", "violat")
_RETRY_HTTP = (429, 500, 502, 503, 504)


class ApiMartError(RuntimeError):
    """An APIMart reply that settles the request as not billed (HTTP error before the task, or a failed task)."""

    def __init__(self, msg: str, job: Job):
        super().__init__(msg)
        self.job = job


def _request(method: str, url: str, headers: dict, data: bytes | None, timeout: float) -> tuple[int, bytes]:
    """One HTTP call, return (status, raw body). HTTP errors come back as (code, body). Patched in tests."""
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def _json(raw: bytes) -> dict:
    try:
        v = json.loads(raw.decode(errors="replace") or "{}")
    except ValueError:
        return {"error": {"message": raw[:500].decode(errors="replace")}}
    return v if isinstance(v, dict) else {"data": v}


def _error_text(body: dict) -> str:
    err = body.get("error") if isinstance(body, dict) else None
    if isinstance(err, dict):
        return str(err.get("message") or err)[:500]
    if err:
        return str(err)[:500]
    return json.dumps(body, ensure_ascii=False)[:500]


def _kind(text: str) -> str:
    return "declined" if any(w in text.lower() for w in _DECLINE_WORDS) else "failed"


def ref_jpeg(path: Path, max_px: int = REF_MAX_PX) -> bytes:
    im = Image.open(path).convert("RGB")
    im.thumbnail((max_px, max_px), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=92)
    return buf.getvalue()


def cost_from(data: dict) -> float | None:
    """Real USD charge of a task reply: data.cost, else a token estimate from usage, else None."""
    if not isinstance(data, dict):
        return None
    if data.get("cost") is not None:
        try:
            return float(data["cost"])
        except (TypeError, ValueError):
            pass
    u = data.get("usage") or {}
    if isinstance(u, dict) and (u.get("output_tokens") is not None):
        det = u.get("input_tokens_details") or {}
        img_in = float(det.get("image_tokens") or 0)
        txt_in = float(det.get("text_tokens") or max(0.0, float(u.get("input_tokens") or 0) - img_in))
        return (float(u["output_tokens"]) * PRICE_PER_M["output"] + img_in * PRICE_PER_M["image_input"]
                + txt_in * PRICE_PER_M["text_input"]) / 1e6
    return None


class ApiMartImage(ImageProvider):
    name = "apimart"
    _uploads: dict[tuple, str] = {}  # (path, mtime, size) -> public url, shared by workers (URLs live 72 h)
    _uploads_lock = threading.Lock()

    def __init__(self, model: str = DEFAULT_MODEL, quality: str = "high", resolution: str = "1k",
                 timeout: float = 60.0, task_timeout: float = TASK_TIMEOUT_S, poll_s: float = POLL_S,
                 base_url: str = BASE_URL, sleep=time.sleep, clock=time.monotonic):
        key = os.environ.get("APIMART_API_KEY")
        if not key:
            raise RuntimeError("APIMART_API_KEY is not set (pass it in the environment of this one command)")
        self._key = key
        self.model, self.quality, self.resolution = model, quality, resolution
        self.timeout, self.task_timeout, self.poll_s = timeout, task_timeout, poll_s
        self.base = base_url.rstrip("/")
        self._sleep, self._clock = sleep, clock
        self.last_job: Job | None = None
        self.last_cost: float | None = None

    def __repr__(self) -> str:  # never show the key
        return f"ApiMartImage(model={self.model!r})"

    def _auth(self) -> dict:
        return {"Authorization": f"Bearer {self._key}"}

    # ---- steps ----
    def upload(self, path: Path) -> str:
        path = Path(path)
        st = path.stat()
        ck = (str(path.resolve()), st.st_mtime_ns, st.st_size)
        with self._uploads_lock:
            if ck in self._uploads:
                return self._uploads[ck]
        boundary = uuid.uuid4().hex
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.stem}.jpg\"\r\n"
                f"Content-Type: image/jpeg\r\n\r\n").encode() + ref_jpeg(path) + f"\r\n--{boundary}--\r\n".encode()
        headers = {**self._auth(), "Content-Type": f"multipart/form-data; boundary={boundary}"}
        status, raw = _request("POST", f"{self.base}/v1/uploads/images", headers, body, self.timeout)
        res = _json(raw)
        url = res.get("url")
        if not url and isinstance(res.get("data"), dict):
            url = res["data"].get("url")
        if status >= 400 or not url:
            text = _error_text(res)
            job = Job(id=f"upload-{path.name}", status="failed", raw={"http": status, "error": text, "step": "upload"})
            raise ApiMartError(f"APIMart upload failed (HTTP {status}): {text}", job)
        with self._uploads_lock:
            self._uploads[ck] = url
        return url

    def body(self, req: ImageRequest, image_urls: list[str]) -> dict:
        b = {"model": self.model, "prompt": req.prompt, "size": req.aspect_ratio, "resolution": self.resolution,
             "quality": self.quality, "n": 1, "output_format": "png"}
        if image_urls:
            b["image_urls"] = image_urls
        return b

    def submit(self, body: dict) -> str:
        headers = {**self._auth(), "Content-Type": "application/json"}
        status, raw = _request("POST", f"{self.base}/v1/images/generations", headers,
                               json.dumps(body).encode(), self.timeout)
        res = _json(raw)
        data = res.get("data")
        tid = data[0].get("task_id") if isinstance(data, list) and data and isinstance(data[0], dict) else None
        if status >= 400 or res.get("error") or not tid:
            text = _error_text(res)
            job = Job(id=f"local-{int(time.time() * 1000)}", status=_kind(text),
                      raw={"http": status, "error": text, "step": "submit"})
            raise ApiMartError(f"APIMart {job.status} (HTTP {status}): {text}", job)
        return str(tid)

    def wait(self, task_id: str) -> dict:
        """Poll until completed / failed or the task timeout. Returns data of the completed task."""
        deadline = self._clock() + self.task_timeout
        last = "submitted"
        while True:
            try:
                status, raw = _request("GET", f"{self.base}/v1/tasks/{task_id}?language=en", self._auth(), None,
                                       self.timeout)
            except (OSError, TimeoutError) as e:  # transient transport error: retry until the deadline
                status, raw = -1, str(e).encode()
            res = _json(raw) if status != -1 else {}
            if status >= 400 and status not in _RETRY_HTTP:
                raise RuntimeError(f"APIMart task {task_id}: poll HTTP {status}: {_error_text(res)} "
                                   "(outcome unknown, counted as possibly billed)")
            data = res.get("data") if isinstance(res.get("data"), dict) else {}
            st = str(data.get("status") or "")
            if st:
                last = st
            if st == "completed":
                return data
            if st == "failed":
                err = data.get("error") or data.get("fail_reason") or data
                text = (err.get("message") if isinstance(err, dict) else str(err)) or "failed"
                job = Job(id=task_id, status=_kind(str(text)), raw={"error": str(text)[:500], "step": "task"})
                raise ApiMartError(f"APIMart task {job.status} (refunded): {str(text)[:500]}", job)
            if self._clock() >= deadline:
                raise TimeoutError(f"APIMart task {task_id}: no result after {self.task_timeout:.0f}s "
                                   f"(last status {last}; counted as possibly billed)")
            self._sleep(self.poll_s)

    def download(self, url: str) -> bytes:
        status, raw = _request("GET", url, {}, None, self.timeout)
        if status >= 400:
            raise RuntimeError(f"APIMart image download HTTP {status}")
        return raw

    # ---- interface ----
    def generate(self, req: ImageRequest, dst_dir: Path) -> list[Path]:
        """One task; saves PNGs as dst_dir/<req.name>.png (…_2.png for extras). Sets last_job / last_cost."""
        self.last_job, self.last_cost = None, None
        try:
            urls = [self.upload(p) for p in req.refs]
            task_id = self.submit(self.body(req, urls))
        except ApiMartError as e:
            self.last_job, self.last_cost = e.job, 0.0
            raise
        try:
            data = self.wait(task_id)
        except ApiMartError as e:
            self.last_job, self.last_cost = e.job, 0.0
            raise
        self.last_cost = cost_from(data)
        imgs = (data.get("result") or {}).get("images") or []
        links = []
        for im in imgs:
            u = im.get("url") if isinstance(im, dict) else None
            links.extend(x for x in (u if isinstance(u, list) else [u]) if x)
        if not links:
            raise RuntimeError(f"APIMart task {task_id} completed without image URLs")
        dst_dir = Path(dst_dir)
        dst_dir.mkdir(parents=True, exist_ok=True)
        out = []
        for i, link in enumerate(links):
            raw = self.download(link)
            p = dst_dir / (f"{req.name}.png" if i == 0 else f"{req.name}_{i + 1}.png")
            Image.open(io.BytesIO(raw)).save(p, "PNG")
            out.append(p)
        self.last_job = Job(id=task_id, status="done",
                            raw={"cost": data.get("cost"), "credits_cost": data.get("credits_cost"),
                                 "usage": data.get("usage"), "actual_time": data.get("actual_time"),
                                 "images": len(out)})
        return out
