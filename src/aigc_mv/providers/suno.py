"""Suno adapter – to be wired when the API spec arrives.

Contract the pipeline relies on:
- `generate(lyrics, style, title)` for verse A, then `generate(..., extend_from={clip_id, at_sec})` for B
  (two passes keep the two voices apart; see `aigc-mv ep suno`).
- `stems(job)` returns at least {"vocals": Path, "instrumental": Path} from Suno's own stem split of the
  LOCKED take (verify against the master by cross-correlation; a wrong-take stem ruins every window).
- write them to audio/song.wav, audio/vocals.wav, audio/instrumental.wav (paths in episode.yaml).

Credentials: SUNO_API_KEY / SUNO_API_BASE environment variables only.
"""

from __future__ import annotations

import os
from pathlib import Path

from aigc_mv.providers.base import Job, MusicProvider


class Suno(MusicProvider):
    name = "suno"

    def __init__(self) -> None:
        self.key = os.environ.get("SUNO_API_KEY")
        if not self.key:
            raise RuntimeError("SUNO_API_KEY is not set; use the sheets from `aigc-mv ep suno` on suno.com for now.")

    def generate(self, lyrics: str, style: str, title: str, extend_from: dict | None = None) -> Job:  # pragma: no cover
        raise NotImplementedError("Suno API not wired yet: provide the endpoint spec")

    def stems(self, job: Job, dst_dir: Path) -> dict[str, Path]:  # pragma: no cover
        raise NotImplementedError
