"""Paid step-1 face test: official art -> photoreal adult front portrait candidates, under hard caps.

Prompts and canon images come from refs/refs_plan.json (written by `aigc-mv ep refs`): the step-1 `<key>_face.png`
entry of each cast key gives the prompt and its upload (refs/canon/<card>.jpg). Candidates go to
refs/candidates/<key>_face_cand_<n>.png and are never promoted to <key>_face.png automatically.
Spend and image count are counted from ledger.jsonl lines tagged TAG, so re-runs share the same caps.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from aigc_mv.episode import Episode
from aigc_mv.providers.base import ImageRequest, Job, SpendGate, SpendRefused

TAG = "facetest-step1"
EST_USD = 0.35  # conservative per-image estimate (high quality 3:4 + one reference); real cost comes from usage.cost

FACE_RULES = (
    "The person must clearly be an adult (early-to-mid twenties). The face must be an original face: it must not "
    "resemble any real celebrity or actor, in particular any cast member of the live-action adaptation "
    "\u300a\u5f02\u4eba\u4e4b\u4e0b\u300b (Under One Person), and must not copy any face from the AI show "
    "\u300a\u706b\u5f71\u6709\u563b\u54c8\u300b. Vertical 3:4 portrait. No text, no watermark, no logo."
)


@dataclass
class FaceSpec:
    key: str
    name: str
    prompt: str
    canon: Path


@dataclass
class FaceTestResult:
    made: list[tuple[str, Path, float | None]] = field(default_factory=list)
    failed: list[tuple[str, str, str]] = field(default_factory=list)  # key, status, message
    stopped: str | None = None
    spent_usd: float = 0.0
    images: int = 0


def adapt_prompt(en: str, mj_params: str = "", rules: str = FACE_RULES) -> str:
    """refs_plan English prompt -> plain image-model prompt: no MJ params, the ref is 'the first input image'."""
    text = en.replace("<原作图链接>", "").strip()
    avoid = ""
    m = re.search(r"\s--(iw|oref|ar|style|stylize|no)\b", text)
    if m:
        params = text[m.start():]
        text = text[:m.start()].strip()
        n = re.search(r"--no\s+(.*)$", params or mj_params)
        avoid = n.group(1).strip() if n else ""
    text = text.replace("of the character in the image prompt", "of the anime character in the first input image")
    text = text.rstrip(", ")
    out = ("The first input image is official anime art of the character. Use it only for hair colour, hairstyle, "
           "eye colour, signature items and costume palette, not for its drawing style. " + text + ". " + rules)
    if avoid:
        out += f" Avoid: {avoid}."
    return out


def face_specs(ep_dir: Path, ep: Episode, keys: list[str]) -> list[FaceSpec]:
    plan_p = Path(ep_dir) / "refs" / "refs_plan.json"
    if not plan_p.is_file():
        raise FileNotFoundError(f"{plan_p} missing: run `aigc-mv ep refs {ep_dir}` first")
    plan = json.loads(plan_p.read_text(encoding="utf-8"))
    out = []
    for k in keys:
        if k not in ep.cast:
            raise ValueError(f"no cast key {k!r}")
        e = next((x for x in plan if x.get("cast") == k and x.get("step") == 1 and x.get("kind") == "face"), None)
        if not e:
            raise ValueError(f"{k}: no step-1 face entry in refs_plan.json")
        up = next((u["path"] for u in e.get("uploads", []) if u.get("path", "").startswith("refs/canon/")), None)
        if not up or not (Path(ep_dir) / up).is_file():
            raise FileNotFoundError(f"{k}: canon art {up or '(none)'} missing: run `aigc-mv ep canon {ep_dir}`")
        out.append(FaceSpec(k, ep.cast[k].name_cn, adapt_prompt(e["en"], e.get("mj_params", "")), Path(ep_dir) / up))
    return out


def _next_index(dst: Path, key: str) -> int:
    nums = [int(m.group(1)) for p in dst.glob(f"{key}_face_cand_*.png")
            if (m := re.fullmatch(rf"{re.escape(key)}_face_cand_(\d+)\.png", p.name))]
    return max(nums, default=0) + 1


def run_facetest(ep_dir: Path, gate: SpendGate, provider, specs: list[FaceSpec], n: int, cap_usd: float,
                 max_images: int, est_usd: float = EST_USD, log=print) -> FaceTestResult:
    """Interleave keys (a1 b1 a2 b2 ...), one image per request, stop at the caps (counted from the ledger)."""
    dst = Path(ep_dir) / "refs" / "candidates"
    dst.mkdir(parents=True, exist_ok=True)
    res = FaceTestResult()
    model = getattr(provider, "model", provider.name)
    for _round in range(n):
        for s in specs:
            spent, images = gate.tag_totals(TAG)
            res.spent_usd, res.images = spent, images
            try:
                gate.check_image(est_usd, cap_usd, max_images, spent, images)
            except SpendRefused as e:
                res.stopped = str(e)
                log(f"stop: {e}")
                return res
            idx = _next_index(dst, s.key)
            req = ImageRequest(name=f"{s.key}_face_cand_{idx}", prompt=s.prompt, aspect_ratio="3:4", refs=[s.canon])
            try:
                paths = provider.generate(req, dst)
            except Exception as e:  # recorded, then continue within the caps
                job = getattr(e, "job", None)
                if job is not None:
                    # the provider got an HTTP error response: nothing generated, nothing billed
                    units, real = 0, 0.0
                else:
                    # transport/decode failure (timeout, URLError, bad b64 on a 200 ...): the call may have been
                    # billed. Fail closed: count the reported cost if known, else the estimate (real_usd=None),
                    # and count the image against max_images.
                    job = Job(id=f"local-{s.key}-{idx}", status="failed")
                    units, real = 1, getattr(provider, "last_cost", None)
                gate.record(provider.name, model, "image", units, est_usd, job, real_usd=real, tag=TAG,
                            note=f"{s.key}: {e}")
                res.failed.append((s.key, job.status, str(e)))
                log(f"  {s.key} #{idx}: {job.status}: {e}"
                    + ("" if units == 0 else f" (counted as billed: ${real if real is not None else est_usd:.4f})"))
                continue
            cost = provider.last_cost
            gate.record(provider.name, model, "image", len(paths), est_usd, provider.last_job, real_usd=cost,
                        tag=TAG, note=f"{s.key} {s.name} " + ",".join(p.name for p in paths))
            for p in paths:
                res.made.append((s.key, p, cost))
            log(f"  {s.key} {s.name} -> {', '.join(p.name for p in paths)}  cost "
                + (f"${cost:.4f}" if cost is not None else "(not reported, counted at estimate)"))
            if cost is None:
                log("  ! cost not reported; counting the estimate against the cap")
    res.spent_usd, res.images = gate.tag_totals(TAG)
    return res


def _label_font(size: int):
    try:
        from aigc_mv.overlays import _font

        return _font("sans", size)
    except Exception:
        return ImageFont.load_default()


def contact_sheet(ep_dir: Path, specs: list[FaceSpec], tile_h: int = 640) -> Path:
    """refs/candidates/face_candidates_sheet.png: one row per key, canon art first, then every candidate."""
    dst = Path(ep_dir) / "refs" / "candidates"
    gap, label_h, bg = 16, 56, (24, 24, 28)
    font = _label_font(30)
    rows = []
    for s in specs:
        cands = sorted(dst.glob(f"{s.key}_face_cand_*.png"),
                       key=lambda p: int(re.search(r"_(\d+)\.png$", p.name).group(1)))
        rows.append([(s.canon, f"{s.key} {s.name} 原作图（只参考）")]
                    + [(p, f"{s.key} {s.name} 候选 {p.stem.rsplit('_', 1)[1]}") for p in cands])
    tiles = [[(_fit(p, tile_h), lab) for p, lab in row] for row in rows]
    width = max(sum(im.width for im, _ in row) + gap * (len(row) + 1) for row in tiles)
    height = len(tiles) * (tile_h + label_h + gap) + gap
    sheet = Image.new("RGB", (width, height), bg)
    d = ImageDraw.Draw(sheet)
    y = gap
    for row in tiles:
        x = gap
        for im, lab in row:
            sheet.paste(im, (x, y))
            d.text((x + 4, y + tile_h + 10), lab, fill=(240, 240, 240), font=font)
            x += im.width + gap
        y += tile_h + label_h + gap
    out = dst / "face_candidates_sheet.png"
    sheet.save(out, "PNG")
    return out


def _fit(p: Path, h: int) -> Image.Image:
    im = Image.open(p).convert("RGB")
    return im.resize((max(1, round(im.width * h / im.height)), h), Image.LANCZOS)


def write_readme(ep_dir: Path, gate: SpendGate, specs: list[FaceSpec], model: str) -> Path:
    dst = Path(ep_dir) / "refs" / "candidates"
    lines = ["# 第一步 定妆正面像 候选（本地文件，不进仓库）", "",
             f"- 模型：OpenRouter `{model}`（Image API，quality high，3:4，原作图作为参考图 1 张）",
             "- 原作图只参考发色、发型、眼睛、招牌物件和服装配色；要求成年、原创面孔，不像任何真人明星/演员"
             "（尤其真人版《异人之下》演员），不照搬《火影有嘻哈》的脸。",
             "- 联系表：`face_candidates_sheet.png`（每行先放原作图，后面是候选）", "",
             "## 每张图的实际费用（OpenRouter 返回的 usage.cost）", "", "| 文件 | 状态 | 费用 USD |", "|---|---|---|"]
    for r in gate.entries(TAG):
        lines.append(f"| {r.get('note', '')} | {r.get('status')} | "
                     f"{r.get('real_usd') if r.get('real_usd') is not None else '未返回（按估算 ' + str(r.get('est_usd')) + '）'} |")
    usd, n = gate.tag_totals(TAG)
    lines += ["", f"合计：{n} 张，${usd:.4f}", "", "## 怎么挑", "",
              "看联系表，选每个人最像“真人版本人”、成年、脸是原创的一张，复制成第一步的锁定图：", "",
              "```", "cp refs/candidates/a_face_cand_<n>.png refs/a_face.png   # 诸葛青",
              "cp refs/candidates/b_face_cand_<n>.png refs/b_face.png   # 王也", "```", "",
              "这些图由版权原作图派生，只能本地使用，永远不要提交到仓库。", "", "## 用到的提示词", ""]
    for s in specs:
        lines += [f"### {s.key} {s.name}（参考图 `{s.canon.name}`）", "", s.prompt, ""]
    out = dst / "README.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
