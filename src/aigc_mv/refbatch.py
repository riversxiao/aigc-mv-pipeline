"""Paid reference batches under hard caps: environment plates, step-2 views, step-1 portraits for any cast key.

Prompts and uploads come from refs/refs_plan.json (written by `aigc-mv ep refs`):
- plates: the plate entry's `gpt` prompt; its upload (venue.png / venue_high.png) must already be locked in refs/;
- step 2: the `<key>_<view>.png` entry, with the locked refs/<key>_face.png as the first input image;
- step 1: the `<key>_face.png` entry, with the canon art as the first input image when the card has one (else
  text-to-image), and an age rule taken from the card (old judges must look old).

Candidates go to refs/candidates/<stem>_cand_<n>.png. Nothing is promoted to refs/<file> automatically: `lock`
copies one candidate and records who picked it and why in refs/candidates/picks.json. It never replaces a locked
file it did not write, nor one a user picked, unless force=True.

Spend and image count are counted from ledger.jsonl lines tagged TAG, so all runs of the series share one cap.
Requests can run in a few threads; a lock reserves the estimate of every in-flight call before it starts, so the
cap holds with concurrency too.
"""

from __future__ import annotations

import json
import re
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from aigc_mv.episode import Episode
from aigc_mv.facetest import adapt_prompt
from aigc_mv.providers.base import ImageRequest, Job, SpendGate, SpendRefused

TAG = "refs-batch"
EST_USD = 0.12  # per-image reservation against the cap (2x the measured $0.055-0.060); real cost is usage.cost
STEP2_VIEWS = ("34", "profile", "half", "full")
VIEW_CN = {"face": "正面", "34": "四分之三侧", "profile": "侧面", "half": "半身持麦", "full": "全身", "expr": "表情"}
FONT = Path.home() / ".cache" / "aigc-mv" / "fonts" / "NotoSansSC.ttf"

NO_LIKENESS = ("The face must be an original face: it must not resemble any real celebrity or actor, in particular "
               "any cast member of the live-action adaptation \u300a\u5f02\u4eba\u4e4b\u4e0b\u300b (Under One "
               "Person), and must not copy any face from the AI show \u300a\u706b\u5f71\u6709\u563b\u54c8\u300b.")


@dataclass
class Item:
    file: str               # locked target in refs/, e.g. venue.png, a_34.png, chulan_face.png
    label: str              # Chinese label for sheets and logs
    prompt: str
    aspect: str
    refs: list[Path] = field(default_factory=list)
    group: str = ""         # plates | step2 | step1
    n: int | None = None    # candidates for this item (None: the run's n)

    @property
    def stem(self) -> str:
        return self.file.removesuffix(".png")


@dataclass
class BatchResult:
    made: list[tuple[str, Path, float | None]] = field(default_factory=list)
    failed: list[tuple[str, str, str]] = field(default_factory=list)  # file, status, message
    stopped: str | None = None
    spent_usd: float = 0.0
    images: int = 0


def _plan(ep_dir: Path) -> list[dict]:
    p = Path(ep_dir) / "refs" / "refs_plan.json"
    if not p.is_file():
        raise FileNotFoundError(f"{p} missing: run `aigc-mv ep refs {ep_dir}` first")
    return json.loads(p.read_text(encoding="utf-8"))


def _strip_mj(en: str) -> tuple[str, str]:
    """(prompt without MJ params, the --no list)."""
    m = re.search(r"\s--(iw|oref|ow|ar|style|stylize|sref|no)\b", en)
    if not m:
        return en.strip().rstrip(", "), ""
    n = re.search(r"--no\s+(.*)$", en[m.start():])
    return en[:m.start()].strip().rstrip(", "), (n.group(1).strip() if n else "")


def card_age(en: str) -> int | None:
    m = re.search(r"\b(?:a |looks (?:about )?)(\d{2})(?:-year-old)?\b", en)
    return int(m.group(1)) if m else None


def age_rule(age: int | None) -> str:
    if age is None:
        return "The person must clearly be an adult."
    if age >= 60:
        return (f"The person must clearly look elderly, about {age} years old: deeply lined and loose skin, age spots, "
                "white or grey hair and beard exactly as described. Do not make them look younger; any makeup or "
                "styling wording above must not take years off the face.")
    return f"The person must clearly be an adult of about {age}, matching the age stated above, not a teenager."


