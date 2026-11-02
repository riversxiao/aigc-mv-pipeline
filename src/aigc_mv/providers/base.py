"""Provider interfaces + the spend gate every paid call goes through.

Spending rules (claudia.gallery, learned the expensive way):
- estimate = planned seconds × price × 2 (takes ran ~2× the seconds that reach the cut);
- nothing is submitted without an approval that covers that exact prompt (hash);
- a hard cap enforced in code, plus `budget.frozen` as the stop switch;
- one ledger line per paid call; quote real spend only from the provider's bill.
API keys come from environment variables only, never from files in the repo.
"""

from __future__ import annotations

import hashlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from aigc_mv.episode import Budget


@dataclass
class VideoRequest:
    unit: str
    prompt: str
    duration: int
    images: list[Path] = field(default_factory=list)
    audio: Path | None = None
    first_frame: Path | None = None
    resolution: str = "720p"
    aspect_ratio: str = "16:9"
    model: str = "seedance"

    def digest(self) -> str:
        h = hashlib.sha256()
        h.update(self.prompt.encode())
        h.update(f"{self.duration}|{self.resolution}|{self.aspect_ratio}|{self.model}".encode())
        for p in [*self.images, self.audio, self.first_frame]:
            if p:
                h.update(str(p).encode())
        return h.hexdigest()[:16]


@dataclass
class ImageRequest:
    name: str
    prompt: str
    aspect_ratio: str = "16:9"
    refs: list[Path] = field(default_factory=list)


@dataclass
class Job:
    id: str
    status: str = "submitted"  # submitted | running | done | failed | declined
    url: str | None = None
    raw: dict = field(default_factory=dict)


class VideoProvider(ABC):
    name = "base"
    price_per_sec_usd = 0.0

    @abstractmethod
    def submit(self, req: VideoRequest) -> Job: ...

    @abstractmethod
    def poll(self, job: Job) -> Job: ...

    @abstractmethod
    def download(self, job: Job, dst: Path) -> Path: ...


class ImageProvider(ABC):
    name = "base"

    @abstractmethod
    def generate(self, req: ImageRequest, dst_dir: Path) -> list[Path]: ...


class MusicProvider(ABC):
    name = "base"

    @abstractmethod
    def generate(self, lyrics: str, style: str, title: str, extend_from: dict | None = None) -> Job: ...

    @abstractmethod
    def stems(self, job: Job, dst_dir: Path) -> dict[str, Path]: ...


class SpendRefused(RuntimeError):
    pass


class SpendGate:
    """Approvals + cap + ledger, stored in the project folder."""

    def __init__(self, project_dir: Path, budget: Budget):
        self.dir = Path(project_dir)
        self.budget = budget
        self.ledger = self.dir / "ledger.jsonl"
        self.approvals = self.dir / "approvals.json"

    def spent(self) -> float:
        if not self.ledger.is_file():
            return 0.0
        total = 0.0
        for line in self.ledger.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                total += float(rec.get("real_usd") or rec.get("est_usd") or 0)
        return total

    def approved(self) -> dict:
        if self.approvals.is_file():
            return json.loads(self.approvals.read_text(encoding="utf-8"))
        return {}

    def approve(self, unit: str, digest: str) -> None:
        a = self.approved()
        a[unit] = digest
        self.approvals.write_text(json.dumps(a, indent=2) + "\n", encoding="utf-8")

    def check(self, req: VideoRequest, price_per_sec: float) -> float:
        if self.budget.frozen:
            raise SpendRefused("budget.frozen is true")
        if self.approved().get(req.unit) != req.digest():
            raise SpendRefused(f"{req.unit}: prompt not approved (run `aigc-mv ep approve` after reading it)")
        est = req.duration * price_per_sec
        if self.spent() + est > self.budget.cap_usd:
            raise SpendRefused(f"cap ${self.budget.cap_usd:.2f} would be exceeded (spent ${self.spent():.2f} + ${est:.2f})")
        return est

    def record(self, provider: str, model: str, kind: str, units: float, est_usd: float, job: Job,
               real_usd: float | None = None) -> None:
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "provider": provider, "model": model, "kind": kind,
               "units": units, "est_usd": round(est_usd, 4), "real_usd": real_usd, "request_id": job.id,
               "status": job.status}
        with self.ledger.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
