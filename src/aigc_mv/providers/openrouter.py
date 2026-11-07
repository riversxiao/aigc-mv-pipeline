"""OpenRouter image adapter (dedicated Image API: POST /api/v1/images).

Request (https://openrouter.ai/docs/guides/overview/multimodal/image-generation):
    {"model", "prompt", "n", "aspect_ratio", "quality", "input_references": [{"type": "image_url",
     "image_url": {"url": "data:image/jpeg;base64,..."}}]}
Response: {"data": [{"b64_json", "media_type"}], "usage": {"cost": <USD>, ...}}. Billing is all-or-nothing:
generations that come back as an HTTP error are not billed (OpenRouterError, last_cost=0.0). Client-side failures
after the server accepted the request (timeout, connection drop, undecodable image on a 200) may still be billed:
those raise other exceptions, with last_cost set to usage.cost when the response was read, else None.

The key is read from OPENROUTER_API_KEY only. It is never logged, stored, or put into an exception message.
"""

from __future__ import annotations

import base64
import io
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

from aigc_mv.providers.base import ImageProvider, ImageRequest, Job

API_URL = "https://openrouter.ai/api/v1/images"
DEFAULT_MODEL = "openai/gpt-image-2.5-sunburst"
REF_MAX_PX = 1024
_DECLINE_WORDS = ("moderation", "safety", "content policy", "policy", "refus", "rejected", "not allowed")


class OpenRouterError(RuntimeError):
    def __init__(self, msg: str, job: Job):
        super().__init__(msg)
        self.job = job


def _post(url: str, body: dict, headers: dict, timeout: float) -> tuple[int, dict]:
    """POST JSON, return (status, parsed body). Patched in tests (no network there)."""
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, {"error": {"message": raw[:500]}}


def ref_data_url(path: Path, max_px: int = REF_MAX_PX) -> str:
    """Reference image downscaled to <= max_px on the long side, as a JPEG data URL."""
    im = Image.open(path).convert("RGB")
    im.thumbnail((max_px, max_px), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=92)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def _error_text(body: dict) -> str:
    err = body.get("error") if isinstance(body, dict) else None
    if isinstance(err, dict):
        msg = str(err.get("message") or err)
        meta = err.get("metadata")
        if meta:
            msg += f" {json.dumps(meta, ensure_ascii=False)[:400]}"
        return msg
    return str(err or body)[:500]


class OpenRouterImage(ImageProvider):
    name = "openrouter"

    def __init__(self, model: str = DEFAULT_MODEL, quality: str = "high", timeout: float = 300.0):
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY is not set (pass it in the environment of this one command)")
        self._key = key
        self.model = model
        self.quality = quality
        self.timeout = timeout
        self.last_job: Job | None = None
        self.last_cost: float | None = None

    def __repr__(self) -> str:  # never show the key
        return f"OpenRouterImage(model={self.model!r})"

    def body(self, req: ImageRequest) -> dict:
        body = {"model": self.model, "prompt": req.prompt, "n": 1, "aspect_ratio": req.aspect_ratio,
                "quality": self.quality}
        if req.refs:
            body["input_references"] = [{"type": "image_url", "image_url": {"url": ref_data_url(p)}}
                                        for p in req.refs]
        return body

    def generate(self, req: ImageRequest, dst_dir: Path) -> list[Path]:
        """One request; saves PNGs as dst_dir/<req.name>.png (…_2.png for extras). Sets last_job / last_cost."""
        self.last_job, self.last_cost = None, None
        headers = {"Authorization": f"Bearer {self._key}", "Content-Type": "application/json",
                   "X-Title": "aigc-mv-pipeline"}
        status, res = _post(API_URL, self.body(req), headers, self.timeout)
        gen_id = str(res.get("id") or f"local-{int(time.time() * 1000)}") if isinstance(res, dict) else "local"
        if status >= 400 or not isinstance(res, dict) or res.get("error") or not res.get("data"):
            text = _error_text(res) if isinstance(res, dict) else str(res)[:500]
            kind = "declined" if any(w in text.lower() for w in _DECLINE_WORDS) else "failed"
            job = Job(id=gen_id, status=kind, raw={"http": status, "error": text})
            self.last_job, self.last_cost = job, 0.0
            raise OpenRouterError(f"OpenRouter {kind} (HTTP {status}): {text}", job)
        cost = (res.get("usage") or {}).get("cost")
        self.last_cost = float(cost) if cost is not None else None
        dst_dir = Path(dst_dir)
        dst_dir.mkdir(parents=True, exist_ok=True)
        out = []
        for i, item in enumerate(res["data"]):
            raw = base64.b64decode(item["b64_json"])
            p = dst_dir / (f"{req.name}.png" if i == 0 else f"{req.name}_{i + 1}.png")
            Image.open(io.BytesIO(raw)).save(p, "PNG")
            out.append(p)
        self.last_job = Job(id=gen_id, status="done", raw={"usage": res.get("usage"), "images": len(out)})
        return out