def _aspect(mj: str, default: str) -> str:
    m = re.search(r"--ar\s+(\d+:\d+)", mj or "")
    return m.group(1) if m else default


def plate_items(ep_dir: Path, files: list[str]) -> list[Item]:
    plan = {e["file"]: e for e in _plan(ep_dir) if e.get("plate")}
    out = []
    for f in files:
        e = plan.get(f)
        if not e:
            raise ValueError(f"{f}: no plate entry in refs_plan.json")
        refs = []
        for u in e.get("uploads", []):
            p = Path(ep_dir) / "refs" / u["file"]
            if not p.is_file():
                raise FileNotFoundError(f"{f}: needs the locked {u['file']} first (lock it with `ep lock`)")
            refs.append(p)
        out.append(Item(f, f"{e.get('title', f)}（{f}）", e["gpt"], e.get("aspect", "16:9"), refs, "plates"))
    return out


def step2_items(ep_dir: Path, ep: Episode, keys: list[str], views: list[str]) -> list[Item]:
    plan = _plan(ep_dir)
    out = []
    for k in keys:
        face = Path(ep_dir) / "refs" / f"{k}_face.png"
        if not face.is_file():
            raise FileNotFoundError(f"{k}: lock refs/{k}_face.png first")
        for v in views:
            e = next((x for x in plan if x.get("cast") == k and x.get("step") == 2 and x.get("kind") == v), None)
            if not e:
                raise ValueError(f"{k}: no step-2 {v} entry in refs_plan.json")
            text, avoid = _strip_mj(e["en"])
            text = text.replace("the same person as the omni reference", "the same person as in the first input image")
            extra = ""
            if v == "full":
                extra = (" The whole body from the top of the head to the soles of the shoes is in frame; both hands "
                         "have five natural fingers; both feet and shoes are complete.")
                if "microphone" not in text:
                    extra += " No microphone, empty hands."
            if v == "half":  # only people the plan gives a mic (rapper/host/dj/hook) hold one
                extra = (" The microphone hand has five natural fingers." if "microphone" in text else
                         " Both hands have five natural fingers. No microphone, empty hands.")
            prompt = ("The first input image is the locked costume-test front portrait of this person. Keep exactly "
                      "the same face and identity, hairstyle, hair colour, outfit and adult proportions; only the "
                      "camera view and pose change. " + text + "." + extra + " " + age_rule(card_age(e["en"])) + " "
                      + NO_LIKENESS + " A real photograph. No text, no watermark, no logo.")
            if avoid:
                prompt += f" Avoid: {avoid}."
            name = ep.cast[k].name_cn
            out.append(Item(e["file"], f"{k} {name} {VIEW_CN.get(v, v)}", prompt, _aspect(e.get("mj_params", ""), "3:4"),
                            [face], "step2"))
    return out


def step1_items(ep_dir: Path, ep: Episode, keys: list[str]) -> list[Item]:
    plan = _plan(ep_dir)
    out = []
    for k in keys:
        if k not in ep.cast:
            raise ValueError(f"no cast key {k!r}")
        e = next((x for x in plan if x.get("cast") == k and x.get("step") == 1 and x.get("kind") == "face"), None)
        if not e:
            raise ValueError(f"{k}: no step-1 face entry in refs_plan.json")
        rules = (age_rule(card_age(e["en"])) + " " + NO_LIKENESS + " Vertical 3:4 portrait. No text, no watermark, "
                 "no logo.")
        up = next((u["path"] for u in e.get("uploads", []) if str(u.get("path", "")).startswith("refs/canon/")), None)
        if up:
            canon = Path(ep_dir) / up
            if not canon.is_file():
                raise FileNotFoundError(f"{k}: canon art {up} missing: run `aigc-mv ep canon {ep_dir}`")
            prompt, refs = adapt_prompt(e["en"], e.get("mj_params", ""), rules=rules), [canon]
        else:  # original character: text to image from the card
            text, avoid = _strip_mj(e["en"])
            prompt = text + ". A real photograph. " + rules + (f" Avoid: {avoid}." if avoid else "")
            refs = []
        out.append(Item(e["file"], f"{k} {ep.cast[k].name_cn}", prompt, "3:4", refs, "step1"))
    return out


def cand_path(ep_dir: Path, stem: str, n: int) -> Path:
    return Path(ep_dir) / "refs" / "candidates" / f"{stem}_cand_{n}.png"


