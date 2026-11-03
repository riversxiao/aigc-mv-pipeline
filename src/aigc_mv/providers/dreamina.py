"""Dreamina / 即梦 (Seedance video + Seedream image) adapter – to be wired when the API spec arrives.

What the adapter must do (and what the rest of the pipeline already assumes):
- `submit`: one request per board unit. Sung units use REFERENCE mode (images + @音频1), not first-frame
  mode: on some providers a first frame silently drops the audio reference. Motion units may send a
  first frame (refs/plate_<unit>.png).
- duration / resolution / aspect ratio go in request fields, never in the prompt text.
- images are downscaled to the output size and sent as PNG (full-size stills cause fingerprint textures).
- audio must usually be an HTTPS URL; upload the window first if the API needs it.
- return the provider's job id; never resubmit a request that already got one.
- `download` saves into units/<unit>/takes/take-N.mp4, after which `aigc-mv ep sync` measures it.

Credentials: environment variables only (DREAMINA_API_KEY, DREAMINA_API_BASE, …).
"""

from __future__ import annotations

import os
from pathlib import Path

from aigc_mv.providers.base import ImageProvider, ImageRequest, Job, VideoProvider, VideoRequest


class DreaminaVideo(VideoProvider):
    name = "dreamina"
    price_per_sec_usd = float(os.environ.get("DREAMINA_PRICE_PER_SEC", "0.23"))

    def __init__(self) -> None:
        self.key = os.environ.get("DREAMINA_API_KEY")
        self.base = os.environ.get("DREAMINA_API_BASE", "")
        if not self.key:
            raise RuntimeError("DREAMINA_API_KEY is not set. Until the API is wired, use `aigc-mv ep packs` "
                               "and generate on the 即梦 web app.")

    def submit(self, req: VideoRequest) -> Job:  # pragma: no cover - awaiting API spec
        raise NotImplementedError("Dreamina video API not wired yet: provide the endpoint spec")

    def poll(self, job: Job) -> Job:  # pragma: no cover
        raise NotImplementedError

    def download(self, job: Job, dst: Path) -> Path:  # pragma: no cover
        raise NotImplementedError


class DreaminaImage(ImageProvider):
    name = "dreamina-image"

    def generate(self, req: ImageRequest, dst_dir: Path) -> list[Path]:  # pragma: no cover
        raise NotImplementedError("Dreamina image API not wired yet")