def candidates(ep_dir: Path, stem: str) -> list[Path]:
    d = Path(ep_dir) / "refs" / "candidates"
    got = [(int(m.group(1)), p) for p in d.glob(f"{stem}_cand_*.png")
           if (m := re.fullmatch(rf"{re.escape(stem)}_cand_(\d+)\.png", p.name))]
    return [p for _, p in sorted(got)]


class _Budget:
    """Ledger totals plus in-flight reservations, behind one lock."""

    def __init__(self, gate: SpendGate, cap_usd: float, max_images: int, est_usd: float, tag: str = TAG):
        self.gate, self.cap, self.max, self.est, self.tag = gate, cap_usd, max_images, est_usd, tag
        self.lock = threading.Lock()
        self.inflight = 0
        self.next_idx: dict[str, int] = {}

    def reserve(self, ep_dir: Path, stem: str) -> int:
        with self.lock:
            spent, images = self.gate.tag_totals(self.tag)
            self.gate.check_image(self.est, self.cap, self.max, spent + self.inflight * self.est,
                                  images + self.inflight)
            self.inflight += 1
            if stem not in self.next_idx:
                have = candidates(ep_dir, stem)
                self.next_idx[stem] = int(have[-1].stem.rsplit("_", 1)[1]) + 1 if have else 1
            idx = self.next_idx[stem]
            self.next_idx[stem] += 1
            return idx

    def release(self, record) -> None:
        with self.lock:
            record()
            self.inflight -= 1


def run_batch(ep_dir: Path, gate: SpendGate, make_provider, items: list[Item], n: int, cap_usd: float,
              max_images: int, est_usd: float = EST_USD, workers: int = 1, log=print, tag: str = TAG) -> BatchResult:
    """n candidates per item (Item.n overrides), item by item in list order (so a cap stop drops the tail of the list).

    cap_usd / max_images count ledger lines tagged `tag` (one tag per run series, e.g. one per provider key).

    make_provider() returns a fresh provider per worker (providers keep last_job / last_cost per instance)."""
    res = BatchResult()
    bud = _Budget(gate, cap_usd, max_images, est_usd, tag)
    stop = threading.Event()
    local = threading.local()
    jobs = [it for it in items for _ in range(it.n if it.n is not None else n)]

    def one(it: Item) -> None:
        if stop.is_set():
            return
        try:
            idx = bud.reserve(ep_dir, it.stem)
        except SpendRefused as e:
            if not stop.is_set():
                stop.set()
                res.stopped = str(e)
                log(f"stop: {e}")
            return
        prov = getattr(local, "p", None) or make_provider()
        local.p = prov
        model = getattr(prov, "model", prov.name)
        req = ImageRequest(name=f"{it.stem}_cand_{idx}", prompt=it.prompt, aspect_ratio=it.aspect, refs=it.refs)
        dst = Path(ep_dir) / "refs" / "candidates"
        try:
            paths = prov.generate(req, dst)
        except Exception as e:
            msg = str(e)
            job = getattr(e, "job", None)
            if job is not None:
                units, real = 0, 0.0  # HTTP error reply: nothing generated, nothing billed
            else:  # transport / decode failure: may be billed, fail closed
                job = Job(id=f"local-{it.stem}-{idx}", status="failed")
                units, real = 1, getattr(prov, "last_cost", None)
            bud.release(lambda: gate.record(prov.name, model, "image", units, est_usd, job, real_usd=real, tag=tag,
                                            note=f"{it.file} #{idx}: {msg}"))
            res.failed.append((it.file, job.status, msg))
            log(f"  {it.label} #{idx}: {job.status}: {msg}")
            return
        cost = prov.last_cost
        bud.release(lambda: gate.record(prov.name, model, "image", len(paths), est_usd, prov.last_job, real_usd=cost,
                                        tag=tag, note=f"{it.label} " + ",".join(p.name for p in paths)))
        res.made.extend((it.file, p, cost) for p in paths)
        log(f"  {it.label} -> {', '.join(p.name for p in paths)}  "
            + (f"${cost:.4f}" if cost is not None else "cost not reported (counted at estimate)"))

    if workers <= 1:
        for it in jobs:
            one(it)
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            list(ex.map(one, jobs))
    res.spent_usd, res.images = gate.tag_totals(tag)
    return res


# ---- picks ----------------------------------------------------------------------------------------------------

def picks_path(ep_dir: Path) -> Path:
    return Path(ep_dir) / "refs" / "candidates" / "picks.json"


def load_picks(ep_dir: Path) -> dict:
    p = picks_path(ep_dir)
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def lock(ep_dir: Path, file: str, cand: int, reason: str, by: str = "agent", force: bool = False) -> Path:
    """Copy refs/candidates/<stem>_cand_<cand>.png to refs/<file> and record the pick.

    Refuses to replace an existing refs/<file> that has no pick record, or one picked by the user, unless force."""
    src = cand_path(ep_dir, file.removesuffix(".png"), cand)
    if not src.is_file():
        raise FileNotFoundError(f"{src} missing")
    dst = Path(ep_dir) / "refs" / file
    picks = load_picks(ep_dir)
    old = picks.get(file)
    if dst.is_file() and not force:
        if old is None:
            raise FileExistsError(f"{dst} exists and was not locked by `ep lock` (use force)")
        if old.get("by") == "user" and by != "user":
            raise FileExistsError(f"{file}: the user picked candidate {old.get('cand')} (use force)")
    shutil.copyfile(src, dst)
    picks[file] = {"cand": cand, "by": by, "reason": reason, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    picks_path(ep_dir).parent.mkdir(parents=True, exist_ok=True)
    picks_path(ep_dir).write_text(json.dumps(picks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return dst


# ---- contact sheets -------------------------------------------------------------------------------------------

def _font(size: int):
    try:
        return ImageFont.truetype(str(FONT), size)
    except OSError:
        return ImageFont.load_default()


def _fit(p: Path, h: int) -> Image.Image:
    im = Image.open(p).convert("RGB")
    return im.resize((max(1, round(im.width * h / im.height)), h), Image.LANCZOS)


def contact_sheet(rows: list[tuple[str, list[tuple[Path, str, bool]]]], out: Path, tile_h: int = 300,
                  title: str = "") -> Path:
    """One row per item: a row label, then tiles (path, label, picked). Picks get a green frame and 【选中】."""
    gap, lab_h, head_w, bg = 12, 34, 0, (22, 22, 26)
    f_lab, f_head = _font(20), _font(24)
    tiles = [(head, [(_fit(p, tile_h), lab, pk) for p, lab, pk in cells]) for head, cells in rows]
    head_h = 34
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    width = max(max(sum(im.width for im, _, _ in cells) + gap * (len(cells) + 1),
                    int(probe.textlength(head, font=f_head)) + 2 * gap) for head, cells in tiles) + head_w
    if title:
        width = max(width, int(probe.textlength(title, font=_font(28))) + 2 * gap)
    top = 50 if title else 0
    height = top + len(tiles) * (head_h + tile_h + lab_h + gap) + gap
    sheet = Image.new("RGB", (width, height), bg)
    d = ImageDraw.Draw(sheet)
    if title:
        d.text((gap, 10), title, fill=(255, 255, 255), font=_font(28))
    y = top + gap
    for head, cells in tiles:
        d.text((gap, y), head, fill=(255, 220, 120), font=f_head)
        y += head_h
        x = gap
        for im, lab, pk in cells:
            sheet.paste(im, (x, y))
            if pk:
                d.rectangle([x - 4, y - 4, x + im.width + 3, y + tile_h + 3], outline=(40, 220, 90), width=6)
            d.text((x + 2, y + tile_h + 6), ("【选中】" if pk else "") + lab,
                   fill=(40, 230, 100) if pk else (230, 230, 230), font=f_lab)
            x += im.width + gap
        y += tile_h + lab_h + gap
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() in (".jpg", ".jpeg"):
        sheet.save(out, "JPEG", quality=85, optimize=True)
    else:
        sheet.save(out, "PNG")
    return out


def item_rows(ep_dir: Path, items: list[Item], extra_first: dict[str, tuple[Path, str]] | None = None):
    """Contact-sheet rows for items: optional first tile per item (e.g. the reference), then every candidate."""
    picks = load_picks(ep_dir)
    rows = []
    for it in items:
        cells = []
        if extra_first and it.file in extra_first:
            p, lab = extra_first[it.file]
            cells.append((p, lab, False))
        pk = (picks.get(it.file) or {}).get("cand")
        for p in candidates(ep_dir, it.stem):
            n = int(p.stem.rsplit("_", 1)[1])
            cells.append((p, f"候选 {n}", n == pk))
        rows.append((it.label, cells))
    return rows
